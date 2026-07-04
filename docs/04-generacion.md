# Fase 4 — Generación de la memoria

> Documento de referencia para la Fase 4 del proyecto. Ver `README.md` en la raíz para la visión general.

## Objetivo de la fase

Construir el **Agente Redactor**: el componente que, apoyándose en el sistema de recuperación (Fase 3), genera el borrador completo de la Memoria Anual, sección por sección, en su versión técnica.

En esta fase se trabaja **solo en español y en la versión técnica**. La traducción a inglés y la versión ejecutiva divulgativa se abordan en la Fase 5 (Agente Adaptador), para no mezclar dos problemas distintos (redactar bien vs. adaptar tono/idioma) en el mismo paso.

---

## Checklist de tareas

| # | Tarea | Estado | Responsable principal |
|---|---|---|---|
| 4.1 | Definir la plantilla de secciones fijas de la memoria | ⏳ Pendiente | Product Owner |
| 4.2 | Diseñar el prompt del Agente Redactor por sección | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 4.3 | Implementar el Agente Redactor con LangChain (recupera contexto del RAG + genera texto) | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 4.4 | Generar cada sección de forma independiente y unirlas en un borrador completo | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 4.5 | Implementar el componente Revisor (validación de cifras por código, no LLM) | ⏳ Pendiente | Product Owner |
| 4.6 | Probar la generación completa con los 3 documentos ficticios | ⏳ Pendiente | Todo el equipo |
| 4.7 | Evaluar el borrador con el criterio de calidad definido en la Fase 2 | ⏳ Pendiente | Product Owner |

---

## Plantilla de secciones (propuesta inicial)

A definir de forma definitiva con el Product Owner, idealmente contrastada con una memoria real de años anteriores (pendiente del Ayuntamiento, ver Fase 0). Propuesta de partida basada en los documentos ficticios disponibles:

1. Resumen ejecutivo
2. Control financiero (presupuesto, ejecución, partidas destacadas)
3. Seguimiento de convenios
4. Agencia de colocación (indicadores históricos)
5. Conclusiones

Cada sección se genera de forma independiente, recuperando del RAG solo los fragmentos relevantes para esa sección (ej. la sección de "convenios" solo recupera fragmentos del documento de convenios).

---

## Cómo funciona el Agente Redactor

```
Para cada sección de la plantilla:
  1. Formular una consulta al RAG (ej. "datos sobre convenios y beneficiarios")
  2. Recuperar los fragmentos más relevantes (Fase 3)
  3. Construir el prompt: instrucción + fragmentos recuperados
  4. Enviar a Ollama (Llama 3.2 3B) y obtener el texto generado
  5. Pasar el texto generado por el componente Revisor (validación de cifras)
  6. Guardar la sección validada
Unir todas las secciones en el borrador completo de la memoria
```

### Por qué el Revisor es código, no un agente de IA

Comparar si una cifra generada coincide con la cifra original es una tarea determinista: no necesita "criterio", necesita precisión exacta. Usar un LLM para esto sería más lento, menos fiable (otro modelo pequeño podría cometer el mismo tipo de error que estamos intentando detectar) y consumiría una llamada adicional al modelo, algo que se decidió evitar por la limitación de GPU (ver decisión tomada en la Fase 0 / README principal, sección 2).

**Funcionamiento del Revisor:** extrae las cifras numéricas del texto generado y las compara contra las cifras del documento fuente correspondiente (disponibles gracias a la metadata `fuente` del `DocumentoCargado`, Fase 1). Si una cifra no coincide o no se encuentra en el original, se marca la sección para revisión humana antes de darla por válida.

---

## Entregables de la fase

- [ ] Plantilla de secciones de la memoria acordada con el Product Owner
- [ ] `src/agents/redactor.py`
- [ ] `src/validation/revisor.py`
- [ ] `config/prompts.yaml` con los prompts de cada sección
- [ ] Borrador completo de la memoria (español, versión técnica) generado a partir de los datos ficticios
- [ ] Registro de la evaluación de calidad del borrador

## Riesgo a vigilar

Si en la Fase 2 se detectaron alucinaciones o pérdida de fidelidad en las cifras, el componente Revisor cobra más importancia todavía en esta fase — conviene no avanzar a la Fase 5 sin que el Revisor esté funcionando de forma fiable, ya que un borrador con cifras incorrectas invalidaría el resto del trabajo (traducción y adaptación de tono no arreglan errores de datos).

## Próxima fase

**Fase 5 — Adaptación y validación**: el Agente Adaptador toma el borrador técnico en español y genera la versión ejecutiva divulgativa, además de las versiones en inglés de ambos documentos.