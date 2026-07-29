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

---

# Fase 6 — Interfaz, despliegue y entrega

> Esta sección documenta la interfaz Streamlit (`streamlit_sanse.py`), el despliegue en Streamlit Cloud y la dockerización de la aplicación.

## Interfaz Streamlit

La interfaz está en `streamlit_sanse.py` (raíz del proyecto) y conecta directamente con el pipeline real de LangGraph:

```
Ingesta → Analista → Redactor → Revisor → Adaptador
```

**Funcionalidades:**
- Subida de documentos (PDF, DOCX, XLSX)
- Ejecución del pipeline con progreso por fases en tiempo real
- Visualización del informe en español e inglés
- Panel de incidencias para revisión humana
- Descarga del resultado en `.docx` y `.txt`

**Lanzar en local:**
```bash
# Activar el entorno (Python 3.12 — obligatorio, 3.14 tiene bugs con httpx)
source .venv/Scripts/activate

# Lanzar
python -m streamlit run streamlit_sanse.py --server.port 8507
```

O usar la tarea de VS Code: `Ctrl+Shift+P` → *Run Task* → **Streamlit: streamlit_sanse**

> ⚠️ Usar siempre el venv del proyecto (`.venv/`). Lanzar con el Python del sistema (3.14) bloquea las conexiones HTTPS a la API de Groq.

---

## Configuración de la clave API (local)

Las variables de entorno se leen del archivo `.env` en la raíz (no se sube a GitHub, está en `.gitignore`):

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL_ADAPTADOR=llama-3.1-8b-instant
GROQ_MODEL_REDACTOR=openai/gpt-oss-120b
GROQ_MODEL_MEMORIA=openai/gpt-oss-120b
```

---

## Despliegue en Streamlit Cloud

**URL pública:** https://sanse-llm-assistant.streamlit.app/

**Pasos para desplegar o actualizar:**

1. Asegurarse de que los cambios están en la rama `app` y pusheados a GitHub:
   ```bash
   git push origin app
   ```

2. En [share.streamlit.io](https://share.streamlit.io) la app está configurada así:
   - Repositorio: `Bootcamp-IA-P6/sanse-llm-assistant`
   - Branch: `app`
   - Main file: `streamlit_sanse.py`

3. **Configurar los secrets** (sólo la primera vez o cuando cambie la clave):
   - En el dashboard de Streamlit Cloud → tu app → **⋮** → **Settings** → **Secrets**
   - Pegar el contenido de `.streamlit/secrets.toml` con la clave real:

   ```toml
   GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   GROQ_MODEL_ADAPTADOR = "llama-3.1-8b-instant"
   GROQ_MODEL_REDACTOR = "openai/gpt-oss-120b"
   GROQ_MODEL_MEMORIA = "openai/gpt-oss-120b"
   ```

   - Guardar → la app se reinicia automáticamente.

> ⚠️ El archivo `.streamlit/secrets.toml` está en `.gitignore` y **nunca se sube a GitHub**. Los secrets sólo se configuran desde el dashboard de Streamlit Cloud.

---

## Dockerización

### Imagen construida

```
sanse-llm-assistant:latest
palomita/sanse-llm-assistant:latest
```

### Construir la imagen

```bash
docker build -t sanse-llm-assistant:latest .
```

### Correr con docker-compose (recomendado)

El `docker-compose.yml` en la raíz del proyecto levanta la app pasando el `.env` automáticamente:

```bash
docker compose up
```

La app estará disponible en **http://localhost:8507**.

### Correr sin docker-compose

```bash
docker run --rm -p 8507:8507 --env-file .env sanse-llm-assistant:latest
```

### Subir a Docker Hub

```bash
docker push palomagom/sanse-llm-assistant:latest
```

### ¿Es necesario docker-compose?

No es estrictamente necesario si sólo hay un servicio, pero agiliza el flujo:

| | `docker run` | `docker compose up` |
|---|---|---|
| Recordar flags y puertos | ✋ Manual | ✅ Automático |
| Pasar `.env` | `--env-file .env` | Declarado en `docker-compose.yml` |
| Reinicio automático | `--restart` flag | `restart: unless-stopped` |
| Escalar servicios futuros (BD, etc.) | Complejo | Sencillo |

Para MVP con un solo servicio, `docker run --env-file .env` es suficiente. Si en el futuro se añade ChromaDB persistente u otros servicios, docker-compose será necesario.

---

## Archivos clave de esta fase

| Archivo | Descripción |
|---|---|
| `streamlit_sanse.py` | Interfaz Streamlit principal |
| `Dockerfile` | Imagen Docker basada en Python 3.12-slim |
| `docker-compose.yml` | Orquestación local con `.env` |
| `.dockerignore` | Excluye `.venv`, `.env`, notebooks y datos raw |
| `requirements.txt` | Dependencias para Docker y Streamlit Cloud |
| `.streamlit/secrets.toml` | Secrets locales (en `.gitignore`, no se sube) |
| `.python-version` | Fija Python 3.12 en el directorio del proyecto |