# Grafo LangGraph (workflow) + Agente Ingesta — resumen para el equipo

**Rama:** `feature/workflow-graph` (creada desde `feature/analyst-agent`)
**Notebook:** `notebooks_agents/06_workflow_graph_prototype.ipynb`
**Estado:** grafo compila; ejecución completa interrumpida por límite diario de Groq (segunda vez, ver abajo)

## Qué se hizo

### 1. Agente Ingesta — pieza que faltaba (graduado)

`extraer_carpeta()` no tenía la firma que LangGraph espera de un nodo (recibe el `EstadoPipeline` completo, devuelve un dict con solo el campo que actualiza). Se creó **`src_agents/agents/ingestion.py`** como envoltorio fino — sin lógica de extracción propia, solo adapta la firma. `extractor_generico.py` no se ha tocado.

**Asunción pendiente de confirmar con Frontend:** `agente_ingesta` asume que `state["uploaded_files"]` es una lista con una única carpeta dentro (como se ha probado hasta ahora). Si el Frontend acaba subiendo archivos sueltos en vez de apuntar a una carpeta, esta función necesita ajuste.

Validado con una llamada real contra los 3 documentos antes de construir el grafo encima.

### 2. Grafo — construido y compila (no graduado todavía)

4 nodos, secuencial, sin bifurcaciones (coherente con el MVP acordado):

```
START → ingesta → analista → redactor → revisor (STUB) → END
```

- `ingesta`, `analista`, `redactor` son los agentes reales ya graduados.
- `revisor` es un **stub temporal** — aprueba siempre, sin llamar a ningún modelo — porque `feature/reviewer-agent` todavía no está terminado. Se sustituirá por el Revisor real antes de graduar el grafo.

**`src_agents/graph/workflow.py` NO está graduado a propósito.** El grafo compila, pero compilar no es lo mismo que funcionar — no se ha completado ni una sola ejecución de extremo a extremo, así que no hay evidencia de que Redactor y Revisor reciban bien el estado de los nodos anteriores. Se gradúa solo cuando haya una ejecución completa validada.

## Incidencia: segunda vez con el límite diario de Groq

Al ejecutar el pipeline completo (los 3 documentos reales), Ingesta terminó bien, el Analista hizo varias llamadas con reintento, y se cortó de nuevo por el límite diario de tokens (`Used 97501/100000`). Misma incidencia que en la fase del Analista — confirma que **no es un caso aislado**, es un cuello de botella real con el ritmo de desarrollo actual.

**Sigue pendiente de decidir en equipo:** claves personales para no competir por la misma cuota.

## Qué se graduó y qué no

| Elemento | Estado |
|---|---|
| `src_agents/agents/ingestion.py` | ✅ Graduado, validado con llamada real |
| `pyproject.toml` (dependencia `langgraph`) | ✅ Graduado |
| Construcción del grafo (nodos, aristas) | ⏳ Solo en el notebook — pendiente de ejecución completa antes de graduar |
| Stub del Revisor | ⏳ Temporal, se sustituye por el real en cuanto esté listo |

## Pendiente

- Reintentar la ejecución completa en cuanto se reponga la cuota de Groq.
- Terminar el Agente Revisor real.
- Sustituir el stub, antes de graduar `workflow.py`.
- Resolver la cuestión de la cuota de Groq como equipo.