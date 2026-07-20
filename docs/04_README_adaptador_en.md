# Adaptador de traducción al inglés — resumen para el equipo

**Rama:** `feature/agent_adaptador_en` (creada desde `dev`, tras el merge de `feature/workflow-graph`)
**Archivo:** `src_agents/agents/adaptador_en.py` (antes `writer.py`, renombrado)
**Estado:** fase 1 completa (solo traducción) y probada; fase 2 (tono para el ciudadano) pendiente, a definir con el equipo
**Issue:** #81

## Qué hace

Traduce `state["draft"]` (el informe ya redactado y validado) al inglés. Va al final de la cadena, después del Agente Revisor — solo tiene sentido traducir un informe que ya ha pasado la validación. Comprueba `state["review"].valido` antes de traducir; si el Revisor no lo aprueba, no genera traducción.

Devuelve el resultado en un campo nuevo, `draft_en`, añadido a `EstadoPipeline` en `state.py`.

Es fase 1 (solo traducción, sin cambiar el tono). Mar propuso ese orden: primero traducción, validar que funciona y encaja, y decidir después cómo abordar el tono para el ciudadano.

## Cómo se validó

Probado con un texto de ejemplo (`test_adaptador_manual.py`), no con el pipeline completo todavía (depende de que el Revisor real esté terminado). Cifras verificadas una a una: se mantienen exactas, solo cambia el formato de miles (3.956 → 3,956, convención española a inglesa).

## Decisiones de diseño y problemas encontrados

- **Salida estructurada (Pydantic) en vez de texto libre.** El modelo (`qwen/qwen3.6-27b`) es un modelo de razonamiento y a veces mezcla su proceso de pensamiento con la respuesta final sin usar las etiquetas `<think>` de forma consistente. Forzar salida estructurada evita el problema de raíz.
- **Reintento (hasta 3 veces).** La llamada a Groq con salida estructurada falla de forma intermitente (`tool_use_failed`) aunque el texto generado sea correcto. Se añadió un reintento simple, igual que hace el Analista.
- **Reglas explícitas en el prompt** para dos problemas reales encontrados en pruebas: números en formato español (ambiguos en inglés) y emojis, impropios de un informe institucional.

## Pendiente

- Fase 2: definir y construir el cambio de tono para el ciudadano.
- Conectar `adaptador_en` al grafo en `workflow.py` (lo hará Mar cuando esté listo).
- Prueba de integración completa, cuando el Revisor real esté terminado y haya cuota de Groq disponible.
- No se ha usado notebook para este desarrollo — se ha probado con scripts sueltos, documentado aquí en su lugar.