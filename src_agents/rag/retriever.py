# src/rag/retriever.py (adaptado)
from src.rag.preparador_contexto import bloque_a_texto_mejorado

def indexar_documentos(persist_directory: str):
    bloques = extraer_carpeta(Path("data/raw"))
    
    textos = []
    metadatos = []
    for b in bloques:
        # USAR la versión mejorada que detecta cabeceras
        texto = bloque_a_texto_mejorado(b)
        textos.append(texto)
        metadatos.append({
            "etiqueta": b.etiqueta,
            "fuente": b.fuente,
            "formato": b.formato_origen,
            "tipo": b.tipo_bloque
        })
    # ... resto del código de indexación