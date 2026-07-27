"""
workflow.py - Grafo completo del pipeline (LangGraph).

Conecta los agentes reales: Ingesta -> Analista -> Redactor -> Revisor ->
Adaptador (traduccion al ingles) -> Generador de informe (.docx final).
Grafo lineal, sin bifurcaciones, coherente con el MVP acordado por el
equipo.

El nodo "generador" no llama a ningun LLM -- solo lee draft/draft_en/
review ya generados por los nodos anteriores y escribe el .docx, asi
que no anade coste de cuota de Groq al pipeline.
"""

from langgraph.graph import StateGraph, START, END

from src_agents.agents.ingestion import agente_ingesta
from src_agents.agents.analyst import agente_analista
from src_agents.agents.redactor_v1 import agente_redactor
from src_agents.agents.reviewer import agente_revisor
from src_agents.agents.adaptador_en import agente_adaptador_en
from src_agents.services.report_generator import agente_generador_informe
from src_agents.models.state import EstadoPipeline

grafo = StateGraph(EstadoPipeline)

grafo.add_node("ingesta", agente_ingesta)
grafo.add_node("analista", agente_analista)
grafo.add_node("redactor", agente_redactor)
grafo.add_node("revisor", agente_revisor)
grafo.add_node("adaptador", agente_adaptador_en)
grafo.add_node("generador", agente_generador_informe)

grafo.add_edge(START, "ingesta")
grafo.add_edge("ingesta", "analista")
grafo.add_edge("analista", "redactor")
grafo.add_edge("redactor", "revisor")
grafo.add_edge("revisor", "adaptador")
grafo.add_edge("adaptador", "generador")
grafo.add_edge("generador", END)

pipeline = grafo.compile()