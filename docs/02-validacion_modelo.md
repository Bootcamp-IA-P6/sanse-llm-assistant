# Fase 2 — Validación del modelo

> Documento de referencia para la Fase 2 del proyecto. Ver `README.md` en la raíz para la visión general.

## Objetivo de la fase

Antes de invertir tiempo construyendo la infraestructura completa de RAG (chunking, embeddings, ChromaDB), validar la pregunta que más condiciona la viabilidad del proyecto:

> **¿Es Llama 3.2 3B capaz de redactar un texto de calidad aceptable, en español e inglés, con tono adecuado, a partir de los datos extraídos?**

Es un modelo pequeño (3B parámetros), elegido por las limitaciones de GPU del equipo. No se ha probado todavía su capacidad de redacción real. Si el resultado no es aceptable, es mejor descubrirlo ahora —y decidir si hace falta ajustar el enfoque (prompts más guiados, otro modelo, generación por partes más pequeñas)— que después de haber construido todo el pipeline de recuperación vectorial encima.

---

## Por qué esta fase va antes del RAG completo

Los tres documentos ficticios (y previsiblemente los reales) son pequeños: caben enteros dentro de la ventana de contexto del modelo. Esto permite probar la generación **sin necesidad de chunking ni búsqueda vectorial todavía** — se le pasa el texto completo de un documento al modelo junto con una instrucción, y se evalúa el resultado directamente. Es la forma más rápida de obtener una respuesta a la pregunta de viabilidad.

---

## Checklist de tareas

| # | Tarea | Estado | Responsable principal |
|---|---|---|---|
| 2.1 | Crear notebook de prueba (`01_test_generacion.ipynb`) | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 2.2 | Cargar el informe financiero con el `loader.py` ya construido | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 2.3 | Construir un prompt con LangChain para redactar la sección financiera de la memoria | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 2.4 | Ejecutar la generación contra Ollama (Llama 3.2 3B) | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 2.5 | Evaluar el resultado en equipo (coherencia, fidelidad a las cifras, tono) | ⏳ Pendiente | Todo el equipo, con criterio del Product Owner sobre el tono esperado |
| 2.6 | Repetir el test generando en inglés | ⏳ Pendiente | Data Engineer (Agentes/IA) |
| 2.7 | Documentar conclusiones y decidir si se ajusta el enfoque | ⏳ Pendiente | Todo el equipo |

---

## Qué se evalúa en el resultado

| Criterio | Pregunta a responder |
|---|---|
| **Fidelidad a los datos** | ¿Las cifras que aparecen en el texto generado coinciden exactamente con las del documento original? |
| **Coherencia** | ¿El texto tiene sentido de principio a fin, sin contradicciones ni frases inconexas? |
| **Tono** | ¿Suena a un documento institucional/técnico, o suena artificial/genérico? |
| **Alucinaciones** | ¿El modelo inventa datos que no estaban en el documento de entrada? |
| **Calidad en inglés** | ¿La versión en inglés mantiene el mismo nivel de calidad que en español, o se degrada notablemente? |

---

## Posibles resultados y cómo se actúa en cada caso

| Resultado | Acción |
|---|---|
| ✅ Calidad aceptable en ambos idiomas | Se continúa con la Fase 3 (RAG) tal como estaba planeada |
| ⚠️ Calidad aceptable en español, floja en inglés | Se valora generar primero en español y traducir con un paso adicional del Agente Adaptador, en vez de generar directamente en inglés |
| ⚠️ El modelo inventa datos (alucina) | Se ajustan los prompts para forzar citación literal de cifras, o se refuerza el rol del componente Revisor (validación por código) |
| ❌ Calidad insuficiente en general | Se evalúa cambiar de modelo (ej. Mistral 7B o Llama 3.1 8B, si la GPU lo permite) o replantear el enfoque de generación por secciones más pequeñas y guiadas |

---

## Entregables de la fase

- [ ] Notebook `notebooks/01_test_generacion.ipynb` con el experimento documentado
- [ ] Registro de las conclusiones de la evaluación (calidad, decisión tomada)
- [ ] Decisión explícita de si se avanza a Fase 3 sin cambios o con ajustes

## Próxima fase

**Fase 3 — RAG**: una vez validada la capacidad de generación del modelo, se construye el pipeline de chunking, embeddings (Ollama) e indexación en ChromaDB con LangChain, para poder trabajar con documentos más grandes y múltiples fuentes a la vez.