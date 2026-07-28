# Asistente IA para la Memoria Anual de Actividades
### Departamento de Desarrollo Local y Empleo — Ayuntamiento de San Sebastián de los Reyes

> Proyecto pedagógico de Factoría F5 en colaboración con el Ayuntamiento de San Sebastián de los Reyes.

---

## 1. Descripción del proyecto

El Departamento de Desarrollo Local y Empleo elabora anualmente una **Memoria de Actividades**, actualmente de forma manual: se recopilan datos de informes financieros, convenios y la agencia de colocación, y se redacta un documento extenso, en español e inglés.

Este proyecto desarrolla un **asistente de inteligencia artificial** que automatiza ese proceso: sube los documentos originales (PDF, Word, Excel), un pipeline de agentes los interpreta y sintetiza, y devuelve un `.docx` con la memoria redactada en español e inglés, listo para revisión humana.

### Fuera de alcance en esta fase (mejoras futuras)

- Extracción automática de datos de las webs municipales (ssreyes.org, sansenet.com) o de redes sociales
- Integración con sistemas internos del Ayuntamiento
- Variantes diferenciadas por audiencia (técnica vs. divulgativa) — hoy solo hay traducción ES/EN

Mientras se reciben datos reales del Ayuntamiento, el desarrollo avanza con **documentos ficticios** que replican la estructura esperada.

---

## 2. Punto de entrada: el pipeline

