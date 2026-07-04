# Asistente IA para la Memoria Anual de Actividades
### Departamento de Desarrollo Local y Empleo — Ayuntamiento de San Sebastián de los Reyes

> Proyecto pedagógico de Factoría F5 en colaboración con el Ayuntamiento de San Sebastián de los Reyes.

---

## 1. Descripción del proyecto

El Departamento de Desarrollo Local y Empleo elabora anualmente una **Memoria de Actividades**, actualmente de forma manual: se recopilan datos de informes financieros, convenios y la agencia de colocación, y se redacta un documento extenso, además de una versión resumida para ciudadanos, inversores y responsables políticos.

Este proyecto desarrolla un **asistente de inteligencia artificial** que automatiza ese proceso, a partir de una arquitectura RAG (Retrieval-Augmented Generation) totalmente **open source y local**.

### El asistente debe:

1. **Leer y procesar** los documentos facilitados por el departamento (PDF, Word, Excel)
2. **Generar dos versiones** de la memoria:
   - Versión técnica completa (para auditores y administración)
   - Informe ejecutivo divulgativo (para ciudadanos, inversores y responsables políticos)
3. **Adaptar el tono** del contenido según la audiencia
4. Producir el contenido en **español e inglés**

### Fuera de alcance en esta fase (mejoras futuras)

- Extracción automática de datos de las webs municipales (ssreyes.org, sansenet.com)
- Extracción automática de redes sociales (X, Facebook)
- Integración con sistemas internos del Ayuntamiento

Mientras se reciben datos reales del Ayuntamiento, el desarrollo avanza con **documentos ficticios** que replican la estructura esperada, para no bloquear el trabajo del equipo.

---

## 🚀 Instalación

### Requisitos previos

