"""report_generator.py - Generador del informe final.

Convierte el estado del pipeline (draft, draft_en, review) en un
documento .docx descargable. Las incidencias del Revisor se incluyen
como sección de notas, no se ocultan -- sigue habiendo supervisión
humana antes de publicar el informe.

PENDIENTE (anotado, no resuelto hoy): el formato es provisional, sin
la plantilla acordada con el Ayuntamiento. Revisar diseño/estructura.
"""

from pathlib import Path

from docx import Document


def generar_informe_docx(estado: dict, ruta_salida: Path) -> Path:
    """Genera un .docx a partir del estado del pipeline: borrador en
    español, traducción al inglés si existe, y las incidencias del
    Revisor como notas de validación al final."""
    doc = Document()

    doc.add_heading("Memoria Anual de Actividades", level=0)
    doc.add_heading("Ayuntamiento de San Sebastián de los Reyes", level=2)

    doc.add_heading("Informe (Español)", level=1)
    for parrafo in estado["draft"].split("\n\n"):
        if parrafo.strip():
            doc.add_paragraph(parrafo.strip())

    draft_en = estado.get("draft_en", "")
    if draft_en:
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