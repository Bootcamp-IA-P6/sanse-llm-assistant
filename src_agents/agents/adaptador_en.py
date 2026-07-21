"""
adaptador_en.py - Adaptador de traduccion al ingles.
...
"""

import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src_agents.models.state import EstadoPipeline

SYSTEM_PROMPT = """You are a professional translator for a Spanish municipal
government (Ayuntamiento). Translate the following institutional report
from Spanish into English.

Rules you must always follow:
- Translate faithfully. Do not add, remove, or interpret information.
- Keep every figure exactly as it appears in the original text.
- Keep the same formal, institutional tone as the original.
- Do not add commentary, opinions, or explanations of your own.
- Return only the translated text, nothing else.
- Reformat numbers to English convention (comma for thousands, period for
  decimals) — e.g. Spanish "3.956" becomes English "3,956". The value must
  stay exactly the same; only the punctuation format changes.
- Do not include emojis, icons, or decorative symbols of any kind."""

_plantilla = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Translate this report:\n\n{texto}"),
])


class TraduccionInforme(BaseModel):
    texto_traducido: str = Field(description="El texto del informe traducido al ingles, fiel al original, sin nada mas.")


def agente_adaptador_en(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: traduce state['draft'] al ingles y devuelve
    state['draft_en']. Ya NO bloquea la traduccion si review.valido es
    False -- el Revisor puede dar falsos positivos con contenido
    narrativo largo (parrafos que el Redactor parafrasea por diseño,
    no cifras cortas). Bloquear aqui ocultaba el borrador sin que
    ninguna persona lo viera. Las incidencias siguen disponibles en
    state['review'] para revision humana junto al documento final."""

    modelo = ChatGroq(
        model=os.environ.get("GROQ_MODEL_ADAPTADOR", "qwen/qwen3.6-27b"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0.2,
    )
    modelo_estructurado = modelo.with_structured_output(TraduccionInforme)
    prompt = _plantilla.invoke({"texto": estado["draft"]})

    ultimo_error = None
    for intento in range(3):
        try:
            resultado = modelo_estructurado.invoke(prompt)
            return {"draft_en": resultado.texto_traducido}
        except Exception as e:
            ultimo_error = e
    raise ultimo_error