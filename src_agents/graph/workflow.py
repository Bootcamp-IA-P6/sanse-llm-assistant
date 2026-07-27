"""
workflow.py - Grafo del pipeline (LangGraph).

Ingesta -> Analista -> Generador -> END.

Redactor y Revisor NO se usan en esta cadena en absoluto. Su código
sigue siendo válido y sigue existiendo en el proyecto -- se quitaron
de aquí para no gastar cuota de Groq en trabajo que el resultado
final no consume (el Generador no usa draft ni review). Confirmado
con el equipo antes de simplificar.

Adaptador SÍ se usa, y hace la traducción real -- pero no aparece
como nodo aquí. Vive dentro de report_generator.py, llamado como
función (agente_adaptador_en), 4 veces, una por cada sección de la
memoria. No es un nodo del grafo porque un nodo se ejecuta una vez
por turno, y aquí hace falta repetir la llamada con un texto
distinto cada vez -- eso encaja con una función en un bucle, no con
la forma en que funciona LangGraph.
"""

from langgraph.graph import StateGraph, START, END

from src_agents.agents.ingestion import agente_ingesta
from src_agents.agents.analyst import agente_analista
from src_agents.services.report_generator import agente_generador_informe
from src_agents.models.state import EstadoPipeline

grafo = StateGraph(EstadoPipeline)

grafo.add_node("ingesta", agente_ingesta)
grafo.add_node("analista", agente_analista)
grafo.add_node("generador", agente_generador_informe)

grafo.add_edge(START, "ingesta")
grafo.add_edge("ingesta", "analista")
grafo.add_edge("analista", "generador")
grafo.add_edge("generador", END)

pipeline = grafo.compile()