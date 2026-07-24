# streamlit_prueba.py

## Qué es
Copia de trabajo de `app.py` (diseño e interfaz originales de Paloma), reconectada al pipeline de agentes actual (`src_agents/graph/workflow.py`) en lugar de a los módulos antiguos que usa `app.py` (`redactor.py`, `validation/revisor.py`, `rag/loader.py`).

Se creó como archivo aparte, sin tocar `app.py`, para poder probar la conexión sin arriesgar la interfaz original de Paloma, mientras el equipo decide si se sustituye `app.py` por este archivo o se fusionan.

Contexto: issue #94, PR #95.

## Cómo ejecutarlo
Desde la raíz del proyecto:

uv run streamlit run streamlit_prueba.py

Importante usar `uv run` y no `streamlit run` directamente — si no, puede coger el Python del sistema en vez del entorno virtual del proyecto, y faltarán dependencias como `python-docx`.

Necesita un `.env` en la raíz con `GROQ_API_KEY` (y opcionalmente `GROQ_MODEL_REDACTOR` / `GROQ_MODEL_ADAPTADOR` / `GROQ_MODEL_ANALISTA`; si no se definen, usa los valores por defecto del código).

## Qué hace
1. Se suben uno o varios documentos (PDF, Word, Excel).
2. Al pulsar "Generar Memoria", los archivos se guardan en una carpeta temporal y se llama a `pipeline.invoke(...)` — el mismo pipeline LangGraph que usan los notebooks (Ingesta → Analista → Redactor → Revisor → Adaptador).
3. Se muestra el informe en español e inglés, con las incidencias de validación en un desplegable.
4. Descarga en `.docx` o `.txt`.

## Diferencias respecto a app.py
- Sin selectores de modelo/temperatura/secciones: el pipeline nuevo no los expone (decisión de equipo).
- Usa `st.session_state` para que el informe y los botones de descarga no desaparezcan al pulsar "Descargar" (recarga propia de Streamlit).

## Pruebas realizadas (24 julio)
- Word financiero solo: correcto, informe completo en ES/EN.
- Excel (agencia de innovación y empleo) solo: correcto, cubre los 5 planes del Excel con metas, datos 2024/2025 y texto narrativo de "Principales avances".
- Word + Excel juntos: correcto, combina ambos documentos con éxito (tras algún intento fallido, ver más abajo).

## Pendiente / limitaciones conocidas
- El Adaptador trocea el borrador en bloques para traducir y los manda sin pausa entre peticiones. Cuantos más bloques (documentos de entrada más grandes o combinados), mayor la probabilidad de superar el límite de tokens por minuto del modelo y recibir un error 429 — ya observado hoy con Word + Excel en más de un intento. Pendiente: añadir una pausa entre bloques.
- El número de incidencias no refleja necesariamente datos perdidos: el Revisor compara texto de forma literal, así que cifras escritas en palabras en vez de dígitos, con otro formato decimal, o texto narrativo parafraseado, se marcan como incidencia aunque sí estén presentes en el informe.
- Datos ambiguos en el documento de origen pueden interpretarse de forma distinta entre ejecuciones: un valor mal formado del Excel ("2+1") se citó tal cual en una prueba, y en otra el modelo lo interpretó y calculó "3". El Revisor detectó bien la discrepancia como incidencia — es un buen ejemplo real de por qué la revisión humana importa.


