# Celda — src_agents/agents/ingestion.py (contenido completo, archivo ya existe vacío en el scaffold)
"""ingestion.py - Agente Ingesta.

Envuelve extractor_generico.extraer_carpeta con la firma de nodo que
espera LangGraph: recibe el EstadoPipeline completo, devuelve un dict
con solo el campo que actualiza (documents). No contiene lógica de
extracción propia — toda la extracción real vive en
src_agents/rag/extractor_generico.py, sin tocar.
"""

from pathlib import Path

from src_agents.models.state import EstadoPipeline
from src_agents.rag.extractor_generico import extraer_carpeta


def agente_ingesta(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: lee state['uploaded_files'] (rutas de archivos
    o de una carpeta) y devuelve state['documents']."""
    rutas = estado["uploaded_files"]
    # uploaded_files puede ser una carpeta única o una lista de archivos;
    # por ahora asumimos carpeta única, que es como habéis probado hasta ahora
    carpeta = Path(rutas[0]) if isinstance(rutas, list) else Path(rutas)
    documentos = extraer_carpeta(carpeta)
    return {"documents": documentos}