"""
state.py - Estado compartido del pipeline de agentes.

Define la forma de los datos que van pasando de un agente a otro dentro
del grafo (Ingesta -> Analista -> Redactor -> Revisor). Cada agente lee
la parte que necesita y rellena la suya, sin tocar el resto.

Flujo: uploaded_files -> documents -> analysis -> draft -> review -> final_document
"""

from typing import TypedDict
from pydantic import BaseModel, Field
from src_agents.rag.extractor_generico import BloqueContenido


class ConceptoValor(BaseModel):
    """Un dato ya interpretado por el Agente Analista: qué significa y cuánto vale."""
    concepto: str = Field(description="Nombre del concepto o indicador, ej. 'inscritos en el SEPE'")
    valor: str = Field(description="Valor asociado a ese concepto, tal como aparece en el documento")
    fuente: str = Field(description="Documento y bloque de origen de este dato")


class Analisis(BaseModel):
    """Salida del Agente Analista: los datos ya resueltos, listos para redactar."""
    datos: list[ConceptoValor] = Field(description="Conceptos y valores extraídos y verificados")
    notas: str = Field(default="", description="Observaciones, ej. datos ambiguos o incompletos")


class RevisionResultado(BaseModel):
    """Salida del Agente Revisor."""
    valido: bool = Field(description="True si todas las cifras del informe coinciden con el Analisis")
    incidencias: list[str] = Field(default_factory=list, description="Discrepancias encontradas")


class EstadoPipeline(TypedDict, total=False):
    """Estado compartido que recorre todo el grafo de agentes."""
    uploaded_files: list[str]
    documents: list[BloqueContenido]
    analysis: Analisis
    draft: str
    review: RevisionResultado
    draft_en: str
    final_document: str