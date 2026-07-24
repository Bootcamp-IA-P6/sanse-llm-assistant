"""analyst.py - Agente Analista.

Interpreta los BloqueContenido que produce el Agente Ingesta
(state["documents"]) y resuelve pares concepto->valor explícitos, listos
para que el Redactor los use sin tener que reinterpretar datos en bruto.

Procesa DOS tipos de bloque:
- "tabla": matriz cruda, cabecera detectada por el LLM (no siempre está
  en la primera fila), troceada en bloques de 20 filas si es grande.
- "texto": prosa narrativa con cifras incrustadas (ej. informes en
  .docx). Extrae todas las cifras relevantes, tolerante a que el
  modelo no siempre siga el formato pedido al pie de la letra.

No distingue tipos de fila ni de dato semánticamente (mes, trimestre,
total, cifra puntual): reporta lo que hay tal cual. Esa interpretación
corresponde al Redactor, no a este agente.
"""

import os
import re
import time

from groq import RateLimitError
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from src_agents.models.state import EstadoPipeline, Analisis, ConceptoValor

UMBRAL_FILAS = 20

# --------------------------------------------------------------------
# Tablas
# --------------------------------------------------------------------

PROMPT_ANALISTA = """Recibes una tabla en bruto extraída de un documento
municipal, como matriz de filas (la primera es la cabecera de columnas).

Tu tarea: para CADA fila de datos (todas menos la cabecera), devuelve
los pares columna->valor que tengan un valor real (puedes omitir o
dejar en blanco los que no lo tengan, cualquiera de las dos formas
está bien).

Antes de cada fila, escribe una línea con el identificador de esa fila
(el valor de la primera columna). Separa cada fila con una línea en
blanco. No mezcles datos entre filas distintas.

Responde en este formato, sin explicación adicional:
--- <identificador de fila> ---
concepto: valor

Tabla:
{tabla}"""

_plantilla = ChatPromptTemplate.from_messages([("human", PROMPT_ANALISTA)])


def _trocear_tabla(contenido: list, tamano_bloque: int = UMBRAL_FILAS) -> list:
    """Divide una tabla grande en bloques de tamano_bloque filas de datos,
    repitiendo la cabecera (fila 0) en cada bloque para que el modelo
    conserve el contexto de columnas. Sin esto, tablas grandes (>50 filas
    aprox.) provocan que el modelo trunque su respuesta a mitad de tabla."""
    if len(contenido) <= tamano_bloque:
        return [contenido]
    cabecera = contenido[0]
    filas_datos = contenido[1:]
    bloques = []
    for i in range(0, len(filas_datos), tamano_bloque - 1):
        trozo = filas_datos[i:i + tamano_bloque - 1]
        bloques.append([cabecera] + trozo)
    return bloques


def _parsear_respuesta(texto: str, etiqueta_tabla: str, fuente: str) -> list[ConceptoValor]:
    """Convierte la respuesta del modelo en objetos ConceptoValor. Ignora
    líneas sin valor y las que no siguen 'concepto: valor' (robusto frente
    a que el modelo no obedezca el formato al pie de la letra)."""
    conceptos = []
    identificador_actual = None
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        m_id = re.match(r"^---\s*(.+?)\s*---$", linea)
        if m_id:
            identificador_actual = m_id.group(1)
            continue
        if ":" not in linea:
            continue
        concepto, _, valor = linea.partition(":")
        concepto, valor = concepto.strip(), valor.strip()
        if not valor:
            continue
        nombre = f"{concepto} ({identificador_actual})" if identificador_actual else concepto
        conceptos.append(ConceptoValor(concepto=nombre, valor=valor, fuente=f"{fuente} - {etiqueta_tabla}"))
    return conceptos


# --------------------------------------------------------------------
# Texto narrativo
# --------------------------------------------------------------------

