# Fase 5 — Adaptación y validación

> Documento de referencia para la Fase 5 del proyecto. Ver `README.md` en la raíz para la visión general.

## Objetivo de la fase

Construir el **Agente Adaptador**: toma el borrador técnico en español (Fase 4), ya validado por el Revisor, y genera:

1. La **versión ejecutiva divulgativa** en español (tono adaptado a ciudadanos, inversores y responsables políticos)
2. La **versión técnica en inglés**
3. La **versión ejecutiva en inglés**

Es decir, a partir de un único borrador de entrada, esta fase produce las tres variantes restantes necesarias para completar el alcance del proyecto (versión técnica ES ya existe desde la Fase 4; versión técnica EN, ejecutiva ES y ejecutiva EN se generan aquí).

---

## Por qué tono e idioma se resuelven en el mismo agente

Cambiar el tono (técnico → divulgativo) y cambiar el idioma (español → inglés) son, en la práctica, la misma operación desde el punto de vista del modelo: reescribir un texto dado siguiendo una instrucción distinta. Separarlos en dos agentes distintos (como proponía el diseño inicial con un Agente Traductor aparte) duplicaría llamadas al modelo sin necesidad. Un único prompt bien diseñado puede indicar "reescribe este texto en inglés, con tono cercano para ciudadanos" en un solo paso.

---

## Checklist de tareas

| # | Tarea | Estado | Responsable principal |
|---|---|---|---|
| 5.1 | Diseñar el prompt de adaptación de tono (técnico → divulgativo), en español | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 5.2 | Diseñar el prompt de traducción (ES → EN), manteniendo el tono de origen | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 5.3 | Implementar el Agente Adaptador con LangChain | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 5.4 | Generar las 3 variantes restantes a partir del borrador técnico en español | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 5.5 | Pasar las cifras de las 4 versiones por el componente Revisor (Fase 4) para confirmar que no se alteraron en la adaptación | ⏳ Pendiente | Product Owner |
| 5.6 | Evaluar la versión ejecutiva con el Product Owner (¿es realmente comprensible para un público no técnico?) | ⏳ Pendiente | Product Owner |
| 5.7 | Evaluar la calidad del inglés generado (ver criterio ya definido en la Fase 2) | ⏳ Pendiente | Todo el equipo |

---

## Las 4 versiones finales

| | Español | Inglés |
|---|---|---|
| **Técnica** | Generada en Fase 4 (Agente Redactor) | Generada en esta fase (Agente Adaptador: solo traducción) |
| **Ejecutiva** | Generada en esta fase (Agente Adaptador: solo cambio de tono) | Generada en esta fase (Agente Adaptador: tono + traducción) |

---

## Por qué el Revisor vuelve a intervenir aquí

Aunque el Revisor ya validó las cifras del borrador técnico en español en la Fase 4, cada reescritura del Agente Adaptador es una nueva generación del modelo — y con ello, un nuevo riesgo de que una cifra se transcriba mal (ej. al traducir "1.890.000 €" el modelo podría alterar el formato o el valor). Por eso las 3 versiones generadas en esta fase pasan también por el componente Revisor antes de darse por válidas, no solo el borrador original.

---

## Qué significa "comprensible para un público no técnico" (criterio del Product Owner)

Para evaluar la versión ejecutiva no basta con el criterio de calidad de texto ya usado en fases anteriores (coherencia, fidelidad a los datos). Se añade una pregunta específica: **¿alguien sin conocimientos del departamento entendería este resumen sin necesitar explicaciones adicionales?** Esto es una valoración cualitativa que le corresponde al Product Owner, por su rol de interlocutor con el stakeholder y conocimiento del público objetivo (ciudadanos, inversores, responsables políticos).

---

## Entregables de la fase

- [ ] `src/agents/adaptador.py`
- [ ] Prompts de adaptación de tono y traducción documentados en `config/prompts.yaml`
- [ ] Las 4 versiones completas de la memoria (técnica/ejecutiva × español/inglés), generadas a partir de los datos ficticios
- [ ] Registro de validación del Revisor sobre las 3 versiones derivadas
- [ ] Evaluación cualitativa de la versión ejecutiva por parte del Product Owner

## Riesgo a vigilar

Si en la Fase 2 se detectó que la calidad en inglés es notablemente peor que en español (uno de los resultados posibles contemplados en esa fase), aquí es donde ese problema se materializa a mayor escala, al generar dos versiones completas en inglés. Si no se resolvió antes, conviene revisitarlo ahora en vez de aceptar una calidad inferior en las versiones en inglés del entregable final.

## Próxima fase

**Fase 6 — Interfaz y entrega**: construir la interfaz Streamlit para que el equipo técnico del Ayuntamiento pueda subir documentos y descargar las memorias generadas, dockerizar la aplicación, y preparar la presentación final.