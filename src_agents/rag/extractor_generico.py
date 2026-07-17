"""extractor_generico.py - Ingesta generica de documentos."""

import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Union

ValorCelda = Union[str, int, float, None]

@dataclass
class BloqueContenido:
    """La unidad minima de informacion extraida de un documento."""
    tipo_bloque: Literal["texto", "tabla"]
    contenido: Union[str, list[list[ValorCelda]]]
    etiqueta: str
    fuente: str
    formato_origen: str
    fecha_extraccion: str = field(default_factory=lambda: datetime.now().isoformat())

# --------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------

import pdfplumber

def extraer_pdf(ruta: Path) -> list[BloqueContenido]:
    """Extrae texto y tablas de un PDF, pagina por pagina."""
    bloques = []
    with pdfplumber.open(ruta) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages, start=1):
            tablas_detectadas = pagina.find_tables()
            pagina_sin_tablas = pagina
            for tabla in tablas_detectadas:
                pagina_sin_tablas = pagina_sin_tablas.outside_bbox(tabla.bbox)
            texto = pagina_sin_tablas.extract_text() or ""
            if texto.strip():
                bloques.append(BloqueContenido(
                    tipo_bloque="texto",
                    contenido=texto,
                    etiqueta=f"{ruta.stem} - pagina {num_pagina}",
                    fuente=ruta.name,
                    formato_origen="pdf",
                ))
            for tabla in tablas_detectadas:
                filas = tabla.extract()
                if filas:
                    bloques.append(BloqueContenido(
                        tipo_bloque="tabla",
                        contenido=filas,
                        etiqueta=f"{ruta.stem} - pagina {num_pagina}",
                        fuente=ruta.name,
                        formato_origen="pdf",
                    ))
    return bloques

# --------------------------------------------------------------------
# Word
# --------------------------------------------------------------------

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

def _iter_block_items(doc):
    """Recorre el documento en su orden real, mezclando parrafos y tablas."""
    for child in doc.element.body.iterchildren():
        if child.tag.endswith('}p'):
            yield Paragraph(child, doc)
        elif child.tag.endswith('}tbl'):
            yield Table(child, doc)

def _es_titulo(parrafo) -> bool:
    """Heuristica: un parrafo corto y en negrita actua como titulo."""
    if not parrafo.text.strip() or not parrafo.runs:
        return False
    return bool(parrafo.runs[0].bold) and len(parrafo.text) < 100

def extraer_docx(ruta: Path) -> list[BloqueContenido]:
    """Extrae parrafos y tablas de un Word, en su orden real."""
    doc = Document(ruta)
    bloques = []
    etiqueta_actual = ruta.stem
    buffer_texto = []

    def volcar_buffer():
        if buffer_texto:
            bloques.append(BloqueContenido(
                tipo_bloque="texto",
                contenido="\n".join(buffer_texto),
                etiqueta=etiqueta_actual,
                fuente=ruta.name,
                formato_origen="docx",
            ))
            buffer_texto.clear()

    for item in _iter_block_items(doc):
        if isinstance(item, Paragraph):
            if not item.text.strip():
                continue
            if _es_titulo(item):
                volcar_buffer()
                etiqueta_actual = item.text.strip().rstrip(":")
            else:
                buffer_texto.append(item.text)
        else:  # Table
            volcar_buffer()
            filas = [[celda.text for celda in fila.cells] for fila in item.rows]
            bloques.append(BloqueContenido(
                tipo_bloque="tabla",
                contenido=filas,
                etiqueta=etiqueta_actual,
                fuente=ruta.name,
                formato_origen="docx",
            ))

    volcar_buffer()
    return bloques

# --------------------------------------------------------------------
# Excel
# --------------------------------------------------------------------

from openpyxl import load_workbook

def extraer_xlsx(ruta: Path) -> list[BloqueContenido]:
    """Extrae cada hoja de un Excel como un bloque de tipo 'tabla'."""
    wb = load_workbook(ruta, read_only=True, data_only=True)
    bloques = []
    for nombre_hoja in wb.sheetnames:
        ws = wb[nombre_hoja]
        filas = [
            list(fila) for fila in ws.iter_rows(values_only=True)
            if any(celda is not None for celda in fila)
        ]
        if not filas:
            continue
        bloques.append(BloqueContenido(
            tipo_bloque="tabla",
            contenido=filas,
            etiqueta=nombre_hoja,
            fuente=ruta.name,
            formato_origen="xlsx",
        ))
    return bloques

# --------------------------------------------------------------------
# Despachador
# --------------------------------------------------------------------

EXTRACTORES = {
    ".pdf": extraer_pdf,
    ".docx": extraer_docx,
    ".xlsx": extraer_xlsx,
}

def extraer_documento(ruta: Path) -> list[BloqueContenido]:
    """Punto de entrada unico: detecta el formato y llama al extractor."""
    extension = ruta.suffix.lower()
    if extension not in EXTRACTORES:
        raise ValueError(f"Formato no soportado: {extension} ({ruta.name})")
    return EXTRACTORES[extension](ruta)

def extraer_carpeta(carpeta: Path) -> list[BloqueContenido]:
    """Extrae todos los documentos soportados de una carpeta."""
    bloques = []
    for ruta in sorted(carpeta.iterdir()):
        if ruta.suffix.lower() in EXTRACTORES:
            print(f"Procesando: {ruta.name}")
            bloques.extend(extraer_documento(ruta))
    return bloques
