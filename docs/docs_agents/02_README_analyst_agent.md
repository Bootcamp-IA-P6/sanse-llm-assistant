# Agente Analista — resumen para el equipo

**Rama:** `feature/analyst-agent` (creada desde `fix/docx-empty-cells`)
**Archivo:** `src_agents/agents/analyst.py`
**Notebook de prototipo:** `notebooks/04_analyst_agent_prototype.ipynb`
**Estado:** código escrito y validado por partes; pendiente de commit y de una prueba de integración completa (interrumpida por límite diario de Groq, ver más abajo)

## Qué hace

Recibe `state["documents"]` (los `BloqueContenido` que produce el Agente Ingesta) y devuelve `state["analysis"]`, con la lista de `ConceptoValor` que ya definió el estado compartido (`state.py`).

Convierte tablas en bruto (matrices de strings) en pares `concepto → valor`, resolviendo la cabecera de cada tabla con el LLM en vez de con una heurística fija en código — los documentos reales tienen la cabecera en filas distintas según la hoja, así que no hay una regla única que sirva para todas.

**Solo procesa bloques de tipo `tabla`.** Los de tipo `texto` (narrativo, con cifras incrustadas en la frase, ej. "1.396 personas" en el `.docx`) no están cubiertos todavía — pendiente.

## Cómo se validó (con los 3 documentos reales)

| Caso | Qué probaba | Resultado |
|---|---|---|
| Fila vacía | ¿Inventa datos donde no los hay? | No — reporta la ausencia fielmente |
| Columnas con nombre repetido (dos "Nº ALUMNOS") | ¿Confunde columnas homónimas? | No — atribuye el valor a la columna correcta |
| Tabla completa, 18 filas (hoja Empleo) | ¿Se pierde o desplaza algún dato al procesar de golpe? | No — 16 meses/trimestres, cifras verificadas una a una |
| Tabla grande, 57 filas (Incidencias informáticas) | ¿Aguanta el volumen? | **No, al principio** — el modelo truncaba la respuesta (24 conceptos de ~200 esperados). Resuelto trocenando en bloques de 20 filas con cabecera repetida → 224 conceptos |

## Decisiones de diseño

- **Una llamada al modelo por tabla completa**, no por fila — menos llamadas totales, más contexto para el modelo, más fácil de defender como arquitectura.
- **El Analista no distingue meses de agregados** (Q1, Q2, Q3, TOTALES son filas reales de la tabla y se tratan igual que un mes). Esa interpretación semántica queda para el Redactor, que debe tratar los agregados como resúmenes de periodo, no como meses. Sigue habiendo supervisión humana del informe final antes de publicarse.
- **Troceo de tablas en bloques de 20 filas** para evitar el truncamiento — cada bloque repite la cabecera.
- **Reintento ante error de Groq**, distinguiendo límite por minuto (reintentable con espera corta) de límite diario (no tiene sentido reintentar, se informa y se relanza el error).

## Incidencia a tener en cuenta como equipo

Al probar los 3 documentos juntos, saltó un error de límite **diario** de tokens de Groq (no por minuto): `Limit 100000, Used 98116`, con ~26 min de espera hasta el reseteo. Si cada persona del equipo prueba sus agentes con su propia clave del plan gratuito, es fácil que el equipo se quede sin cuota de forma recurrente cuanto más nos acerquemos a la entrega (29-30 de julio).

**Antes de esa fecha, decidir entre todos:** claves personales para no competir por la misma cuota

## Pendiente

- Confirmar la prueba de integración completa (los 3 documentos juntos) en cuanto haya cuota de Groq de nuevo.
- Cubrir bloques de tipo `texto` (narrativo), no solo tablas.
- Commit y push de `analyst.py` — todavía no hecho.
- Siguiente pieza del pipeline: Agente Revisor + conectar el grafo (`workflow.py`).