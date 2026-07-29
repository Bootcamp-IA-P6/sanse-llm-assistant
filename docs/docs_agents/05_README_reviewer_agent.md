# Agente Revisor — resumen para el equipo

**Rama:** `feature/reviewer-agent-v2`
**Archivo:** `src_agents/agents/reviewer.py`
**Notebook de prototipo:** `notebooks_agents/05_reviewer_agent_prototype.ipynb`
**Estado:** código escrito y validado con casos construidos a mano; pendiente de sustituir al stub en `notebooks_agents/06_workflow_graph_prototype.ipynb` / `src_agents/graph/workflow.py` cuando se gradúe el grafo completo

## Qué hace

Recibe `state["draft"]` (el texto que produce el Agente Redactor) y `state["analysis"]` (los `ConceptoValor` que ya resolvió el Agente Analista), y devuelve `state["review"]`, un `RevisionResultado` (ya definido en `state.py` antes de escribir este agente).

Para cada `ConceptoValor` del Analista, comprueba que su `valor` aparezca tal cual dentro del borrador. Si falta alguno, lo registra como incidencia y marca `valido=False`. Si todos aparecen, `valido=True` y `incidencias` queda vacía.

No distingue **por qué** falta un dato — puede que el Redactor lo haya omitido, o que lo haya reescrito con una cifra distinta (inventada). En ambos casos el síntoma es el mismo (el valor original no está en el texto), así que el Revisor los trata igual y dispara la misma alarma.

## Por qué es código y no otra llamada a un LLM

Esta decisión ya tenía precedente en el proyecto: `src_agents/validation/revisor.py`, el componente de validación de la fase RAG anterior, comparaba cifras por código en vez de con un modelo, y por el mismo motivo se ha mantenido aquí:

- Comparar si un texto contiene una cifra es una tarea determinista. Un segundo LLM podría cometer el mismo tipo de error que se le pide detectar (alucinar, confundir una cifra con otra).
- Es más rápido — sin latencia de red ni de inferencia.
- No consume una llamada adicional de Groq. El equipo ya ha agotado el límite **diario** de tokens dos veces durante el desarrollo (ver `docs/02_README_analyst_agent.md` y `docs/03_README_workflow_graph.md`) — que el Revisor no compita por esa misma cuota es una ventaja práctica, no solo teórica.

Se normalizan los acentos antes de comparar (`_quitar_acentos`, misma función que ya existía en `revisor.py`), para no marcar como incidencia una diferencia ortográfica sin importancia (el modelo escribe "Educacion" y el dato original es "Educación", por ejemplo).

## Cómo se validó (con casos construidos a mano)

No se ejecutó contra Groq para validar la lógica en sí — el objetivo era confirmar el comportamiento del propio Revisor, no el de Analista/Redactor, así que se construyeron los casos directamente con `Analisis`/`ConceptoValor` y borradores de texto fijos. El detalle completo está en `notebooks_agents/05_reviewer_agent_prototype.ipynb`.

| Caso | Qué probaba | Resultado |
|---|---|---|
| Informe fiel a los datos | ¿Aprueba cuando todo coincide? | `valido=True`, sin incidencias |
| Cifra alterada (`1.396` → `1.400`) | ¿Detecta una cifra inventada por el Redactor? | `valido=False`, 1 incidencia señalando el concepto y la fuente exactos |
| Dato omitido por completo | ¿Lo trata igual que una cifra alterada? | `valido=False`, misma incidencia que si estuviera mal escrito |
| Diferencia de acentos (`Educación` vs `Educacion`) | ¿Da un falso positivo por una tilde? | `valido=True` — la normalización evita la alarma innecesaria |

También hay una celda opcional (Paso 6) que monta el grafo completo (Ingesta → Analista → Redactor → Revisor) con el agente real, para una comprobación de extremo a extremo. No se ejecuta por defecto porque Analista y Redactor sí gastan cuota de Groq — el Revisor en sí no añade ninguna llamada al modelo.

## Decisiones de diseño

- **Comparación por substring literal**, no por valor numérico interpretado. Se compara el string `valor` del `ConceptoValor` tal como lo devolvió el Analista contra el texto del borrador — no se parsean números ni se comparan cantidades. Es la opción más simple y más fácil de razonar sobre qué detecta y qué no.
- **Normalización solo de acentos y mayúsculas**, nada más. No se toca el formato numérico (separador de miles, decimales) porque no se ha visto todavía, con datos reales, que el Redactor reformatee una cifra al citarla — si aparece ese caso, esta comparación daría un falso positivo (ver "Qué falta" más abajo).
- **Una única función determinista**, sin estado ni dependencia de red — se puede probar sin tocar Groq, como muestra el notebook.

## Qué falta / qué vigilar

- **Riesgo de falso positivo si cambia el formato numérico.** Si en algún momento el Redactor reescribe una cifra con otro formato (por ejemplo `1396` en vez de `1.396`, o redondea un decimal), el Revisor la marcaría como incidencia aunque el dato sea correcto. No se ha visto ese caso con los documentos reales todavía — queda anotado como riesgo, no como bug confirmado.
- **Sigue habiendo supervisión humana del informe final** antes de publicarse — el Revisor reduce el riesgo de que una cifra inventada pase desapercibida, no sustituye la revisión humana.
- **Pendiente de conectar al grafo real.** `agente_revisor_stub` (el stub que aprobaba siempre, sin comprobar nada) queda comentado, no borrado, en `notebooks_agents/06_workflow_graph_prototype.ipynb`, como referencia de lo que sustituye este agente. Falta la ejecución de extremo a extremo del grafo completo con el Revisor real antes de graduar `src_agents/graph/workflow.py`.
- **No cubre bloques de tipo `texto`** porque el Analista, aguas arriba, tampoco los cubre todavía (ver `docs/02_README_analyst_agent.md`) — cuando se resuelva eso, conviene revisar si el Revisor necesita algún ajuste para ese tipo de dato.
