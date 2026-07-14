"""
redactor.py - Agente Redactor.

Genera el texto de una sección de la Memoria Anual usando LangChain + Ollama,
a partir de un contexto ya preparado (idealmente ya enriquecido con notas
interpretativas cuando el tipo de documento lo requiera, ver
src/rag/enriquecimiento_financiero.py).

El texto que devuelve SIEMPRE debe pasar por el componente Revisor
(src/validation/revisor.py) antes de aceptarse como definitivo.

Soporta español e inglés (ver docs/fase_2_validacion_modelo.md, tarea 2.6):
la calidad en inglés es notablemente inferior a la del español, y el
Revisor todavia no valida cifras con formato ingles - usar con precaucion.
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

IDIOMAS_VALIDOS = {"es", "en"}

SYSTEM_PROMPT_ES = """Eres un redactor tecnico municipal. Redactas secciones de la
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

SYSTEM_PROMPT_EN = """You are a municipal technical writer. You write sections of the Annual Activity Report in English, with a formal, institutional tone.

Rules you must always follow:
- Use EXCLUSIVELY the data provided to you in the user's message.
- Do not invent figures that do not appear in that data.
- If a piece of data is not available, do not mention it.
- Write in flowing paragraphs, integrating the figures naturally.
  Never respond with a list or bullet points.
- Describe the facts in a NEUTRAL and OBJECTIVE way. Do not make value
  judgments about whether a result is good, bad, a "challenge," or an
  "achievement."
- Do not make recommendations or suggest "corrective measures" or
  "underlying causes." That interpretation belongs to the department's
  technical team, not to this document.
- Limit yourself to describing what happened with the data provided,
  without adding conclusions that are not explicitly stated in it."""

_HUMAN_TEMPLATE = {
    "es": 'Redacta la sección "{titulo_seccion}" de la memoria, usando estos datos:\n\n{contexto}',
    "en": 'Write the "{titulo_seccion}" section of the report, using this data:\n\n{contexto}',
}

_PLANTILLAS = {
    "es": ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_ES),
        ("human", _HUMAN_TEMPLATE["es"]),
    ]),
    "en": ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_EN),
        ("human", _HUMAN_TEMPLATE["en"]),
    ]),
}


def generar_seccion(
    titulo_seccion: str,
    contexto: str,
    idioma: str = "es",
    modelo: str = "llama3.2:3b",
    temperature: float = 0.3,
) -> str:
    """Genera el texto de una sección de la memoria, en español o en inglés.

    NOTA IMPORTANTE (ver docs/fase_2_validacion_modelo.md): el system prompt
    reduce, pero no elimina, el riesgo de que el modelo editorialice o
    cometa errores aritmeticos. Por eso el resultado de esta funcion NUNCA
    debe usarse sin pasar despues por el Revisor. En ingles, ademas, la
    fluidez es notablemente peor que en espanol (ver tarea 2.6).
    """
    if idioma not in IDIOMAS_VALIDOS:
        raise ValueError(
            f"idioma debe ser uno de {IDIOMAS_VALIDOS}, se recibio '{idioma}'"
        )

    llm = ChatOllama(model=modelo, temperature=temperature)
    prompt = _PLANTILLAS[idioma].invoke({"titulo_seccion": titulo_seccion, "contexto": contexto})
    respuesta = llm.invoke(prompt)
    return respuesta.content
