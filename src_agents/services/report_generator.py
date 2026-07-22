"""report_generator.py - Generador del informe final.

Sintetiza la Memoria Anual siguiendo la estructura fija del ejemplo
real del Ayuntamiento (Introducción, Análisis por Plan, Actividad
Operativa, Conclusiones) a partir de state["analysis"] -- no del
draft libre del Redactor, que no sigue esta estructura.

Reemplaza la primera versión (que volcaba el draft sin formato) tras
comprobar que el ejemplo real exige una estructura y longitud
específicas que el draft del Redactor no está diseñado para cumplir.

PENDIENTE (anotado, no resuelto hoy):
- El documento sale en ~4 páginas en vez de 2, pese a respetar el
  presupuesto de palabras -- revisar formato (interlineado, tamaño
  de fuente, márgenes) antes de considerar esto cerrado.
- No probado todavía con los 3 documentos reales juntos, solo con uno.
- Sin plantilla oficial del Ayuntamiento (report_template.docx) --
  formato propio provisional.
"""

import os
import re
import unicodedata
from pathlib import Path

from docx import Document
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from src_agents.models.state import Analisis, ConceptoValor

EJEMPLO_ESTILO = """
Destaca la ampliación de las redes colaborativas, alcanzando las 78
personas integrantes de la Red, muy por encima de la meta prevista de
10. Esta colaboración se ha materializado en la ejecución de 3
proyectos en 2025 (surgidos de 0 en 2024), incluyendo ferias y
jornadas, con un nivel de satisfacción del 85%. La atención a personas
usuarias ha crecido exponencialmente, de 10 en 2024 a 508 en 2025.
"""

PROMPT_MEMORIA = """Eres un redactor técnico municipal. A partir de los
datos proporcionados, redacta una Memoria Anual de Actividades siguiendo
ESTRICTAMENTE este estilo (ejemplo de referencia, tono y densidad, no
copies su contenido):

"{ejemplo_estilo}"

Reglas:
- Usa EXCLUSIVAMENTE las cifras que aparecen en los datos proporcionados.
- No inventes cifras. Si un plan no tiene datos suficientes, dilo brevemente.
- Redacta SIEMPRE en párrafos fluidos, sin viñetas ni listas, en ninguna
  sección, integrando las cifras de forma natural en el texto.
- LÍMITE ESTRICTO: el conjunto de las 4 secciones no debe superar
  {presupuesto_palabras} palabras en total.

Responde EXACTAMENTE en este formato, sin nada más:
==INTRODUCCION==
(texto de la introducción)
==ANALISIS_PLANES==
(texto del análisis por plan)
==ACTIVIDAD_OPERATIVA==
(texto de la actividad operativa)
==CONCLUSIONES==
(texto de las conclusiones)

Datos disponibles:
{datos}
"""

_plantilla_memoria = ChatPromptTemplate.from_messages([("human", PROMPT_MEMORIA)])


def _deduplicar(analisis: Analisis) -> Analisis:
    """Agrupa ConceptoValor por valor único -- el mismo texto largo
    (ej. un párrafo de 'avances') suele repetirse bajo varios
    conceptos distintos en tablas reales, inflando el contexto sin
    aportar información nueva."""
    vistos = set()
    datos_dedup = []
    for d in analisis.datos:
        if d.valor not in vistos:
            vistos.add(d.valor)
            datos_dedup.append(d)
    return Analisis(datos=datos_dedup, notas=analisis.notas)


def _formatear_datos(analisis: Analisis) -> str:
    return "\n".join(f"- {d.concepto}: {d.valor}" for d in analisis.datos)


def _parsear_memoria(texto: str) -> dict:
    patron = r"==(\w+)==\s*(.*?)(?=\n==\w+==|\Z)"
    return {nombre: contenido.strip() for nombre, contenido in re.findall(patron, texto, re.DOTALL)}


def _quitar_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def validar_memoria(secciones: dict, analisis: Analisis, longitud_max: int = 15) -> list[str]:
    """Comprueba que los valores CORTOS (candidatos a cifra puntual) del
    Analista aparezcan en el texto generado. Ignora valores largos
    (nombres de indicador, párrafos narrativos) -- comparación literal
    contra ellos produce falsos positivos sistemáticos, ya detectado
    tanto en reviewer.py como en esta misma síntesis."""
    texto_normalizado = _quitar_acentos(" ".join(secciones.values()).lower())
    incidencias = []
    for dato in analisis.datos:
        if len(dato.valor) > longitud_max:
            continue
        if _quitar_acentos(dato.valor.lower()) not in texto_normalizado:
            incidencias.append(f"'{dato.concepto}' = {dato.valor} no aparece en la memoria generada")
    return incidencias


def sintetizar_memoria(analisis: Analisis, presupuesto_palabras: int = 600) -> dict:
    """Llama a Groq para redactar las 4 secciones a partir de los datos
    del Analista, deduplicados. Devuelve un dict con las 4 claves
    (INTRODUCCION, ANALISIS_PLANES, ACTIVIDAD_OPERATIVA, CONCLUSIONES)."""
    modelo = ChatGroq(
        model=os.environ.get("GROQ_MODEL_MEMORIA", "llama-3.3-70b-versatile"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0.3,
    )
    analisis_dedup = _deduplicar(analisis)
    prompt = _plantilla_memoria.invoke({
        "ejemplo_estilo": EJEMPLO_ESTILO,
        "presupuesto_palabras": presupuesto_palabras,
        "datos": _formatear_datos(analisis_dedup),
    })
    respuesta = modelo.invoke(prompt)
    return _parsear_memoria(respuesta.content)


def generar_memoria_docx(analisis: Analisis, ruta_salida: Path) -> Path:
    """Punto de entrada: sintetiza y genera el .docx final, con las
    incidencias de validación como sección de notas para revisión
    humana -- no se ocultan."""
    secciones = sintetizar_memoria(analisis)
    incidencias = validar_memoria(secciones, _deduplicar(analisis))

    doc = Document()
    doc.add_heading("Memoria Anual de Actividades 2025", level=0)
    doc.add_heading("Departamento de Innovación y Empleo — San Sebastián de los Reyes", level=2)

    titulos = {
        "INTRODUCCION": "1. Introducción",
        "ANALISIS_PLANES": "2. Análisis de los Avances por Plan Estratégico",
        "ACTIVIDAD_OPERATIVA": "3. Análisis de la Actividad Operativa",
        "CONCLUSIONES": "4. Desenlace y Conclusiones",
    }
    for clave, titulo in titulos.items():
        doc.add_heading(titulo, level=1)
        doc.add_paragraph(secciones.get(clave, ""))

    if incidencias:
        doc.add_page_break()
        doc.add_heading("Notas de validación (revisión humana)", level=1)
        p = doc.add_paragraph(
            "Datos puntuales del Analista no citados literalmente en el "
            "resumen (selección editorial esperable; revisar si algún "
            "dato clave falta):"
        )
        p.runs[0].italic = True
        for i in incidencias:
            doc.add_paragraph(i, style="List Bullet")

    doc.save(ruta_salida)
    return ruta_salida