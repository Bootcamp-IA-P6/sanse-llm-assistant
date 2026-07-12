"""
redactor.py - Agente Redactor.

Genera el texto de una sección de la Memoria Anual usando LangChain + Ollama,
a partir de un contexto ya preparado (idealmente ya enriquecido con notas
interpretativas cuando el tipo de documento lo requiera, ver
src/rag/enriquecimiento_financiero.py).

El texto que devuelve SIEMPRE debe pasar por el componente Revisor
(src/validation/revisor.py) antes de aceptarse como definitivo.
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """Eres un redactor tecnico municipal. Redactas secciones de la
Memoria Anual de Actividades en espanol, con tono formal e institucional.

Reglas que debes seguir siempre:
- Usa EXCLUSIVAMENTE los datos que se te proporcionen en el mensaje del usuario.
- No inventes cifras que no aparezcan en esos datos.
- Si un dato no esta disponible, no lo menciones.
- Redacta en parrafos fluidos, integrando las cifras de forma natural.
  Nunca respondas con una lista o vinetas.
- Describe los hechos de forma NEUTRA y OBJETIVA. No emitas juicios de valor
  sobre si un resultado es bueno, malo, un "desafio" o un "logro".
- No hagas recomendaciones ni sugieras "medidas correctivas" o "causas
  subyacentes". Esa interpretacion corresponde al equipo tecnico del
  departamento, no a este documento."""

_plantilla = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", 'Redacta la sección "{titulo_seccion}" de la memoria, usando estos datos:\n\n{contexto}'),
])


def generar_seccion(
    titulo_seccion: str,
    contexto: str,
    modelo: str = "llama3.2:3b",
    temperature: float = 0.3,
) -> str:
    """Genera el texto de una sección de la memoria.

    NOTA IMPORTANTE (ver docs/fase_2_validacion_modelo.md): el system prompt
    reduce, pero no elimina, el riesgo de que el modelo editorialice o
    cometa errores aritmeticos. Por eso el resultado de esta funcion NUNCA
    debe usarse sin pasar despues por el Revisor.
    """
    llm = ChatOllama(model=modelo, temperature=temperature)
    prompt = _plantilla.invoke({"titulo_seccion": titulo_seccion, "contexto": contexto})
    respuesta = llm.invoke(prompt)
    return respuesta.content
