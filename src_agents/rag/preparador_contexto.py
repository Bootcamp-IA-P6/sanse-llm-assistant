"""preparador_contexto.py - Formateo mínimo, sin interpretación."""

def bloque_a_texto(b) -> str:
    """
    Convierte un bloque a texto legible.
    
    Principio: CERO interpretación.
    - No detecta cabeceras
    - No separa tablas múltiples
    - No analiza contenido
    
    Solo formatea para que sea legible.
    El LLM (que es más inteligente que cualquier regla) interpreta.
    """
    if b.tipo_bloque == "texto":
        return f"## {b.etiqueta}\n\n{b.contenido}"
    
    elif b.tipo_bloque == "tabla":
        filas = []
        for fila in b.contenido:
            valores = []
            for celda in fila:
                if celda is None:
                    valores.append("")
                elif isinstance(celda, float) and celda == int(celda):
                    valores.append(str(int(celda)))
                else:
                    valores.append(str(celda))
            filas.append(" | ".join(valores))
        return f"## {b.etiqueta} (tabla)\n\n" + "\n".join(filas)
    
    return ""

bloque_a_texto_mejorado = bloque_a_texto
