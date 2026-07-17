"""
adaptador_langchain.py - Convierte los DocumentoCargado (nuestro formato,
ver loader.py) a objetos Document de LangChain, que es lo que esperan el
splitter, los embeddings y ChromaDB en los siguientes pasos de esta fase.
"""

from langchain_core.documents import Document
from src.rag.loader import DocumentoCargado


def a_document_langchain(documento: DocumentoCargado) -> Document:
    """Convierte un DocumentoCargado en un Document de LangChain,
    conservando toda la metadata en el campo metadata."""
    return Document(
        page_content=documento.texto,
        metadata={
            "fuente": documento.fuente,
            "tipo": documento.tipo,
            "formato": documento.formato,
            "fecha_carga": documento.fecha_carga,
        },
    )


def documentos_a_langchain(documentos: list[DocumentoCargado]) -> list[Document]:
    """Convierte una lista completa (ej. la que devuelve cargar_carpeta())."""
    return [a_document_langchain(doc) for doc in documentos]