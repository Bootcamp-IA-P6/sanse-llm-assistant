"""report_generator.py - Generador del informe final.

Genera el .docx a partir del estado completo del pipeline: borrador en
español (state["draft"]), traducción al inglés (state["draft_en"]) y
las incidencias del Revisor como notas de validación al final -- no se
ocultan, sigue habiendo supervisión humana antes de publicar.

Requiere haber ejecutado el pipeline completo (o al menos hasta el
Adaptador) para tener draft y draft_en disponibles.

PENDIENTE, aparcado por hoy por problemas de cuota de Groq con el
modelo usado en la síntesis:
- La versión con estructura de 4 secciones fijas (Introducción /
  Análisis por Plan / Actividad Operativa / Conclusiones) y límite de
  2 páginas, validada en notebooks_agents/08_report_template.ipynb,
  no está aquí todavía -- retomar cuando haya cuota estable.
- Esta versión no tiene límite de páginas ni estructura fija; el
  contenido sale tal cual lo escribió el Redactor.

NOTA sobre _limpiar_fuga_razonamiento: cuando el Adaptador (qwen) falla
al generar salida estructurada, cae a un método de respaldo que a veces
deja fugas de razonamiento en primera persona SIN las etiquetas
<think>...</think> que adaptador_en.py sí filtra (ej. "1. Analyze User
Input: ...") -- detectado en pruebas reales del 27/07. No se modifica
adaptador_en.py (archivo de otra persona del equipo); este filtro
adicional vive aquí, aplicado solo al usar draft_en para el documento.
"""

import os
import re
from pathlib import Path

from docx import Document
from src_agents.models.state import EstadoPipeline  

NOMBRE_ENTIDAD = os.environ.get("NOMBRE_ENTIDAD", "Ayuntamiento")

# Patrón de fuga de razonamiento sin <think>: un bloque que empieza con
# un paso numerado en estilo "plan de trabajo" en inglés (ej.
# "1. Analyze User Input:", "2. Process Data by Indicator:").
# Todo lo posterior a la primera coincidencia se descarta -- lo anterior
# es la traducción real, lo posterior es el modelo pensando en voz alta.
_PATRON_FUGA_RAZONAMIENTO = re.compile(
    r"\n?\d+\.\s*\*{0,2}(Analyze|Process|Draft|Task|Identify|Extract)\b",
    re.IGNORECASE,
)


def _limpiar_fuga_razonamiento(texto: str) -> str:
    """Corta el texto en el primer indicio de fuga de razonamiento sin
    <think> (ver nota del módulo). Si no encuentra ninguna, devuelve el
    texto tal cual -- no modifica nada en el caso normal."""
    match = _PATRON_FUGA_RAZONAMIENTO.search(texto)
    if match:
        return texto[:match.start()].strip()
    return texto


def generar_informe_docx(estado: dict, ruta_salida: Path) -> Path:
    """Genera un .docx a partir del estado del pipeline: borrador en
    español, traducción al inglés si existe (limpia de fugas de
    razonamiento), y las incidencias del Revisor como notas de
    validación al final."""
    doc = Document()

    doc.add_heading("Memoria Anual de Actividades", level=0)
    doc.add_heading(NOMBRE_ENTIDAD, level=2)

    doc.add_heading("Informe (Español)", level=1)
    for parrafo in estado["draft"].split("\n\n"):
        if parrafo.strip():
            doc.add_paragraph(parrafo.strip())

    draft_en = estado.get("draft_en", "")
    if draft_en:
        draft_en = _limpiar_fuga_razonamiento(draft_en)
        doc.add_page_break()
        doc.add_heading("Report (English)", level=1)
        for parrafo in draft_en.split("\n\n"):
            if parrafo.strip():
                doc.add_paragraph(parrafo.strip())

    review = estado.get("review")
    if review is not None and review.incidencias:
        doc.add_page_break()
        doc.add_heading("Notas de validación (revisión humana pendiente)", level=1)
        p = doc.add_paragraph(
            "El Agente Revisor detectó las siguientes cifras o datos del "
            "Analista que no aparecen tal cual en el texto redactado. "
            "Revisar antes de publicar:"
        )
        p.runs[0].italic = True
        for incidencia in review.incidencias:
            doc.add_paragraph(incidencia, style="List Bullet")

    doc.save(ruta_salida)
    return ruta_salida

def agente_generador_informe(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: genera el .docx final a partir del estado
    completo y devuelve la ruta en state['final_document']. No llama a
    ningún LLM -- solo lee draft/draft_en/review ya generados por los
    nodos anteriores, así que no consume cuota de Groq."""
    ruta_salida = Path(os.environ.get("OUTPUT_DIR", "data/output")) / "memoria_final.docx"
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta = generar_informe_docx(estado, ruta_salida)
    return {"final_document": str(ruta)}