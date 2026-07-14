"""
revisor.py - Componente de validacion por codigo (NO es un agente de IA).

Verifica que el texto generado por el Agente Redactor sea coherente con los
datos de origen. Se centra especialmente en las relaciones aritmeticas que
el modelo tiende a calcular mal (ver docs/fase_2_validacion_modelo.md):
confundir "por debajo del presupuesto" con "por encima", o mezclar el total
de una partida con la diferencia respecto al presupuesto.

Por que es codigo y no otro agente de LLM: comparar numeros es una tarea
determinista. Usar un modelo de IA para esto seria mas lento, menos fiable
(otro modelo pequeno podria cometer el mismo tipo de error que se intenta
detectar) y consumiria una llamada adicional, algo que se decidio evitar
por la limitacion de GPU del equipo (ver README principal, seccion 2).
"""

import re
import unicodedata


def quitar_acentos(texto: str) -> str:
    """Normaliza acentos para comparar nombres de forma fiable, aunque el
    modelo los escriba con tilde y los datos de origen no las lleven."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _parse_eur(cifra_texto: str) -> float:
    """Convierte una cifra en formato espanol ('153.000') a float de Python."""
    return float(cifra_texto.replace(".", "").replace(",", "."))


def validar_cifras_financieras(texto_generado: str, partidas: list[dict]) -> list[str]:
    """Revisa que, para cada partida, si el texto afirma cuanto quedo 'sin
    ejecutar' (por debajo del presupuesto) o cuanto se 'excedio' (por encima),
    esa cifra coincida con la diferencia real (presupuesto - ejecutado).

    Devuelve una lista de incidencias encontradas (vacia si todo esta bien).
    Si hay incidencias, la sección debe marcarse para revisión humana antes
    de aceptarse como parte de la memoria final.
    """
    incidencias = []
    texto_normalizado = quitar_acentos(texto_generado)

    for partida in partidas:
        nombre_normalizado = quitar_acentos(partida["nombre"])
        pos_nombre = texto_normalizado.find(nombre_normalizado)
        if pos_nombre == -1:
            continue  # la partida no se menciona; no hay nada que validar aqui

        # Ventana acotada tras el nombre de la partida, para no confundir la
        # cifra de una partida con la de otra si se mencionan seguidas.
        ventana = quitar_acentos(texto_generado[pos_nombre:pos_nombre + 400])

        match_debajo = re.search(r"([\d.,]+)\s*EUR\s*sin ejecutar", ventana)
        match_encima = re.search(r"exced[a-z]*\s*en\s*([\d.,]+)\s*EUR", ventana)

        diferencia_fmt = f"{partida['diferencia']:,.0f}".replace(",", ".")

        if match_debajo is not None:
            cifra_texto = match_debajo.group(1)
            if abs(_parse_eur(cifra_texto) - partida["diferencia"]) > 1:  # margen por redondeos
                incidencias.append(
                    f"Partida '{partida['nombre']}': el texto dice {cifra_texto} EUR sin ejecutar, "
                    f"pero el valor correcto es {diferencia_fmt} EUR"
                )
        elif match_encima is not None:
            cifra_texto = match_encima.group(1)
            if abs(_parse_eur(cifra_texto) - partida["diferencia"]) > 1:
                incidencias.append(
                    f"Partida '{partida['nombre']}': el texto dice que se excedio en {cifra_texto} EUR, "
                    f"pero el valor correcto es {diferencia_fmt} EUR"
                )

    return incidencias


PATRON_NUMERO = re.compile(r"\d+(?:\.\d{3})*(?:,\d+)?")


def _extraer_numeros(texto: str) -> set[float]:
    """Extrae todos los numeros (formato espanol) que aparecen en un texto."""
    numeros = set()
    for match in PATRON_NUMERO.finditer(texto):
        try:
            numeros.add(_parse_eur(match.group()))
        except ValueError:
            continue
    return numeros


def _fmt_numero(numero: float) -> str:
    return f"{numero:.2f}".rstrip("0").rstrip(".")


def validar_cifras_generales(
    texto_generado: str, texto_fuente: str, tolerancia: float = 0.5
) -> list[str]:
    """Revisor generico (no especifico de un tipo de documento): extrae todas
    las cifras numericas del texto generado y comprueba que cada una aparezca
    tambien en el documento fuente correspondiente.

    Pensado para detectar el riesgo mas importante encontrado al probar el
    modelo (ver docs/04-generacion.md y el hallazgo 2.8 de
    notebooks/01-test_generacion.ipynb): el modelo calcula por su cuenta
    cifras derivadas (ej. porcentajes de crecimiento) que no venian en el
    dato original, y esos calculos suelen ser incorrectos.

    'texto_fuente' debe incluir tambien cualquier nota interpretativa
    pre-calculada que se le haya anadido al contexto (ver
    src/rag/enriquecimiento_financiero.py), para no marcar como "inventada"
    una cifra que en realidad viene de un calculo determinista nuestro.

    Devuelve una lista de incidencias encontradas (vacia si todo esta bien).
    """
    numeros_fuente = _extraer_numeros(texto_fuente)

    incidencias = []
    for numero in sorted(_extraer_numeros(texto_generado)):
        if not any(abs(numero - fuente) <= tolerancia for fuente in numeros_fuente):
            incidencias.append(
                f"La cifra {_fmt_numero(numero)} aparece en el texto generado pero no en el "
                "documento fuente (posible calculo propio del modelo, no un dato original)."
            )

    return incidencias