PROMPT_TEXTO = """Recibes un fragmento de texto de un documento municipal.
Puede contener cifras relevantes (cantidades, indicadores, totales) o
ninguna en absoluto (texto introductorio, firmas, cierres formales).

Tu tarea: extrae TODAS las cifras relevantes que encuentres, con un
nombre de concepto claro, en español natural, con mayúsculas y
espacios normales (ej. "Solicitantes bolsa de empleo", NO
"solicitantes_bolsa_empleo"). Si una frase menciona varias cifras
distintas, extráelas TODAS por separado, no solo la primera.

Si el texto no contiene ninguna cifra relevante, responde exactamente:
SIN_DATOS

Si contiene cifras, responde en este formato, una línea por cifra,
SIN explicaciones ni comentarios entre paréntesis:
concepto: valor

Texto:
{texto}"""

_plantilla_texto = ChatPromptTemplate.from_messages([("human", PROMPT_TEXTO)])


def _parsear_respuesta_texto(texto: str, etiqueta: str, fuente: str) -> list[ConceptoValor]:
    """Convierte la respuesta del modelo (texto narrativo) en ConceptoValor.
    Tolerante a explicaciones entre parentesis que el modelo a veces
    añade pese a la instruccion de no hacerlo (ej. '0 (no se proporciona
    un valor especifico...)') -- se descarta esa parte, no se confia en
    que el modelo obedezca el formato al pie de la letra."""
    if texto.strip() == "SIN_DATOS":
        return []
    conceptos = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or ":" not in linea:
            continue
        concepto, _, valor = linea.partition(":")
        concepto, valor = concepto.strip(), valor.strip()
        valor = re.sub(r"\s*\(.*?\)\s*$", "", valor).strip()
        if not valor:
            continue
        conceptos.append(ConceptoValor(concepto=concepto, valor=valor, fuente=f"{fuente} - {etiqueta}"))
    return conceptos


# --------------------------------------------------------------------
# Reintento ante límite de Groq
# --------------------------------------------------------------------

def _invocar_con_reintento(modelo, prompt, intentos: int = 3):
    """Reintenta la llamada al modelo si Groq devuelve RateLimitError,
    esperando un margen creciente (5s, 10s, 15s) entre intentos. Necesario
    porque procesar varios documentos con tablas grandes trocedadas genera
    ráfagas de llamadas que superan el límite de tokens/minuto del plan
    gratuito."""
    for intento in range(intentos):
        try:
            return modelo.invoke(prompt)
        except RateLimitError:
            if intento == intentos - 1:
                raise
            espera = 5 * (intento + 1)
            print(f"  Rate limit alcanzado, esperando {espera}s (intento {intento + 1}/{intentos})...")
            time.sleep(espera)


# --------------------------------------------------------------------
# Nodo del grafo
# --------------------------------------------------------------------

def agente_analista(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: interpreta state["documents"] (tablas y texto
    narrativo) y devuelve state["analysis"]."""
    modelo = ChatGroq(
        model=os.environ.get("GROQ_MODEL_ANALISTA", "llama-3.3-70b-versatile"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0,
    )

    bloques_tabla = [b for b in estado["documents"] if b.tipo_bloque == "tabla"]
    bloques_texto = [b for b in estado["documents"] if b.tipo_bloque == "texto"]

    todos_los_conceptos = []
    notas = []

    # --- tablas ---
    for bloque in bloques_tabla:
        sub_tablas = _trocear_tabla(bloque.contenido)
        for sub_tabla in sub_tablas:
            tabla_texto = "\n".join(str(fila) for fila in sub_tabla)
            respuesta = _invocar_con_reintento(modelo, _plantilla.invoke({"tabla": tabla_texto}))
            conceptos = _parsear_respuesta(respuesta.content, bloque.etiqueta, bloque.fuente)
            if not conceptos:
                notas.append(f"Sin datos interpretables en un bloque de '{bloque.etiqueta}' ({bloque.fuente})")
            todos_los_conceptos.extend(conceptos)

    # --- texto narrativo ---
    for bloque in bloques_texto:
        respuesta = _invocar_con_reintento(modelo, _plantilla_texto.invoke({"texto": bloque.contenido}))
        conceptos = _parsear_respuesta_texto(respuesta.content, bloque.etiqueta, bloque.fuente)
        todos_los_conceptos.extend(conceptos)
        # No se registra "sin datos" si sale SIN_DATOS -- es un resultado
        # esperado (firmas, cierres formales), no un fallo del Analista.

    return {"analysis": Analisis(datos=todos_los_conceptos, notas="; ".join(notas))}