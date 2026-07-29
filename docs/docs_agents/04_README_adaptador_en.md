# Adaptador de traducción al inglés — resumen para el equipo

**Rama original:** `feature/agent_adaptador_en` (issue #81)
**Actualizaciones posteriores:** `fix/adaptador-reasoning-effort` (issue #90, PR #91) y `fix/adaptador-troceo-tpm` (issue #92, PR #93)
**Archivo:** `src_agents/agents/adaptador_en.py`
**Estado:** integrado en el pipeline (`workflow.py`) y probado en producción, con documentos reales por separado y combinados (Word + Excel). Fase 2 (tono para el ciudadano) sigue pendiente, a definir con el equipo.

## Qué hace

Traduce `state["draft"]` (el informe ya redactado y validado) al inglés, al final de la cadena Ingesta → Analista → Redactor → Revisor → Adaptador. Devuelve el resultado en `draft_en`, dentro de `EstadoPipeline` (`state.py`).

Es fase 1 (solo traducción, sin cambiar el tono). Mar propuso ese orden: primero traducción, validar que funciona y encaja, y decidir después cómo abordar el tono para el ciudadano — eso sigue pendiente.

## Cómo se ha validado

Ya no se prueba solo con script suelto (`test_adaptador_manual.py`): está conectado al grafo real y se ha probado de extremo a extremo varias veces, con el informe financiero solo, con el Excel de la agencia de empleo solo, y con los dos documentos combinados — en los tres casos genera el informe en inglés correctamente.

## Decisiones de diseño y problemas encontrados

- **Salida estructurada (Pydantic) en vez de texto libre**, con reintento hasta 3 veces y, si falla, respaldo a una llamada sin estructura seguida de limpieza del `<think>` — necesario porque algunos modelos de razonamiento mezclan su proceso de pensamiento con la respuesta final.
- **`reasoning_effort="none"` solo quando el modelo es de la familia `qwen`** (issue #90). Al usar modelos de repuesto sin capacidad de razonamiento (como `llama-3.1-8b-instant`), ese parámetro no es compatible y provocaba un error 400 — se hizo condicional a que `"qwen" in modelo_id`.
- **Troceo del borrador en bloques de ~3.000 caracteres antes de traducir** (issue #92), respetando párrafos completos. Antes se enviaba el borrador entero en una sola petición, lo que superaba el límite de tokens por petición del proveedor (error 413) en documentos largos.

## Pendiente

- Fase 2: definir y construir el cambio de tono para el ciudadano.
- El troceo evita el error 413 (petición demasiado grande) pero no espera entre bloque y bloque — con documentos combinados grandes (ej. Word + Excel), el volumen de peticiones seguidas puede superar el límite de tokens por minuto del modelo y dar un error 429. Detectado hoy (24 julio) en pruebas con Word + Excel juntos. Pendiente: añadir una pequeña pausa entre bloques.
- Revisar si conviene volver al modelo de producción (`qwen/qwen3.6-27b`) en `GROQ_MODEL_ADAPTADOR` una vez se libere la cuota agotada esta semana, en vez de seguir con el modelo de repuesto.