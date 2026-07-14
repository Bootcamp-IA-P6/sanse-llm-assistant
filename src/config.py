"""
config.py - Carga de los ficheros de configuracion (config/*.yaml).

Externaliza lo que antes vivia hardcodeado en el codigo (el system prompt del
Agente Redactor, la plantilla de secciones de la memoria, los parametros del
LLM y del RAG), para que se pueda ajustar sin tocar src/.
"""

from pathlib import Path

import yaml

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
CONFIG_DIR = RAIZ_PROYECTO / "config"


def cargar_settings(ruta: Path = CONFIG_DIR / "settings.yaml") -> dict:
    """Carga config/settings.yaml (modelo, temperature, parametros del RAG)."""
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_prompts(ruta: Path = CONFIG_DIR / "prompts.yaml") -> dict:
    """Carga config/prompts.yaml (system_prompt y la plantilla de secciones)."""
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)