Todo el proceso se define en [`src_agents/graph/workflow.py`](src_agents/graph/workflow.py), un grafo de [LangGraph](https://langchain-ai.github.io/langgraph/) con **3 nodos**:

```
START → ingesta → analista → generador → END
```

| Nodo (función) | Módulo | Qué hace |
|---|---|---|
| `agente_ingesta` | `src_agents/agents/ingestion.py` (usa `src_agents/rag/extractor_generico.py`) | Lee una carpeta con los ficheros subidos (PDF/DOCX/XLSX) y los convierte en una lista de `BloqueContenido` (bloques de tipo `"texto"` o `"tabla"`, con su fuente y etiqueta de origen) |
| `agente_analista` | `src_agents/agents/analyst.py` | Por cada bloque, llama a un LLM de Groq para extraer pares `concepto: valor` — trocea tablas grandes en bloques de 20 filas y reintenta ante `RateLimitError` |
| `agente_generador_informe` | `src_agents/services/report_generator.py` | Sintetiza los datos del Analista en las 4 secciones fijas de la memoria (Introducción, Análisis por Plan, Actividad Operativa, Conclusiones), valida que las cifras citadas aparezcan en el texto generado, traduce al inglés y escribe el `.docx` final |

El estado que viaja por el grafo está tipado en [`src_agents/models/state.py`](src_agents/models/state.py) (`EstadoPipeline`): cada nodo lee lo que necesita del estado y devuelve solo el campo que actualiza (`documents`, `analysis`, `final_document`).

### El Adaptador (traducción EN) no es un nodo del grafo

`src_agents/agents/adaptador_en.py` (`agente_adaptador_en`) sí se usa, y hace la traducción real ES→EN de la memoria — pero **no aparece como nodo en `workflow.py`**. `report_generator.py` lo llama como función normal, 4 veces (una por sección), porque un nodo de LangGraph se ejecuta una sola vez por turno y aquí hace falta repetir la llamada con un texto distinto cada vez. Internamente aplica reintento, troceo por límite de tokens y limpieza de fugas de razonamiento (`<think>...</think>`) de los modelos de Groq.

### Módulos que existen pero no forman parte de esta cadena

El repositorio conserva código de una arquitectura anterior, más granular, que se simplificó para no gastar cuota de Groq en pasos cuyo resultado el pipeline final no consume. Sigue siendo válido pero **no está conectado**:

- `src_agents/agents/redactor.py` / `redactor_v1.py` — agente Redactor (generaba un borrador libre por sección; el Generador actual sintetiza directamente desde `state["analysis"]`, sin pasar por un draft)
- `src_agents/agents/reviewer.py`, `src_agents/validation/revisor.py` — agente/componente Revisor (comparaba el draft del Redactor contra el Analista; el Generador actual incorpora su propia validación de cifras con `validar_memoria`)
- `src_agents/rag/loader.py`, `retriever.py`, `preparador_contexto.py`, `enriquecimiento_financiero.py`, `adaptador_langchain.py` — un pipeline RAG con embeddings/ChromaDB que se sustituyó por la extracción directa de `extractor_generico.py` + interpretación por LLM
- `src_agents/services/docx_reader.py`, `excel_reader.py` — lectores previos, sustituidos por `extractor_generico.py`

Ver [`docs/07_README_generador_y_grafo`](docs/07_README_generador_y_grafo) para el detalle de por qué se simplificó el grafo a 3 nodos.

---

## 3. Interfaz: `streamlit_sanse.py`

[`streamlit_sanse.py`](streamlit_sanse.py) (en la raíz del repo) es la interfaz web y el punto de entrada para el usuario final. Flujo:

1. El usuario sube uno o varios ficheros (PDF/DOCX/XLSX) con `st.file_uploader`.
2. Al pulsar **"Generar Memoria"**, los ficheros se guardan en una carpeta temporal (el nodo de ingesta espera una carpeta, no una lista de rutas sueltas).
3. Se invoca `pipeline.stream({"uploaded_files": [str(tmp_dir)]}, stream_mode="updates")` — importado directamente de `src_agents.graph.workflow` — y cada actualización de nodo (`ingesta` / `analista` / `generador`) se refleja en un `st.status` con la fase en curso.
4. Al terminar, se lee el `.docx` real dejado en `state["final_document"]` (no se reconstruye nada en la interfaz) y se separan sus párrafos en bloques **español / inglés / notas de validación** según el estilo de párrafo de Word (`Title`, `Heading 1`).
5. Se muestran ambos bloques y, si hay incidencias de validación, un `st.expander` con las discrepancias detectadas. Un único botón descarga el `.docx` final.

Ejecutar la interfaz:

```bash
streamlit run streamlit_sanse.py
```

> Existe también `streamlit_prueba.py` en la raíz — versión previa/de pruebas de la interfaz, sustituida por `streamlit_sanse.py` (ver cabecera de ese fichero para el historial de cambios).

---

## 4. Instalación y configuración

### Requisitos previos

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) instalado
- Una API key de [Groq](https://console.groq.com/) (el pipeline llama a modelos de Groq, no ejecuta un LLM local)

### Pasos

```bash
# Clonar el repositorio
git clone https://github.com/Bootcamp-IA-P6/sanse-llm-assistant.git
cd sanse-llm-assistant

# Crear entorno virtual e instalar dependencias
uv venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac
uv sync

# Configurar variables de entorno
cp .env.example .env   # si no existe, crear .env a mano (ver tabla abajo)
```

### Variables de entorno (`.env`)

| Variable | Obligatoria | Por defecto | Uso |
|---|---|---|---|
| `GROQ_API_KEY` | Sí | — | API key de Groq, usada por los 3 agentes que llaman a un LLM (Analista, Generador, Adaptador) |
| `GROQ_MODEL_ANALISTA` | No | `llama-3.3-70b-versatile` | Modelo usado por `agente_analista` |
| `GROQ_MODEL_MEMORIA` | No | `openai/gpt-oss-120b` | Modelo usado por `sintetizar_memoria` (dentro del Generador) |
| `GROQ_MODEL_ADAPTADOR` | No | `qwen/qwen3.6-27b` | Modelo usado por `agente_adaptador_en` para traducir |
| `NOMBRE_ENTIDAD` | No | `Ayuntamiento` | Nombre mostrado en la portada del `.docx` generado |
| `OUTPUT_DIR` | No | `data/output` | Carpeta donde se escribe `memoria_final.docx` |

### Arrancar la aplicación

```bash
streamlit run streamlit_sanse.py
```

---

## 5. Stack tecnológico

| Categoría | Tecnología | Función |
|---|---|---|
| Entorno / paquetes | `uv` | Gestión de dependencias y entorno virtual |
| Orquestación del pipeline | LangGraph | Grafo de 3 nodos (`src_agents/graph/workflow.py`) |
| LLM | Groq (`langchain-groq`) — modelos Llama 3.3, GPT-OSS, Qwen según agente | Extracción de datos, síntesis de la memoria y traducción |
| Interfaz web | Streamlit | Subida de documentos, progreso del pipeline y descarga del resultado |
| Lectura de documentos | `pdfplumber` (PDF), `python-docx` (Word), `openpyxl`/`pandas` (Excel) | Extracción genérica por formato (`extractor_generico.py`) |
| Generación de Word | `python-docx` | Documento final `.docx` (ES + EN) |
| Validación de datos | Código determinista (`validar_memoria`, sin LLM) | Comprueba que las cifras del Analista aparecen en el texto generado |
| Control de versiones | GitHub | Repositorio del código |

> Nota: `chromadb` figura en `pyproject.toml` porque el proyecto exploró una arquitectura RAG con base vectorial (ver `src_agents/rag/loader.py`, `retriever.py`); esa vía no está conectada al pipeline actual, que interpreta los documentos directamente con LLM en vez de recuperación semántica.

---

## 6. Estructura del repositorio

```
sanse-llm-assistant/
├── streamlit_sanse.py          # Interfaz Streamlit activa (punto de entrada de usuario)
├── streamlit_prueba.py         # Versión anterior de la interfaz
├── src_agents/
│   ├── graph/
│   │   └── workflow.py         # Punto de entrada del pipeline: define el grafo de 3 nodos
│   ├── agents/
│   │   ├── ingestion.py        # Nodo "ingesta"
│   │   ├── analyst.py          # Nodo "analista"
│   │   ├── adaptador_en.py     # Traductor ES→EN, llamado como función desde el Generador
│   │   ├── redactor.py / redactor_v1.py   # No conectados al grafo actual
│   │   └── reviewer.py         # No conectado al grafo actual
│   ├── services/
│   │   ├── report_generator.py # Nodo "generador": síntesis, validación, traducción, .docx final
│   │   ├── docx_reader.py / excel_reader.py  # No usados por el pipeline actual
│   ├── rag/
│   │   ├── extractor_generico.py  # Extracción real de PDF/DOCX/XLSX (usado por ingesta)
│   │   └── loader.py, retriever.py, preparador_contexto.py,
│   │       enriquecimiento_financiero.py, adaptador_langchain.py  # RAG/ChromaDB, no conectado
│   ├── validation/
│   │   └── revisor.py          # No conectado al grafo actual
│   └── models/
│       └── state.py            # EstadoPipeline y modelos Pydantic compartidos
├── data/
│   ├── raw/                    # Documentos de entrada (ficticios / reales)
│   ├── processed/
│   └── output/                 # Memorias .docx generadas (OUTPUT_DIR)
├── config/                     # prompts.yaml / settings.yaml (placeholders, aún sin uso)
├── notebooks_agents/           # Laboratorio de pruebas antes de escribir código definitivo
├── docs/                       # Documentación por fase y por agente
├── Dockerfile / docker-compose.yml
├── pyproject.toml / uv.lock
└── README.md
```

---

## 7. Documentación adicional

Cada fase y cada agente tiene su propio documento de referencia en [`docs/`](docs/):

- `docs/00-preparacion.md`
- `docs/01-captura_datos.md`, `docs/01_README_extractor_agent.md`
- `docs/02-validacion_modelo.md`, `docs/02_README_analyst_agent.md`
- `docs/03-rag.md`, `docs/03_README_workflow_graph.md`
- `docs/04-generacion.md`, `docs/04_README_adaptador_en.md`
- `docs/05-adaptacion_validacion.md`, `docs/05_README_reviewer_agent.md`
- `docs/06-interfaz_entrega.md`, `docs/06-README_analyst_narrative_text_agent.md`
- `docs/07_README_generador_y_grafo` — resumen de por qué el grafo se simplificó a 3 nodos (la referencia más directa para entender el estado actual de `workflow.py`)

---

## 8. Estado actual del proyecto

| Componente | Estado |
|---|---|
| Extracción de documentos (PDF/Word/Excel) — `extractor_generico.py` | ✅ Construido y en uso |
| Agente Analista (tablas + texto narrativo) | ✅ Construido y en uso |
| Generador de memoria (síntesis 4 secciones + validación + traducción) | ✅ Construido y en uso |
| Grafo LangGraph de 3 nodos (`workflow.py`) | ✅ Construido y en uso |
| Interfaz Streamlit (`streamlit_sanse.py`) conectada al pipeline real | ✅ Conectada |
| Redactor / Revisor / RAG con ChromaDB | 🗄️ Código existente, no conectado al pipeline actual |
| Ejecución completa validada con los 3 documentos reales del Ayuntamiento juntos | ⏳ Pendiente |
| Plantilla oficial / formato final del `.docx` (paginación) | ⏳ Pendiente de ajuste |
| Dockerización | ⏳ Pendiente |
