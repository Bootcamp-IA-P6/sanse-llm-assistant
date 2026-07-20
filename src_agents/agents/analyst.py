"""analyst.py - Agente Analista.

Interpreta los BloqueContenido de tipo tabla que produce el Agente Ingesta
(state["documents"]) y resuelve pares concepto->valor explícitos, listos
para que el Redactor los use sin tener que reinterpretar tablas en bruto.

No distingue tipos de fila (mes, trimestre, total): reporta lo que hay
en cada fila tal cual. Esa interpretación semántica corresponde al
Redactor (ver src_agents/agents/redactor_v1.py), no a este agente.

Solo procesa bloques de tipo 'tabla' — los de tipo 'texto' (narrativo,
con cifras incrustadas, ej. "1.396 personas" en el .docx) NO están
cubiertos todavía. Queda como trabajo pendiente.
"""

import os
import re
import time

from groq import RateLimitError
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from src_agents.models.state import EstadoPipeline, Analisis, ConceptoValor

UMBRAL_FILAS = 20

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


def agente_analista(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: interpreta state["documents"] y devuelve
    state["analysis"]."""
    modelo = ChatGroq(
        model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0,
    )

    bloques_tabla = [b for b in estado["documents"] if b.tipo_bloque == "tabla"]

    todos_los_conceptos = []
    notas = []
    for bloque in bloques_tabla:
        sub_tablas = _trocear_tabla(bloque.contenido)
        for sub_tabla in sub_tablas:
            tabla_texto = "\n".join(str(fila) for fila in sub_tabla)
            respuesta = _invocar_con_reintento(modelo, _plantilla.invoke({"tabla": tabla_texto}))
            conceptos = _parsear_respuesta(respuesta.content, bloque.etiqueta, bloque.fuente)
            if not conceptos:
                notas.append(f"Sin datos interpretables en un bloque de '{bloque.etiqueta}' ({bloque.fuente})")
            todos_los_conceptos.extend(conceptos)

    return {"analysis": Analisis(datos=todos_los_conceptos, notas="; ".join(notas))}