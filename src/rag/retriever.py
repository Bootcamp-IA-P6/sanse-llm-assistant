"""
retriever.py - Recuperacion de contexto desde la base vectorial (ChromaDB)
para el Agente Redactor (Fase 4).

Hallazgo clave de la Fase 3 (ver docs/fase_3_rag.md): la busqueda semantica
pura no es fiable con estos datos, porque los documentos comparten
cabeceras institucionales casi identicas que pesan mas en el embedding
que el contenido especifico. La solucion es combinar busqueda semantica
con un filtro EXACTO por la metadata 'tipo' (calculada de forma
deterministica en el loader, Fase 1).

Por eso este modulo NUNCA expone una busqueda "abierta" sobre toda la
base vectorial - siempre exige indicar el tipo de documento.
"""

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

TIPOS_VALIDOS = {"financiero", "convenio", "agencia_colocacion"}


def cargar_vectorstore(
    persist_directory: str,
    collection_name: str = "memoria_ayuntamiento",
    modelo_embeddings: str = "nomic-embed-text",
) -> Chroma:
    """Abre una base vectorial ya indexada (no la crea de nuevo).
    Usar Chroma.from_documents() (Fase 3, notebook) solo para la carga
    inicial de documentos; esta funcion es para reutilizar esa base
    desde el resto del pipeline (ej. el Agente Redactor)."""
    embeddings = OllamaEmbeddings(model=modelo_embeddings)
    return Chroma(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_function=embeddings,
    )


def recuperar_contexto(
    vectorstore: Chroma,
    pregunta: str,
    tipo_documento: str,
    k: int = 2,
) -> list[Document]:
    """Recupera los k chunks mas relevantes para una pregunta, limitados
    SIEMPRE a un tipo de documento concreto (financiero, convenio,
    agencia_colocacion). No se permite busqueda sin filtro: ver el
    hallazgo documentado en docs/fase_3_rag.md sobre por que la busqueda
    semantica abierta no es fiable con estos datos.

    Devuelve la lista de Document recuperados (sin el score; usar
    similarity_search_with_score directamente si se necesita inspeccionar
    la puntuacion, como se hizo durante la validacion en el notebook).
    """
    if tipo_documento not in TIPOS_VALIDOS:
        raise ValueError(
            f"tipo_documento debe ser uno de {TIPOS_VALIDOS}, se recibio '{tipo_documento}'"
        )

    resultados = vectorstore.similarity_search(
        pregunta, k=k, filter={"tipo": tipo_documento}
    )
    return resultados


def contexto_como_texto(chunks: list[Document]) -> str:
    """Concatena una lista de chunks recuperados en un unico bloque de
    texto, listo para insertarse en el prompt del Agente Redactor."""
    return "\n\n".join(chunk.page_content for chunk in chunks)
