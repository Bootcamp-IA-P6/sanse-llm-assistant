# Fase 3 — RAG

> Documento de referencia para la Fase 3 del proyecto. Ver `README.md` en la raíz para la visión general.

## Objetivo de la fase

Construir el sistema de recuperación de información (RAG) que permitirá al agente Redactor (Fase 4) acceder a los fragmentos relevantes de cada documento a la hora de generar cada sección de la memoria, en lugar de depender de pasar documentos completos en cada prompt.

Esta fase solo tiene sentido una vez confirmado en la Fase 2 que el modelo genera texto de calidad aceptable — de lo contrario, se estaría construyendo infraestructura sobre una base no validada.

---

## Por qué hace falta RAG (y no basta con lo de la Fase 2)

En la Fase 2 probamos pasarle un documento completo al modelo porque los documentos ficticios son pequeños. Pero un caso real de uso implicará:
- Varios informes a la vez (financiero + convenios + agencia de colocación, y potencialmente varios cuatrimestres)
- Documentos más largos que los de prueba
- La necesidad de recuperar **solo la parte relevante** para cada sección de la memoria (ej. al redactar la sección de "convenios", no hace falta mandarle al modelo el informe financiero completo)

El RAG resuelve esto: divide los documentos en fragmentos pequeños (chunks), los convierte en vectores numéricos (embeddings) que capturan su significado, y permite recuperar solo los fragmentos más relevantes para una consulta concreta.

---

## Checklist de tareas

| # | Tarea | Estado | Responsable principal |
|---|---|---|---|
| 3.1 | Convertir `DocumentoCargado` (Fase 1) a objetos `Document` de LangChain | ⏳ Pendiente | Data Engineer (RAG) |
| 3.2 | Dividir documentos en chunks con un `TextSplitter` de LangChain | ⏳ Pendiente | Data Engineer (RAG) |
| 3.3 | Generar embeddings de cada chunk con Ollama (`nomic-embed-text`) | ⏳ Pendiente | Data Engineer (RAG) |
| 3.4 | Crear e indexar la base de datos vectorial en ChromaDB | ⏳ Pendiente | Data Engineer (RAG) |
| 3.5 | Configurar el LLM (Ollama + Llama 3.2 3B) como componente de LangChain | ⏳ Pendiente | Data Engineer (RAG) |
| 3.6 | Probar consultas de recuperación con preguntas de ejemplo | ⏳ Pendiente | Data Engineer (RAG) |
| 3.7 | Ajustar tamaño de chunk y número de resultados recuperados (top-k) | ⏳ Pendiente | Data Engineer (RAG) |
| 3.8 | Evaluación manual ligera: ¿recupera los fragmentos correctos para preguntas conocidas? | ⏳ Pendiente | Product Owner + Data Engineer (RAG) |

---

## Decisiones técnicas a tomar en esta fase

| Decisión | Opciones | Criterio de elección |
|---|---|---|
| **Tamaño de chunk** | Pequeño (~200-300 palabras) vs. grande (~500-1000 palabras) | Chunks pequeños dan recuperación más precisa pero pueden perder contexto; se ajustará probando con los documentos ficticios y observando la calidad de las respuestas |
| **Solapamiento entre chunks (overlap)** | Con o sin solapamiento | Un pequeño solapamiento evita cortar una idea justo en el límite de dos chunks |
| **Número de resultados recuperados (top-k)** | Pocos (2-3) vs. varios (5+) | Con un modelo pequeño y contexto limitado, conviene empezar con pocos y ampliar solo si falta información |
| **Persistencia de ChromaDB** | En memoria (se pierde al reiniciar) vs. persistida en disco | Persistida, para no tener que re-generar embeddings cada vez que se reinicia el sistema durante el desarrollo |

---

## Evaluación (versión ligera, no el framework completo de métricas)

En vez de implementar métricas formales de recuperación (Hit Rate, MRR), se define un pequeño set de preguntas de prueba con respuesta conocida, usando los documentos ficticios, por ejemplo:

- "¿Cuánto se ejecutó del presupuesto de formación y empleo?" → debe recuperar el fragmento del informe financiero con esa partida
- "¿Cuántas personas atendió el convenio con Cáritas?" → debe recuperar el fragmento correspondiente del informe de convenios

Si el sistema recupera el fragmento correcto para este set de preguntas, se considera validado para el MVP.

---

## Entregables de la fase

- [ ] `src/rag/splitter.py`
- [ ] `src/rag/embeddings.py`
- [ ] `src/rag/retriever.py`
- [ ] Base de datos vectorial de ChromaDB poblada con los documentos ficticios
- [ ] Registro del set de preguntas de prueba y resultado de la evaluación manual

## Próxima fase

**Fase 4 — Generación de la memoria**: el agente Redactor usará este sistema de recuperación para obtener el contexto relevante y redactar cada sección de la memoria, en vez de recibir documentos completos como en la Fase 2.