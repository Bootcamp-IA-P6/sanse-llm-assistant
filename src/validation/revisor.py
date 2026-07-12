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


def validar_cifras_financieras(texto_generado: str, partidas: list[dict]) -> list[str]:
    """Revisa que, para cada partida, si el texto afirma cuanto quedo 'sin
    ejecutar', esa cifra coincida con la diferencia real (presupuesto -
    ejecutado).

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
        ventana = texto_generado[pos_nombre:pos_nombre + 400]
        match = re.search(r"([\d.,]+)\s*EUR\s*sin ejecutar", ventana)
        if match is None:
            continue

        cifra_texto = match.group(1)
        cifra_mencionada = float(cifra_texto.replace(".", "").replace(",", "."))

        if abs(cifra_mencionada - partida["diferencia"]) > 1:  # margen por redondeos
            incidencias.append(
                f"Partida '{partida['nombre']}': el texto dice {cifra_texto} EUR sin ejecutar, "
                f"pero el valor correcto es {partida['diferencia']:,.0f} EUR".replace(",", ".")
            )

    return incidencias