- Python 3.10+
- [Ollama](https://ollama.com) instalado
- `uv` instalado ([instrucciones](https://docs.astral.sh/uv/))

### Pasos

```bash
# Clonar el repositorio
git clone https://github.com/Marizqdo/sanse-llm-assistant.git
cd sanse-llm-assistant

# Crear entorno virtual con uv
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
uv sync

# Descargar modelos de Ollama
ollama pull llama3.2:3b
ollama pull nomic-embed-text



## 2. Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│              INTERFAZ WEB (Streamlit)                        │
│   Carga de documentos → Botón "Generar Memoria" → Descarga   │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         LOADER                                │
│   PDF (pdfplumber) · Word (python-docx) · Excel (pandas)      │
│   → texto normalizado + metadata                              │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         RAG (LangChain: splitter + embeddings + ChromaDB)    │
│   Chunking → embeddings (Ollama) → búsqueda vectorial         │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENTES DE IA (LangChain + Ollama)          │
│                                                                │
│  Agente REDACTOR   → extrae datos del contexto RAG y          │
│                       redacta cada sección de la memoria       │
│                                                                │
│  Componente REVISOR (código, no LLM) → valida que las cifras  │
│                       generadas coinciden con la fuente         │
│                                                                │
│  Agente ADAPTADOR  → ajusta tono (técnico ↔ divulgativo)      │
│                       y traduce (ES ↔ EN) en un mismo paso     │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         GENERADOR DE DOCUMENTO (python-docx)                 │
│   Combina secciones → memoria técnica + versión ejecutiva     │
└─────────────────────────────────────────────────────────────┘
```

**Por qué solo 2 agentes de IA (Redactor, Adaptador) y no más:** cada agente adicional implica una llamada extra al modelo de lenguaje. Al trabajar con GPU limitada, se prioriza un diseño con pocas llamadas, robustas y bien probadas, sobre una arquitectura más granular pero más lenta. La validación de cifras se implementa como código determinista (comparación de números), no como un agente de IA, porque es una tarea que no necesita "inteligencia" — necesita precisión.

---

## 3. Stack tecnológico

Todo el stack es **open source**, pensado para ejecutarse en local sin depender de APIs de pago ni enviar datos del Ayuntamiento fuera de la infraestructura del equipo.

| Categoría | Tecnología | Función |
|---|---|---|
| Entorno / paquetes | `uv` | Gestión de dependencias y entorno virtual |
| LLM (local) | Ollama + Llama 3.2 3B | Generación de texto |
| Embeddings | Ollama + nomic-embed-text | Vectorización para búsqueda semántica |
| Base de datos vectorial | ChromaDB | Almacén de embeddings |
| Orquestación RAG | LangChain | Splitters, integración con ChromaDB y Ollama |
| Interfaz web | Streamlit | Subida de documentos y descarga de resultados |
| Lectura de documentos | pdfplumber, python-docx, pandas/openpyxl | Extracción por formato |
| Generación de Word | python-docx | Documento final descargable |
| Contenedores | **Docker** | Empaquetar el proyecto para que corra igual en cualquier máquina del equipo |
| Exploración/prototipado | Jupyter notebooks | Laboratorio de pruebas antes de escribir el código definitivo |
| Control de versiones | **GitHub** | Repositorio del código |
| Gestión de tareas | **GitHub Projects (Kanban)** | Seguimiento del trabajo del equipo |
| Diseño de interfaz (opcional) | Figma | Mockups de la interfaz Streamlit antes de construirla |

### Flujo notebook → código definitivo

Todo prototipo (probar un prompt, probar una consulta al RAG) se hace primero en un notebook dentro de `notebooks/`. Solo cuando ese código funciona de forma fiable, se traslada como función/módulo limpio a `src/`. Los notebooks nunca son la versión final de la lógica del proyecto — son el espacio de pruebas.

---

## 4. Estructura del repositorio

```
sanse-llm-assistant/
├── notebooks/              # Laboratorio de pruebas
├── src/
│   ├── rag/                 # Loader, splitter, embeddings, retriever
│   ├── agents/               # Redactor, Adaptador
│   ├── validation/           # Revisor (código, no LLM)
│   ├── output/                # Generador de documento Word
│   └── app.py                  # Interfaz Streamlit
├── data/
│   ├── raw/                  # Documentos de entrada (ficticios / reales)
│   └── processed/
├── config/
│   ├── prompts.yaml
│   └── settings.yaml
├── docs/                     # Documentación del proyecto (este README y los de cada fase)
├── outputs/                  # Memorias generadas
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## 5. Equipo y reparto de responsabilidades

Somos 4 personas: 1 Data Analyst, 1 Full Stack, 2 Data Engineers. El equipo trabaja de forma colaborativa ("todos entre todos"), pero cada persona tiene una **responsabilidad principal**, combinando un rol ágil (Scrum/Product) con un bloque técnico del pipeline:

| Persona (perfil) | Rol ágil | Responsabilidad técnica principal | Componentes |
|---|---|---|---|
| **Data Analyst** | Documentación y validación de datos | `docs/`, componente Revisor (`src/validation/`) |
| **Full Stack** | Interfaz y Dockerización | `src/app.py`, `src/output/`, `Dockerfile` |
| **Data Engineer (1)** | — | Datos y RAG | `src/rag/` (loader, splitter, embeddings, ChromaDB) |
| **Data Engineer (2)** | — | Agentes e IA | `src/agents/` (Redactor, Adaptador), `config/prompts.yaml` |
| **Product Owner** — prioriza el backlog, interlocutor principal con el stakeholder (Ayuntamiento) |
| **Scrum Master** — facilita las dailies, mantiene el tablero Kanban, destapa bloqueos |

El Product Owner y el Scrum Master no dejan de programar: su responsabilidad ágil se suma a su bloque técnico, no lo sustituye.

---

## 6. Flujo de trabajo del equipo

- **Control de versiones:** GitHub, con ramas por funcionalidad (`feature/loader`, `feature/agente-redactor`, etc.) y Pull Requests antes de fusionar a `main`.
- **Gestión de tareas:** tablero Kanban en GitHub Projects, con columnas por fase del proyecto (ver documentación por fase en `docs/`).
- **Daily:** reunión diaria y breve (10-15 min) para compartir avance, bloqueos y próximos pasos de cada persona. La facilita el Scrum Master.
- **Reuniones semanales con el stakeholder:** 4 sesiones con objetivos definidos, coordinadas por el Product Owner.

---

## 7. Documentación adicional

Cada fase del proyecto tiene su propio documento de referencia en `docs/`, con el detalle técnico y las tareas específicas de esa fase:

- `docs/fase_0_preparacion.md`
- `docs/fase_1_captura_datos.md`
- `docs/fase_2_rag.md`
- `docs/fase_3_generacion.md`
- `docs/fase_4_adaptacion_validacion.md`
- `docs/fase_5_interfaz_entrega.md`

*(Se crean progresivamente a medida que el equipo avanza por cada fase)*

---

## 8. Cómo ejecutar el proyecto localmente

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd asistente-memoria

# Crear entorno virtual e instalar dependencias
uv venv
source .venv/bin/activate
uv sync

# Instalar y arrancar Ollama, descargar los modelos
ollama pull llama3.2:3b
ollama pull nomic-embed-text

# Levantar el proyecto con Docker (cuando esté disponible)
docker compose up
```

---

## 9. Estado actual del proyecto

| Componente | Estado |
|---|---|
| Loader (PDF/Word/Excel) | ✅ Construido y probado |
| Datos ficticios de prueba | ✅ Creados |
| Cuestionario al Ayuntamiento | 🔄 Enviado, pendiente de respuesta |
| RAG (splitter, embeddings, ChromaDB) | ⏳ Pendiente |
| Agentes (Redactor, Adaptador) | ⏳ Pendiente |
| Componente Revisor | ⏳ Pendiente |
| Interfaz Streamlit | ⏳ Pendiente |
| Dockerización | ⏳ Pendiente |