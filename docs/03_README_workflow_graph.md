# Grafo LangGraph (workflow) + Agente Ingesta — resumen para el equipo

**Rama:** `feature/workflow-graph` (creada desde `feature/analyst-agent`)
**Actualizaciones posteriores:** incorporación del Agente Revisor real y del Agente Adaptador (issues #81, #90, #92), y validación completa del pipeline en producción vía Streamlit (issue #94)
**Notebook:** `notebooks_agents/06_workflow_graph_prototype.ipynb`
**Estado:** graduado — grafo completo con los cinco agentes reales, ejecutado de extremo a extremo varias veces con documentos reales (24 julio)

## Qué se hizo

### 1. Agente Ingesta — graduado y validado

`extraer_carpeta()` no tenía la firma que LangGraph espera de un nodo (recibe el `EstadoPipeline` completo, devuelve un dict con solo el campo que actualiza). Se creó `src_agents/agents/ingestion.py` como envoltorio fino, sin lógica de extracción propia — solo adapta la firma; `extractor_generico.py` no se tocó.

La asunción pendiente de confirmar con Frontend (`state["uploaded_files"]` como lista con una única carpeta) queda confirmada: así es exactamente como lo usa `streamlit_prueba.py`, que guarda los archivos subidos en una carpeta temporal y llama a `pipeline.invoke({"uploaded_files": [str(tmp_dir)]})`.

### 2. Grafo — completo y graduado

5 nodos, secuencial, sin bifurcaciones:

START → ingesta → analista → redactor → revisor → adaptador → END

Los cinco son ya agentes reales, sin stubs:
- `revisor` (Agente Revisor real, `reviewer.py`) sustituyó al stub temporal que aprobaba siempre.
- `adaptador` (`adaptador_en.py`) se añadió al final de la cadena, tras el Revisor.

`src_agents/graph/workflow.py` queda graduado: se han completado varias ejecuciones de extremo a extremo con documentos reales del Ayuntamiento (informe financiero, Excel de la agencia de empleo, y ambos combinados), probadas también desde la interfaz de Streamlit (`streamlit_prueba.py`), no solo desde notebook.

## Incidencia del límite diario de Groq — resuelta de forma provisional

El cuello de botella de cuota que se documentaba aquí (`Used 97501/100000` al ejecutar el pipeline completo) se ha paliado usando modelos de repuesto en el `.env` (`GROQ_MODEL_REDACTOR`, `GROQ_MODEL_ADAPTADOR`, `GROQ_MODEL_ANALISTA`) cuando el modelo principal agota su cuota. No es una solución de fondo: si varias personas del equipo prueban a la vez sobre el mismo modelo, se puede volver a agotar — confirmado el 24 de julio revisando el panel de Groq durante pruebas simultáneas del equipo.

## Qué se graduó y qué no

| Elemento | Estado |
|---|---|
| `src_agents/agents/ingestion.py` | ✅ Graduado, validado con llamadas reales |
| `pyproject.toml` (dependencia `langgraph`) | ✅ Graduado |
| Construcción del grafo (nodos, aristas) | ✅ Graduado — 5 nodos, ejecución completa validada |
| Agente Revisor | ✅ Graduado — sustituye al stub |
| Agente Adaptador | ✅ Graduado — integrado al final de la cadena |

## Pendiente

- Documentos más grandes o combinados pueden hacer que el Adaptador supere el límite de tokens por minuto (error 429) al traducir por bloques sin pausa entre peticiones — ver `docs/04_README_adaptador_en.md`.
- Decidir en equipo una solución de fondo para la cuota compartida de Groq (claves personales, o coordinar quién prueba y cuándo).
- Terminar de decidir si `streamlit_prueba.py` sustituye a `app.py` o se fusionan.