"""reviewer.py - Agente Revisor.

Valida que el informe redactado por el Agente Redactor (state["draft"])
sea fiel a los datos que resolvio el Agente Analista (state["analysis"]).

Trata dos tipos de valor de forma distinta, porque no tiene sentido
exigir la misma precision a los dos:

- Valores numericos (cifras, porcentajes, codigos cortos): comparacion
  LITERAL, sin margen. Una cifra alterada es exactamente lo que este
  agente existe para detectar - aqui no se relaja nada.
- Valores narrativos largos (texto descriptivo, ej. "LINEAS DE
  ACTUACION"): el Redactor los parafrasea por diseno, asi que exigir
  coincidencia literal exacta genera falsos positivos constantes.
  Se comprueba en su lugar que un porcentaje suficiente de las palabras
  significativas del valor aparecen en el borrador.

No es una llamada a un LLM - sigue siendo una comprobacion por codigo,
determinista, sin gastar cuota de Groq.
"""
import re
import unicodedata

from src_agents.models.state import EstadoPipeline, RevisionResultado

# Umbral de cobertura de palabras para valores narrativos: si al menos
# este porcentaje de las palabras significativas del valor aparece en
# el borrador, se considera que el dato SI esta presente (aunque
# reformulado). Ajustable si en la practica da demasiados o muy pocos
# falsos positivos.
_UMBRAL_COBERTURA_NARRATIVA = 0.7

# Un valor se considera "numerico" si, quitando espacios, solo contiene
# digitos y los separadores/simbolos habituales en cifras (punto y coma
# de miles/decimales, barra de fechas o proporciones, porcentaje, signo).
# Ej.: "1.396", "97/100%", "2+1", "0,8229" -> numericos.
# Ej.: "Educacion Infantil", "4. Ejecucion y difusion..." -> narrativos
# (llevan letras, aunque empiecen por un numero).
_PATRON_NUMERICO = re.compile(r"^[\d.,/%+\-\s]+$")


def _quitar_acentos(texto: str) -> str:
    """Normaliza acentos para comparar de forma fiable, aunque el
    Redactor escriba con tilde y el dato de origen no la lleve (o al
    reves)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _es_valor_numerico(valor: str) -> bool:
    """True si el valor es una cifra o dato corto - se compara siempre
    de forma literal, sin margen."""
    return bool(_PATRON_NUMERICO.match(valor.strip()))


def _aparece_literal(valor_normalizado: str, draft_normalizado: str) -> bool:
    """Comparacion estricta: el valor debe aparecer tal cual, como
    subcadena, dentro del borrador."""
    return valor_normalizado in draft_normalizado


def _aparece_narrativo(
    valor_normalizado: str,
    draft_normalizado: str,
    umbral: float = _UMBRAL_COBERTURA_NARRATIVA,
) -> bool:
    """Comparacion tolerante para texto largo: en vez de exigir la frase
    completa tal cual, comprueba que la mayoria de sus palabras
    significativas (mas de 3 letras, para saltar articulos/preposiciones
    cortas) aparecen en el borrador. Si el valor no tiene palabras largas
    (caso raro), cae a la comparacion literal como respaldo."""
    palabras = [w for w in re.findall(r"\w+", valor_normalizado) if len(w) > 3]
    if not palabras:
        return _aparece_literal(valor_normalizado, draft_normalizado)
    encontradas = sum(1 for palabra in palabras if palabra in draft_normalizado)
    return (encontradas / len(palabras)) >= umbral


def agente_revisor(estado: EstadoPipeline) -> dict:
    """Nodo de LangGraph: contrasta state['draft'] contra state['analysis']
    y devuelve state['review'].

    Para cada ConceptoValor que resolvio el Analista, comprueba si su
    'valor' esta presente en el borrador - con comparacion literal si es
    una cifra, o por cobertura de palabras si es texto narrativo largo.
    Si no aparece, se registra como incidencia.
    """
    draft = estado["draft"]
    analisis = estado["analysis"]
    draft_normalizado = _quitar_acentos(draft.lower())

    incidencias = []
    for dato in analisis.datos:
        valor_normalizado = _quitar_acentos(dato.valor.lower())

        if _es_valor_numerico(dato.valor):
            encontrado = _aparece_literal(valor_normalizado, draft_normalizado)
        else:
            encontrado = _aparece_narrativo(valor_normalizado, draft_normalizado)

        if not encontrado:
            incidencias.append(
                f"'{dato.concepto}' = {dato.valor} (fuente: {dato.fuente}) "
                f"no aparece en el informe redactado"
            )

    return {"review": RevisionResultado(valido=len(incidencias) == 0, incidencias=incidencias)}
