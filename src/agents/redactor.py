"""
redactor.py - Agente Redactor.

Genera el texto de una sección de la Memoria Anual usando LangChain + Ollama,
a partir de un contexto ya preparado (idealmente ya enriquecido con notas
interpretativas cuando el tipo de documento lo requiera, ver
src/rag/enriquecimiento_financiero.py).

El texto que devuelve SIEMPRE debe pasar por el componente Revisor
(src/validation/revisor.py) antes de aceptarse como definitivo.

generar_borrador_completo() es la orquestación de la Fase 4 (tarea 4.4):
recorre la plantilla de secciones de config/prompts.yaml, recupera contexto
del RAG para las secciones ligadas a un tipo de documento (financiero,
convenio, agencia_colocacion), y genera las secciones de síntesis (Resumen
Ejecutivo, Conclusiones) a partir de las demás secciones ya redactadas y
validadas, sin volver a consultar el RAG (ver docs/04-generacion.md: esas
secciones no tienen un tipo_documento propio, y una búsqueda sin filtro de
tipo no es fiable, ver docs/fase_3_rag.md).
"""

from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from src.config import RAIZ_PROYECTO, cargar_prompts, cargar_settings
from src.rag.enriquecimiento_financiero import enriquecer_partidas, extraer_partidas
from src.rag.loader import cargar_carpeta
from src.rag.retriever import contexto_como_texto, recuperar_contexto
from src.validation.revisor import validar_cifras_financieras, validar_cifras_generales


def _plantilla(system_prompt: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", 'Redacta la sección "{titulo_seccion}" de la memoria, usando estos datos:\n\n{contexto}'),
    ])


def generar_seccion(
    titulo_seccion: str,
    contexto: str,
    modelo: str = "llama3.2:3b",
    temperature: float = 0.3,
) -> str:
    """Genera el texto de una sección de la memoria.

    NOTA IMPORTANTE (ver docs/02-validacion_modelo.md): el system prompt
    reduce, pero no elimina, el riesgo de que el modelo editorialice o
    cometa errores aritmeticos. Por eso el resultado de esta funcion NUNCA
    debe usarse sin pasar despues por el Revisor.
    """
    system_prompt = cargar_prompts()["system_prompt"]
    llm = ChatOllama(model=modelo, temperature=temperature)
    prompt = _plantilla(system_prompt).invoke({"titulo_seccion": titulo_seccion, "contexto": contexto})
    respuesta = llm.invoke(prompt)
    return respuesta.content


def _textos_fuente_por_tipo(data_raw_directory: Path) -> dict[str, str]:
    """Concatena el texto de los documentos originales de data/raw, agrupado
    por tipo. Se usa como referencia del Revisor (validar_cifras_generales)
    para comprobar cifras contra el documento completo, no solo los chunks
    que haya devuelto el RAG."""
    textos: dict[str, list[str]] = {}
    for documento in cargar_carpeta(data_raw_directory):
        textos.setdefault(documento.tipo, []).append(documento.texto)
    return {tipo: "\n\n".join(partes) for tipo, partes in textos.items()}


def generar_borrador_completo(vectorstore) -> dict:
    """Genera el borrador completo de la memoria (tarea 4.4).

    Devuelve un dict:
        {"secciones": {titulo: {"texto": str, "incidencias": list[str]}},
         "borrador": str}
    Si alguna sección tiene incidencias, debe marcarse para revisión humana
    antes de aceptar el borrador como definitivo.
    """
    settings = cargar_settings()
    prompts = cargar_prompts()

    modelo = settings["llm"]["modelo"]
    temperature = settings["llm"]["temperature"]
    k = settings["rag"]["k"]
    data_raw_directory = RAIZ_PROYECTO / settings["rag"]["data_raw_directory"]

    textos_fuente = _textos_fuente_por_tipo(data_raw_directory)
    secciones = prompts["secciones"]
    resultado_por_titulo: dict[str, dict] = {}

    # 1. Secciones ligadas a un tipo de documento: contexto del RAG.
    for seccion in secciones:
        tipo = seccion["tipo_documento"]
        if tipo is None:
            continue

        chunks = recuperar_contexto(vectorstore, seccion["pregunta"], tipo, k=k)
        contexto = contexto_como_texto(chunks)

        partidas = None
        if tipo == "financiero":
            partidas = extraer_partidas(contexto)
            contexto = enriquecer_partidas(contexto, partidas)

        texto_generado = generar_seccion(seccion["titulo"], contexto, modelo=modelo, temperature=temperature)

        texto_fuente = textos_fuente.get(tipo, "") + "\n\n" + contexto
        incidencias = validar_cifras_generales(texto_generado, texto_fuente)
        if partidas is not None:
            incidencias += validar_cifras_financieras(texto_generado, partidas)

        resultado_por_titulo[seccion["titulo"]] = {"texto": texto_generado, "incidencias": incidencias}

    # 2. Secciones de síntesis: se generan a partir de las secciones ya
    # redactadas y validadas, sin volver a consultar el RAG.
    contexto_sintesis = "\n\n".join(
        resultado_por_titulo[s["titulo"]]["texto"] for s in secciones if s["tipo_documento"] is not None
    )
    texto_fuente_sintesis = "\n\n".join(textos_fuente.values()) + "\n\n" + contexto_sintesis

    for seccion in secciones:
        if seccion["tipo_documento"] is not None:
            continue

        texto_generado = generar_seccion(
            seccion["titulo"], contexto_sintesis, modelo=modelo, temperature=temperature
        )
        incidencias = validar_cifras_generales(texto_generado, texto_fuente_sintesis)
        resultado_por_titulo[seccion["titulo"]] = {"texto": texto_generado, "incidencias": incidencias}

    # 3. Unir todo en el orden de la plantilla (config/prompts.yaml).
    borrador = "\n\n".join(
        f"## {seccion['titulo']}\n\n{resultado_por_titulo[seccion['titulo']]['texto']}"
        for seccion in secciones
    )

    return {"secciones": resultado_por_titulo, "borrador": borrador}
