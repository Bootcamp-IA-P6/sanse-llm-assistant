"""
adaptador_en.py - Adaptador de traduccion al ingles.
...
"""

import os
import re

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

def _limpiar_pensamiento(texto: str) -> str:
    """Quita el bloque <think>...</think> que algunos modelos de razonamiento
    incluyen antes de la respuesta final."""
    return re.sub(r"<think>.*?</think>\s*", "", texto, flags=re.DOTALL).strip()

_MAX_BLOQUE_CHARS = 3000


def _partir_texto_en_bloques(texto: str, max_chars: int = _MAX_BLOQUE_CHARS) -> list[str]:
    """Agrupa los parrafos del borrador en bloques que quepan holgadamente
    bajo el limite de tokens por minuto de Groq, sin cortar ningun parrafo
    a la mitad. Mismo enfoque que ya usa redactor.py con los datos del
    Analista (ver _partir_datos_en_bloques)."""
    parrafos = texto.split("\n\n")
    bloques: list[str] = []
    bloque_actual: list[str] = []
    longitud_actual = 0

    for parrafo in parrafos:
        longitud_parrafo = len(parrafo)
        if bloque_actual and longitud_actual + longitud_parrafo > max_chars:
            bloques.append("\n\n".join(bloque_actual))
            bloque_actual = []
            longitud_actual = 0
        bloque_actual.append(parrafo)
        longitud_actual += longitud_parrafo + 2

    if bloque_actual:
        bloques.append("\n\n".join(bloque_actual))

    return bloques


def agente_adaptador_en(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: traduce state['draft'] al ingles y devuelve
    state['draft_en']. Trocea el borrador en bloques (igual que hace
    redactor.py) para no superar el limite de tokens por minuto de Groq
    en documentos largos o con varios archivos combinados. Ya NO bloquea
    la traduccion si review.valido es False -- ver docstring original."""

    import certifi, httpx
    modelo_id = os.environ.get("GROQ_MODEL_ADAPTADOR", "qwen/qwen3.6-27b")
    kwargs_modelo = dict(
        model=modelo_id,
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0.2,
        max_tokens=2000,
        http_client=httpx.Client(verify=certifi.where()),
        http_async_client=httpx.AsyncClient(verify=certifi.where()),
    )
    if "qwen" in modelo_id:
        kwargs_modelo["reasoning_effort"] = "none"

    modelo = ChatGroq(**kwargs_modelo)
    modelo_estructurado = modelo.with_structured_output(TraduccionInforme)
    bloques = _partir_texto_en_bloques(estado["draft"])

    traducciones = []
    for indice, bloque in enumerate(bloques, start=1):
        if len(bloques) > 1:
            print(f"[adaptador] bloque {indice}/{len(bloques)}...")
        prompt = _plantilla.invoke({"texto": bloque})

        ultimo_error = None
        for intento in range(3):
            try:
                resultado = modelo_estructurado.invoke(prompt)
                traducciones.append(resultado.texto_traducido)
                break
            except Exception as e:
                ultimo_error = e
        else:
            print(f"[adaptador] bloque {indice}: salida estructurada fallo 3 veces, uso metodo de respaldo: {ultimo_error}")
            respuesta = modelo.invoke(prompt)
            traducciones.append(_limpiar_pensamiento(respuesta.content))

    return {"draft_en": "\n\n".join(traducciones)}