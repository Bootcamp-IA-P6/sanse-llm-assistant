# Fase 0 — Preparación y definición

> Documento de referencia para la Fase 0 del proyecto. Ver `README.md` en la raíz para la visión general.

## Objetivo de la fase

Sentar las bases del proyecto antes de escribir el código del pipeline: definir el alcance con el stakeholder, dejar el entorno técnico funcionando, y disponer de datos con los que poder empezar a construir sin depender de que lleguen los datos reales del Ayuntamiento.

---

## Checklist de tareas

| # | Tarea | Estado | Responsable principal |
|---|---|---|---|
| 0.1 | Kick-off del equipo: presentación, expectativas y alcance | ✅ Hecho | Todo el equipo |
| 0.2 | Cuestionario al Ayuntamiento (inputs, formatos, idiomas, prioridades) | 🔄 Enviado, esperando respuesta | Product Owner |
| 0.3 | Obtener datos de prueba reales (anonimizados si aplica) | ⏳ Pendiente de respuesta del Ayuntamiento | Product Owner |
| 0.4 | Obtener una memoria anual de años anteriores como referencia de formato/tono | ⏳ Pendiente de respuesta del Ayuntamiento | Product Owner |
| 0.5 | Confirmar tipo de asistente (generador de documentos vs. chatbot) | ✅ Confirmado: generador de documentos | Product Owner |
| 0.6 | Configurar entorno técnico (uv, Python, Ollama, modelos, Docker) | ✅ Hecho (uv, Ollama y modelos instalados) · 🔄 Docker pendiente de integrar | Data Engineers / Full Stack |
| 0.7 | Crear datos de prueba ficticios (financiero, convenios, agencia de colocación) | ✅ Hecho | Data Engineer (RAG) |
| 0.8 | Crear repositorio en GitHub y tablero Kanban | ⏳ Pendiente | Scrum Master |
| 0.9 | Definir estructura de carpetas del proyecto | ✅ Hecho (ver `README.md`, sección 4) | Data Engineers |

---

## Detalle por tarea

### 0.1 — Kick-off del equipo
Reunión inicial para repartir roles (ver `README.md`, sección 5) y alinear expectativas sobre el alcance del MVP dado el plazo de 4 semanas.

### 0.2 — Cuestionario al Ayuntamiento
Preguntas enviadas cubriendo:
- Formato y estructura de los informes (financiero, convenios, agencia de colocación)
- Acceso a datos reales de ejemplo
- Idiomas requeridos (confirmado: **español e inglés**, sin euskera)
- Formato de salida esperado (documento descargable)
- Infraestructura disponible y restricciones de confidencialidad
- Alcance mínimo viable esperado para la presentación del 29 de julio

*Pendiente: respuesta del Ayuntamiento. Mientras tanto, se avanza en paralelo con datos ficticios (ver 0.7).*

### 0.3 y 0.4 — Datos y memoria de referencia reales
Bloqueados hasta respuesta del stakeholder. Cuando lleguen, sustituirán a los documentos ficticios en `data/raw/`, y la memoria de referencia servirá para ajustar la plantilla de secciones que use el agente Redactor.

### 0.5 — Tipo de asistente
Confirmado con el equipo: el asistente es un **generador de documentos**, no un chatbot conversacional. El usuario sube documentos y descarga la memoria generada; no hay una interacción de preguntas y respuestas libre.

### 0.6 — Entorno técnico
Instalado y verificado:
- `uv` (gestor de paquetes y entornos virtuales)
- Ollama, con los modelos `llama3.2:3b` y `nomic-embed-text` descargados
- Python 3.10+

Pendiente de definir en esta fase:
- `Dockerfile` y `docker-compose.yml` para empaquetar la aplicación y (previsiblemente) Ollama como servicio independiente
- Repositorio Git inicializado con la estructura de carpetas ya definida

### 0.7 — Datos de prueba ficticios
Creados tres documentos que replican la estructura esperada de los reales:
- `financiero_cuatrimestral_1.pdf` — informe de control financiero
- `convenios_2026.docx` — seguimiento de convenios
- `agencia_colocacion.xlsx` — histórico de colocaciones

Ya usados para construir y probar el `loader.py` (ver Fase 1).

### 0.8 — Repositorio y Kanban (pendiente)
Por hacer:
- Crear repositorio en GitHub
- Configurar tablero Kanban (GitHub Projects) con columnas por fase
- Definir convención de ramas (`feature/...`) y flujo de Pull Requests

### 0.9 — Estructura de carpetas
Ya definida y documentada en el `README.md` principal (sección 4).

---

## Entregables de la fase

- [x] Entorno técnico funcional (uv + Ollama + modelos)
- [x] Tres documentos ficticios de prueba
- [x] Estructura de carpetas del proyecto
- [ ] Repositorio GitHub + tablero Kanban
- [ ] Respuestas del cuestionario del Ayuntamiento
- [ ] `Dockerfile` / `docker-compose.yml` iniciales

## Riesgo a vigilar

La dependencia de la respuesta del Ayuntamiento (0.2, 0.3, 0.4) es el mayor riesgo de calendario del proyecto. Se mitiga avanzando en paralelo con datos ficticios, pero conviene que el Product Owner haga seguimiento activo para no perder más tiempo del necesario esperando esa respuesta.