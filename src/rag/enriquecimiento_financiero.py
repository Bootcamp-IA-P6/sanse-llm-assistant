"""
enriquecimiento_financiero.py - Enriquece el texto del informe financiero con
notas interpretativas pre-calculadas (por encima / por debajo del presupuesto),
para reducir errores de razonamiento aritmetico del LLM al redactar (ver
docs/fase_2_validacion_modelo.md para el detalle del hallazgo que motiva esto).

Nota: esta logica es especifica del documento de tipo 'financiero'. Los
documentos de convenios y agencia de colocacion no tienen esta misma
estructura de presupuesto/ejecucion; necesitaran su propio enriquecimiento
si se detecta una necesidad similar al probarlos.
"""

import re

PATRON_PARTIDA = re.compile(
    r"Partida:\s*(?P<nombre>[^|]+)\|\s*Presupuesto:\s*([\d.,]+)\s*EUR\s*\|\s*"
    r"Ejecutado:\s*([\d.,]+)\s*EUR\s*\|\s*%\s*Ejecucion:\s*([\d.,]+)%"
)


def _a_float(numero_texto: str) -> float:
    """Convierte un numero en formato espanol ('850.000') a float de Python."""
    return float(numero_texto.replace(".", "").replace(",", "."))


def extraer_partidas(texto: str) -> list[dict]:
    """Extrae las partidas presupuestarias del texto de un informe financiero.

    Es la UNICA fuente de verdad de estos datos: tanto enriquecer_partidas()
    como el Revisor (src/validation/revisor.py) reutilizan esta funcion en
    vez de volver a calcular o escribir las cifras a mano.
    """
    partidas = []
    for match in PATRON_PARTIDA.finditer(texto):
        presupuesto = _a_float(match.group(2))
        ejecutado = _a_float(match.group(3))
        partidas.append({
            "nombre": match.group("nombre").strip(),
            "presupuesto": presupuesto,
            "ejecutado": ejecutado,
            "pct": _a_float(match.group(4)),
            "diferencia": abs(presupuesto - ejecutado),
        })
    return partidas


def enriquecer_partidas(texto: str, partidas: list[dict]) -> str:
    """Añade al texto notas interpretativas sobre si cada partida ejecuto por
    encima o por debajo del presupuesto. La relacion aritmetica ya viene
    resuelta por codigo; el LLM solo tiene que redactarla, no deducirla.
    """
    notas = []
    for p in partidas:
        diferencia_fmt = f"{p['diferencia']:,.0f}".replace(",", ".")
        if p["pct"] < 100:
            nota = (f"Nota interpretativa: '{p['nombre']}' ejecuto POR DEBAJO "
                     f"del presupuesto (quedaron {diferencia_fmt} EUR sin ejecutar).")
        elif p["pct"] > 100:
            nota = (f"Nota interpretativa: '{p['nombre']}' ejecuto POR ENCIMA "
                     f"del presupuesto (se excedio en {diferencia_fmt} EUR).")
        else:
            nota = f"Nota interpretativa: '{p['nombre']}' ejecuto EXACTAMENTE el presupuesto previsto."
        notas.append(nota)

    if notas:
        texto = texto + "\n\n" + "\n".join(notas)
    return texto
