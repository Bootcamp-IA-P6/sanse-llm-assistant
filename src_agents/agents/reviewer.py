"""reviewer.py - Agente Revisor.

Valida que el informe redactado por el Agente Redactor (state["draft"])
sea fiel a los datos que resolvió el Agente Analista (state["analysis"]):
comprueba que cada valor de Analisis.datos aparezca, tal cual, en el
texto del borrador. Devuelve state["review"] (ver RevisionResultado en
src_agents/models/state.py, que ya define el contrato: valido=True solo
si todas las cifras del informe coinciden con el Analisis).

No es una llamada a un LLM — es una comprobación por código, la misma
decisión de diseño que ya se tomó en la versión anterior de este
componente (src_agents/validation/revisor.py): comparar si un texto
contiene una cifra es una tarea determinista, así que usar otro modelo
para esto sería más lento, menos fiable (un segundo modelo podría
cometer el mismo tipo de error que se intenta detectar) y consumiría una
llamada extra de Groq — algo que conviene evitar dado el límite diario
de tokens que el equipo ya ha agotado dos veces durante el desarrollo
(ver docs/02_README_analyst_agent.md y docs/03_README_workflow_graph.md).

No sustituye la revisión humana del informe final antes de publicarse.
"""

import unicodedata

from src_agents.models.state import EstadoPipeline, RevisionResultado


def _quitar_acentos(texto: str) -> str:
    """Normaliza acentos para comparar de forma fiable, aunque el
    Redactor escriba con tilde y el dato de origen no la lleve (o al
    revés)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def agente_revisor(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: contrasta state['draft'] contra state['analysis']
    y devuelve state['review'].

    Para cada ConceptoValor que resolvió el Analista, busca su 'valor'
    (sin reinterpretar el número, tal como lo devolvió el Analista) dentro
    del borrador. Si no aparece, se registra como incidencia — puede
    significar que el Redactor omitió el dato o que lo reescribió con una
    cifra distinta (inventada).
    """
    draft = estado["draft"]
    analisis = estado["analysis"]

    draft_normalizado = _quitar_acentos(draft.lower())
    incidencias = []

    for dato in analisis.datos:
        valor_normalizado = _quitar_acentos(dato.valor.lower())
        if valor_normalizado not in draft_normalizado:
            incidencias.append(
                f"'{dato.concepto}' = {dato.valor} (fuente: {dato.fuente}) "
                f"no aparece en el informe redactado"
            )

    return {"review": RevisionResultado(valido=len(incidencias) == 0, incidencias=incidencias)}
