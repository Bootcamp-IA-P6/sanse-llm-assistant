"""
redactor.py - Agente Redactor.

Genera el texto del informe a partir de los datos ya interpretados por el
Agente Analista (state["analysis"]), usando Groq. Mantiene las mismas
reglas de estilo y seguridad que la version anterior (sin inventar cifras,
tono formal, sin juicios de valor), adaptadas al estado compartido del
pipeline (ver src_agents/models/state.py).

El texto que devuelve SIEMPRE debe pasar por el Agente Revisor
(src_agents/agents/reviewer.py) antes de aceptarse como definitivo.
"""

import os
import re

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from src_agents.models.state import EstadoPipeline

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
- No hagas recomendaciones ni sugieras "medidas correctivas". Esa
  interpretacion corresponde al equipo tecnico del departamento, no a
  este documento."""

_plantilla = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Redacta el informe usando estos datos:\n\n{contexto}"),
])


def _limpiar_pensamiento(texto: str) -> str:
    """Quita el bloque <think>...</think> que algunos modelos de razonamiento
    incluyen antes de la respuesta final."""
    return re.sub(r"<think>.*?</think>\s*", "", texto, flags=re.DOTALL).strip()


def _formatear_contexto(datos) -> str:
    return "\n".join(f"- {d.concepto}: {d.valor} (fuente: {d.fuente})" for d in datos)


def agente_redactor(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: redacta el informe a partir de state['analysis']."""
    modelo = ChatGroq(
        model=os.environ.get("GROQ_MODEL", "qwen/qwen3.6-27b"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0.3,
    )
    analisis = estado["analysis"]
    contexto = _formatear_contexto(analisis.datos)
    prompt = _plantilla.invoke({"contexto": contexto})
    respuesta = modelo.invoke(prompt)
    return {"draft": _limpiar_pensamiento(respuesta.content)}