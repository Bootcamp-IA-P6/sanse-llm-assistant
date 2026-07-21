"""
workflow.py - Grafo completo del pipeline (LangGraph).

Conecta los agentes reales: Ingesta -> Analista -> Redactor -> Revisor -> Adaptador
(traduccion al ingles). Grafo lineal, sin bifurcaciones, coherente con el MVP
acordado por el equipo.
"""

from langgraph.graph import StateGraph, START, END

from src_agents.agents.ingestion import agente_ingesta
from src_agents.agents.analyst import agente_analista
from src_agents.agents.redactor_v1 import agente_redactor
from src_agents.agents.reviewer import agente_revisor
from src_agents.agents.adaptador_en import agente_adaptador_en
from src_agents.models.state import EstadoPipeline

grafo = StateGraph(EstadoPipeline)

grafo.add_node("ingesta", agente_ingesta)
grafo.add_node("analista", agente_analista)
grafo.add_node("redactor", agente_redactor)
grafo.add_node("revisor", agente_revisor)
grafo.add_node("adaptador", agente_adaptador_en)

grafo.add_edge(START, "ingesta")
grafo.add_edge("ingesta", "analista")
grafo.add_edge("analista", "redactor")
grafo.add_edge("redactor", "revisor")
grafo.add_edge("revisor", "adaptador")
grafo.add_edge("adaptador", END)

pipeline = grafo.compile()