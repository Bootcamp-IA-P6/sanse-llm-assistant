# Analista con texto narrativo + fix de trazabilidad en el extractor — resumen para el equipo

**Rama:** `feature/analyst-narrative-text` (creada desde `dev`, ya al día tras los merges de las PR #88/#91/#93)
**Notebook:** `notebooks_agents/09_analyst_narrative_text.ipynb`
**Archivos tocados:** `src_agents/agents/analyst.py`, `src_agents/rag/extractor_generico.py`
**Estado:** ambos cambios validados con datos reales, pendiente de PR

## 1. El Analista ya cubre texto narrativo, no solo tablas

Hasta ahora `analyst.py` solo procesaba `tipo_bloque == "tabla"` — estaba anotado como pendiente desde el propio `00_exploration.ipynb`. Cifras dentro de frases (ej. *"Número de solicitantes en la bolsa de empleo: 1.396 personas"*, en `financiero_informe_1q.docx`) no se extraían en absoluto.

**Qué se añadió:**
- Un segundo prompt (`PROMPT_TEXTO`) y parser (`_parsear_respuesta_texto`), específicos para prosa — no tienen cabecera de columna que detectar, así que el modelo tiene que encontrar cifras dentro de la frase y nombrarlas con un concepto propio.
- Sentinela `SIN_DATOS` para bloques sin cifras relevantes (párrafos introductorios, firmas) — validado que el modelo lo respeta sin inventar.
- El parser descarta explicaciones entre paréntesis que el modelo a veces añade pese a la instrucción de no hacerlo (ej. `"0 (no se proporciona un valor específico...)"`) — mismo criterio de robustez que ya usa el resto del Analista: no confiar en que el modelo obedezca el formato al pie de la letra.

**Validado con:** 27 conceptos extraídos de un único bloque narrativo con varias cifras en la misma frase (sin perder ninguna), `SIN_DATOS` correcto en un bloque de firma, y 107 conceptos totales en `financiero_informe_1q.docx` completo (80 de tablas + 27 de texto — cuadra exacto, nada perdido ni duplicado).

## 2. Fix de trazabilidad en `extractor_generico.py`

Al revisar los bloques de texto de ese mismo documento, se detectó que el párrafo de cierre/firma (*"Fdo: Jefe de Servicio..."*) aparecía etiquetado como **"Ferias y mercados"** — heredaba la etiqueta de la última tabla real vista, porque `_es_titulo` (heurística "corto + negrita") no distingue un título real de un cierre institucional.

**Por qué importa:** la etiqueta forma parte de la `fuente` de cada `ConceptoValor` — es el campo de trazabilidad. Si un dato real cayera en un bloque mal etiquetado, cualquiera que quisiera verificar de dónde salió esa cifra buscaría en la sección equivocada.

**Fix:** nueva función `_es_cierre_institucional`, con un patrón corto de frases de cierre (`Fdo:`, `Enterada,`, `Lo que informo...`), comprobada antes de caer en el buffer de texto normal. Si coincide, el bloque se etiqueta como `"Cierre del documento"` en vez de heredar la sección anterior. No toca la detección de títulos reales, que ya estaba validada.

**Validado:** el mismo párrafo que antes salía como `"Ferias y mercados"` ahora sale correctamente como `"Cierre del documento"`.

## A vigilar

- El patrón de `_es_cierre_institucional` está calibrado solo con los documentos vistos hasta ahora — si llega un documento con otra fórmula de cierre, puede que no la detecte (falla de forma segura: hereda la etiqueta anterior, como antes del fix, no rompe nada).
- El Analista con texto narrativo no se ha probado todavía contra los 3 documentos juntos, solo contra `financiero_informe_1q.docx`.
- Con el Analista trayendo ahora conceptos de dos orígenes (tabla y texto), pendiente de confirmar que `report_generator.py` (deduplicación, síntesis) sigue funcionando bien con esta mezcla antes de darlo por definitivo.