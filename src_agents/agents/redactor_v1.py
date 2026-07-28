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
from pydantic import BaseModel, Field

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


class ParrafoInforme(BaseModel):
    texto: str = Field(description="El parrafo del informe redactado a partir de" \
    " los datos proporcionados, en espanol formal e institucional. Solo el texto " \
    "del informe, sin explicaciones ni razonamiento adicional.")


def _limpiar_pensamiento(texto: str) -> str:
    """Quita el bloque <think>...</think> que algunos modelos de razonamiento
    incluyen antes de la respuesta final."""
    return re.sub(r"<think>.*?</think>\s*", "", texto, flags=re.DOTALL).strip()


def _formatear_contexto(datos) -> str:
    return "\n".join(f"- {d.concepto}: {d.valor} (fuente: {d.fuente})" for d in datos)


# Groq limita el modelo llama-3.3-70b-versatile a 12000 tokens/minuto en el
# tier gratuito. ~8000 caracteres (~2000 tokens) por bloque deja margen
# de sobra para el prompt de sistema y la respuesta antes de chocar con
# ese limite (error 413), sin necesidad de descartar ningun dato: si no
# caben en un bloque, se reparten en varios.
_MAX_BLOQUE_CHARS = 8000


def _partir_datos_en_bloques(datos, max_chars: int = _MAX_BLOQUE_CHARS) -> list[list]:
    """Agrupa los datos del analista en bloques que quepan holgadamente bajo
    el limite de tokens por request de Groq, sin descartar ningun dato."""
    bloques: list[list] = []
    bloque_actual: list = []
    longitud_actual = 0

    for dato in datos:
        longitud_dato = len(f"- {dato.concepto}: {dato.valor} (fuente: {dato.fuente})")
        if bloque_actual and longitud_actual + longitud_dato > max_chars:
            bloques.append(bloque_actual)
            bloque_actual = []
            longitud_actual = 0
        bloque_actual.append(dato)
        longitud_actual += longitud_dato + 1

    if bloque_actual:
        bloques.append(bloque_actual)

    return bloques


def agente_redactor(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: redacta el informe a partir de state['analysis'].

    Si los datos no caben en una sola llamada dentro del limite de tokens
    por minuto de Groq, se reparten en varios bloques y se redacta un
    parrafo por bloque (mismo prompt, mismas reglas), en vez de truncar
    datos y perder cifras del informe final.
    """
    import certifi, httpx
    modelo = ChatGroq(
        model=os.environ.get("GROQ_MODEL_REDACTOR", "qwen/qwen3.6-27b"),
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0.3,
        max_tokens=4000,
        http_client=httpx.Client(verify=certifi.where()),
        http_async_client=httpx.AsyncClient(verify=certifi.where()),
    )
    modelo_estructurado = modelo.with_structured_output(ParrafoInforme)
    analisis = estado["analysis"]
    bloques = _partir_datos_en_bloques(analisis.datos)

    parrafos = []
    for indice, bloque in enumerate(bloques, start=1):
        if len(bloques) > 1:
            print(f"[redactor] bloque {indice}/{len(bloques)}...")
        contexto = _formatear_contexto(bloque)
        prompt = _plantilla.invoke({"contexto": contexto})

        ultimo_error = None
        for intento in range(3):
            try:
                respuesta = modelo_estructurado.invoke(prompt)
                parrafos.append(respuesta.texto)
                break
            except Exception as e:
                ultimo_error = e
        else:
            print(f"[redactor] bloque {indice}: salida estructurada fallo 3 veces, uso metodo de respaldo")
            respuesta = modelo.invoke(prompt)
            parrafos.append(_limpiar_pensamiento(respuesta.content))

    return {"draft": "\n\n".join(parrafos)}