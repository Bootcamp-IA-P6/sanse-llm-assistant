"""
loader.py - Carga de documentos para el pipeline RAG.

Convierte los documentos de entrada (PDF, Word, Excel) en un formato comun
de texto + metadata, para que el resto del pipeline no necesite saber
de que formato vino cada dato.
"""

from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import pdfplumber
from docx import Document as DocxDocument
import pandas as pd


@dataclass
class DocumentoCargado:
    """Documento ya extraido, listo para el siguiente paso del pipeline (splitter)."""
    texto: str
    fuente: str            # nombre del archivo original
    tipo: str              # 'financiero' | 'convenio' | 'agencia_colocacion' | 'otro'
    formato: str           # 'pdf' | 'docx' | 'xlsx'
    fecha_carga: str = field(default_factory=lambda: datetime.now().isoformat())


def cargar_pdf(ruta: Path) -> str:
    """Extrae texto y tablas de un PDF, sin duplicar el contenido de las tablas
    entre el texto narrativo y la version estructurada."""
    partes = []
    with pdfplumber.open(ruta) as pdf:
        for pagina in pdf.pages:
            tablas_detectadas = pagina.find_tables()

            # Excluimos el area de cada tabla antes de sacar el texto narrativo,
            # asi cada dato aparece una sola vez y en su forma mas util (estructurada).
            pagina_sin_tablas = pagina
            for tabla in tablas_detectadas:
                pagina_sin_tablas = pagina_sin_tablas.outside_bbox(tabla.bbox)

            texto = pagina_sin_tablas.extract_text() or ""
            if texto:
                partes.append(texto)

            for tabla in tablas_detectadas:
                texto_tabla = _tabla_a_texto(tabla.extract())
                if texto_tabla:
                    partes.append(texto_tabla)

    return "\n\n".join(partes)


def _tabla_a_texto(tabla: list) -> str:
    """Convierte una tabla (lista de filas) en texto tipo 'columna: valor' por fila."""
    if not tabla or len(tabla) < 2:
        return ""
    cabecera = tabla[0]
    filas_texto = []
    for fila in tabla[1:]:
        pares = [f"{c}: {v}" for c, v in zip(cabecera, fila) if c and v]
        if pares:
            filas_texto.append(" | ".join(pares))
    return "\n".join(filas_texto)


def cargar_docx(ruta: Path) -> str:
    """Extrae texto de un Word, preservando la jerarquia de titulos como Markdown."""
    doc = DocxDocument(ruta)
    partes = []
    for parrafo in doc.paragraphs:
        if not parrafo.text.strip():
            continue
        estilo = parrafo.style.name if parrafo.style is not None else ""
        if estilo.startswith("Heading") or estilo == "Title":
            partes.append(f"\n## {parrafo.text}\n")
        else:
            partes.append(parrafo.text)
    return "\n".join(partes)


def cargar_xlsx(ruta: Path) -> str:
    """Convierte cada hoja de un Excel en texto tabular legible por el LLM."""
    hojas = pd.read_excel(ruta, sheet_name=None)
    partes = []
    for nombre_hoja, df in hojas.items():
        partes.append(f"## Hoja: {nombre_hoja}")
        partes.append(df.to_string(index=False))
    return "\n\n".join(partes)


def _inferir_tipo(nombre_archivo: str) -> str:
    """Heuristica simple por nombre de archivo. Valido para el MVP;
    mas adelante conviene que el usuario clasifique el documento al subirlo."""
    nombre = nombre_archivo.lower()
    if "financ" in nombre:
        return "financiero"
    if "convenio" in nombre:
        return "convenio"
    if "agencia" in nombre or "colocacion" in nombre:
        return "agencia_colocacion"
    return "otro"


CARGADORES = {
    ".pdf": cargar_pdf,
    ".docx": cargar_docx,
    ".xlsx": cargar_xlsx,
}


def cargar_documento(ruta: Path) -> DocumentoCargado:
    """Punto de entrada unico: detecta el formato y llama al cargador adecuado."""
    extension = ruta.suffix.lower()
    if extension not in CARGADORES:
        raise ValueError(f"Formato no soportado: {extension} ({ruta.name})")

    texto = CARGADORES[extension](ruta)

    return DocumentoCargado(
        texto=texto,
        fuente=ruta.name,
        tipo=_inferir_tipo(ruta.name),
        formato=extension.lstrip("."),
    )


def cargar_carpeta(carpeta: Path) -> list:
    """Carga todos los documentos soportados dentro de una carpeta (data/raw)."""
    documentos = []
    for ruta in sorted(carpeta.iterdir()):
        if ruta.suffix.lower() in CARGADORES:
            print(f"Cargando: {ruta.name}")
            documentos.append(cargar_documento(ruta))
    return documentos


if __name__ == "__main__":
    carpeta_datos = Path(__file__).resolve().parents[2] / "data" / "raw"
    documentos = cargar_carpeta(carpeta_datos)

    print(f"\n{len(documentos)} documentos cargados:\n")
    for doc in documentos:
        print(f"--- {doc.fuente} [{doc.tipo}] ({len(doc.texto)} caracteres) ---")
        print(doc.texto[:400])
        print("...\n")
