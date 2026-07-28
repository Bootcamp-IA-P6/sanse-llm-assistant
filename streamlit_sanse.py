"""
streamlit_sanse.py — Interfaz Streamlit del Asistente de Memoria Anual
Departamento de Desarrollo Local y Empleo · Ayuntamiento de San Sebastián de los Reyes

Basado en streamlit_prueba.py, con correcciones de accesibilidad/UX:
1. Los cuadros de alerta (st.info / st.warning / st.error) y el expander de
   incidencias fuerzan colores propios (fondo + texto), en vez de depender del
   tema claro/oscuro del navegador — evita texto negro sobre fondo negro,
   o texto amarillo sobre fondo amarillo.
2. El botón "quitar archivo" de cada fichero subido queda más separado del
   nombre del fichero.
3. La generación del informe muestra un st.status con spinner y va
   actualizando la fase del pipeline en curso (ingesta, análisis, generación
   del informe final), en vez de un spinner mudo sin detalle.

Actualizado (27/07) para el pipeline simplificado a 3 nodos
(ingesta -> analista -> generador -> END): el generador ya no vuelca
state["draft"]/state["draft_en"]/state["review"] (esos campos ya no
existen) -- sintetiza su propia memoria de 4 secciones desde
state["analysis"] y escribe el .docx final en state["final_document"].
Esta interfaz ahora lee ese archivo real en vez de reconstruir uno
propio. Se retira también el botón de descarga en .txt (decisión de
equipo, 27/07) -- el generador no produce esa versión.

Actualizado (27/07, tarde) tras inspeccionar el DOM real con las
herramientas de desarrollador del navegador:
- El botón de "Seleccionar archivos" y el de borrar cada archivo se
  identifican ahora por su data-testid real (stBaseButton-secondary /
  stBaseButton-borderlessIcon para el de subir, stBaseButton-minimal
  dentro de stFileChipDeleteBtn para el de borrar) en vez de un
  :not(...) que no funcionaba porque ese atributo estaba en un
  elemento distinto al botón.
- Se fuerza visible el control nativo para volver a abrir el lateral
  (stSidebarCollapsedControl), porque seguía oculto al ocultar la
  cabecera completa (header stHeader).
"""

import sys
import tempfile
import time
from pathlib import Path

import streamlit as st
from docx import Document as DocxDocument

from dotenv import load_dotenv
load_dotenv()

# -- Ruta raíz al path para importar src_agents.*
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src_agents.graph.workflow import pipeline

# ---------------------------------------------------------------------------
# Fases del pipeline (para mostrar progreso real durante la generación)
# Actualizado: el grafo ahora solo tiene 3 nodos (ingesta, analista,
# generador) -- redactor/revisor/adaptador ya no son nodos del grafo.
# ---------------------------------------------------------------------------
FASES_PIPELINE = {
    "ingesta": "📥 Leyendo y extrayendo los documentos…",
    "analista": "🔎 Interpretando los datos…",
    "generador": "📝 Sintetizando y traduciendo la memoria…",
}

import base64

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Asistente Memoria Anual · Sanse",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Logo SVG → base64
# ---------------------------------------------------------------------------
_LOGO_PATH = Path(__file__).parent / "assets" / "logo_sanse.svg"
_logo_b64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode() if _LOGO_PATH.exists() else ""
_LOGO_HTML = (
    f'<img src="data:image/svg+xml;base64,{_logo_b64}" '
    f'alt="Ayuntamiento de San Sebastián de los Reyes" style="height:56px;display:block;">'
    if _logo_b64 else '<span style="font-size:2rem">🏛️</span>'
)

# ---------------------------------------------------------------------------
# CSS — estética institucional Ayuntamiento de San Sebastián de los Reyes
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
:root {
    --sanse-red:    #A3132F;
    --sanse-red-dk: #7D0E22;
    --sanse-red-lt: #F9E8EB;
    --sanse-gray:   #F4F4F4;
    --sanse-border: #E0E0E0;
    --sanse-text:   #1A1A1A;
    --sanse-muted:  #5A5A5A;
    --sanse-ok:     #1A6B3C;
    --sanse-warn:   #8B6000;
    --radius:       6px;
    color-scheme: light;
}
html, body, .stApp {
    font-family: 'Open Sans', Arial, sans-serif;
    background: #FFFFFF;
    color: var(--sanse-text);
}
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
/* El control nativo para volver a abrir el lateral vive dentro de la
   cabecera (stHeader). Al ocultar la cabecera entera arriba, se perdía
   también este botón. Se fuerza visible aquí para no perder la única
   forma de recuperar el lateral si se pliega. */
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: block !important;
}
.block-container { padding-top: 0 !important; }
.sanse-header {
    display: flex;
    align-items: center;
    gap: 1.4rem;
    background: #FFFFFF;
    border-bottom: 3px solid var(--sanse-red);
    padding: 1rem 1.8rem 0.9rem;
    margin-bottom: 1.8rem;
}
.sanse-header-text h1 { font-size:1.35rem; font-weight:700; color:var(--sanse-text); margin:0 0 2px; }
.sanse-header-text p  { font-size:.82rem; color:var(--sanse-muted); margin:0; }
section[data-testid="stSidebar"] { background: var(--sanse-gray) !important; border-right: 1px solid var(--sanse-border); }
section[data-testid="stSidebar"] * { color: var(--sanse-text) !important; }
section[data-testid="stSidebar"] h3 { color: var(--sanse-red) !important; font-weight:700; font-size:.95rem; text-transform:uppercase; letter-spacing:.05em; }
section[data-testid="stSidebar"] hr { border-color: var(--sanse-border) !important; }
.section-card { background:white; border:1px solid var(--sanse-border); border-top:4px solid var(--sanse-red); border-radius:var(--radius); padding:1.2rem 1.6rem; margin-bottom:1.2rem; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.section-card h3 { color:var(--sanse-red); margin-top:0; font-size:1rem; }
.badge-ok   { background:var(--sanse-ok);   color:white; padding:2px 10px; border-radius:20px; font-size:.75rem; font-weight:600; }
.badge-warn { background:var(--sanse-warn);  color:white; padding:2px 10px; border-radius:20px; font-size:.75rem; font-weight:600; }

/* --- Subida de archivos ------------------------------------------------ */
[data-testid="stFileUploaderDropzone"] { background:white !important; border:2px dashed var(--sanse-border) !important; border-radius:var(--radius) !important; }
[data-testid="stFileUploaderDropzone"] * { color:var(--sanse-text) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > span { visibility:hidden; display:block; height:0; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > span::before { visibility:visible; display:block; height:auto; content:"Arrastra y suelta los archivos aquí"; font-weight:600; font-size:.95rem; color:var(--sanse-text) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > small { visibility:hidden; display:block; height:0; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > small::before { visibility:visible; display:block; height:auto; content:"Límite 200 MB por archivo  •  PDF, DOCX, XLSX"; font-size:.82rem; color:var(--sanse-muted) !important; }

/* Botón de subir/añadir archivos (versión inicial "Upload" y versión
   compacta "+" que aparece cuando ya hay archivos). Se identifican por
   su data-testid real, comprobado con el inspector del navegador --
   antes se intentaba excluir el botón de borrar con :not(...), pero
   ese atributo estaba en el <small> que lo envuelve, no en el <button>,
   así que nunca se excluía nada. */
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"],
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-borderlessIcon"] {
    background: var(--sanse-red) !important;
    border: none !important;
    border-radius: var(--radius) !important;
    padding: .5rem 1.2rem !important;
}
/* Oculta TODO el contenido interno original del botón (icono "+" y el
   texto "Upload"), en vez de font-size:0 -- ese truco no bastaba
   porque Streamlit reasigna su propio tamaño de letra al <p> interno,
   más específico que el heredado del botón, y el "Upload" se colaba. */
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] *,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-borderlessIcon"] * {
    display: none !important;
}
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"]::after,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-borderlessIcon"]::after {
    content: "Seleccionar archivos";
    font-size: .85rem;
    font-weight: 600;
    color: white;
}
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"]:hover,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-borderlessIcon"]:hover {
    background: var(--sanse-red-dk) !important;
}

/* Botón de borrar archivo (la X): queda pequeño y transparente, sin el
   fondo rojo ni el texto "Seleccionar archivos" superpuesto -- ahora
   se apunta directamente al botón real (stBaseButton-minimal) dentro
   de su envoltorio (stFileChipDeleteBtn), no al envoltorio en sí. */
[data-testid="stFileChipDeleteBtn"] [data-testid="stBaseButton-minimal"] {
    background: transparent !important;
    border: none !important;
    padding: .2rem !important;
}

/* Separación entre el botón "Seleccionar archivos" y la lista de archivos ya subidos */
[data-testid="stFileChips"] { margin-top:1.1rem !important; }

/* Fila de cada archivo ya subido: separar el icono de quitar y explicar qué hace */
[data-testid="stFileChip"] { background:#FFFFFF !important; border:1px solid var(--sanse-border) !important; border-radius:var(--radius) !important; padding-right:.4rem !important; margin-bottom:.5rem !important; }
[data-testid="stFileChip"] * { color:var(--sanse-text) !important; }
[data-testid="stFileChipDeleteBtn"] { margin-left:1rem !important; position:relative; }
[data-testid="stFileChipDeleteBtn"] svg { color:var(--sanse-muted) !important; fill:currentColor !important; }
[data-testid="stFileChipDeleteBtn"]:hover svg { color:var(--sanse-red) !important; }

/* --- Botones ------------------------------------------------------------ */
div.stButton > button[kind="primary"] { background:var(--sanse-red) !important; color:white !important; border:none !important; border-radius:3px !important; padding:.65rem 2.4rem !important; font-weight:700 !important; font-size:.95rem !important; letter-spacing:.08em !important; text-transform:uppercase !important; transition:background .2s, box-shadow .2s; box-shadow:0 2px 6px rgba(163,19,47,.30) !important; }
div.stButton > button[kind="primary"]:hover { background:var(--sanse-red-dk) !important; box-shadow:0 4px 12px rgba(163,19,47,.40) !important; }
div.stButton > button:not([kind="primary"]),
div[data-testid="stDownloadButton"] button:not([kind="primary"]) {
    background:#FFFFFF !important;
    color:var(--sanse-red-dk) !important;
    border:2px solid var(--sanse-red) !important;
    border-radius:3px !important;
    font-weight:700 !important;
    padding:.6rem 2rem !important;
}
div.stButton > button:not([kind="primary"]) *,
div[data-testid="stDownloadButton"] button:not([kind="primary"]) * { color:inherit !important; }
div.stButton > button:not([kind="primary"]):hover,
div[data-testid="stDownloadButton"] button:not([kind="primary"]):hover {
    background:var(--sanse-red-lt) !important;
    border-color:var(--sanse-red-dk) !important;
}

/* --- Alertas (st.info / st.warning / st.error) — contraste garantizado -- */
[data-testid="stAlertContainer"] { border-radius:var(--radius) !important; }
[data-testid="stAlertContentInfo"] { background:var(--sanse-red-lt) !important; border-left:4px solid var(--sanse-red) !important; }
[data-testid="stAlertContentWarning"] { background:#FFF3CD !important; border-left:4px solid var(--sanse-warn) !important; }
[data-testid="stAlertContentError"] { background:#F8D7DA !important; border-left:4px solid #B02A37 !important; }
[data-testid="stAlertContentSuccess"] { background:#D1E7DD !important; border-left:4px solid var(--sanse-ok) !important; }
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentInfo"] * { color:var(--sanse-text) !important; }
[data-testid="stAlertContentWarning"], [data-testid="stAlertContentWarning"] * { color:#664D03 !important; }
[data-testid="stAlertContentError"], [data-testid="stAlertContentError"] * { color:#58151C !important; }
[data-testid="stAlertContentSuccess"], [data-testid="stAlertContentSuccess"] * { color:#0A3622 !important; }
[data-testid="stAlertContentInfo"] svg, [data-testid="stAlertContentWarning"] svg,
[data-testid="stAlertContentError"] svg, [data-testid="stAlertContentSuccess"] svg { fill:currentColor !important; }

/* --- Expander / st.status (incidencias y progreso del pipeline) -------- */
[data-testid="stExpander"] { background:#FFFFFF !important; border:1px solid var(--sanse-border) !important; border-radius:var(--radius) !important; color:var(--sanse-text) !important; }
[data-testid="stExpanderDetails"] { background:#FFFFFF !important; }
[data-testid="stExpander"] svg { fill:currentColor; }

/* --- Sidebar: visible por defecto (initial_sidebar_state="expanded"
   arriba), sin ocultar sus controles nativos de plegar/reabrir. */
.zona-titulo { font-size:1rem; font-weight:700; color:var(--sanse-text); border-left:4px solid var(--sanse-red); padding-left:.7rem; margin:1.4rem 0 .8rem; }
hr { border-color: var(--sanse-border) !important; }
@media (max-width: 768px) {
    .sanse-header { flex-direction:column; align-items:flex-start; gap:.8rem; padding:.8rem 1rem; }
    .sanse-header-text h1 { font-size:1.1rem; }
    .block-container { padding-left:.8rem !important; padding-right:.8rem !important; }
    [data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
    div.stButton > button[kind="primary"] { width:100% !important; }
    .section-card { padding:.9rem 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="sanse-header">
    {_LOGO_HTML}
    <div class="sanse-header-text">
        <h1>Asistente de Generación de Memoria Anual</h1>
        <p>Departamento de Desarrollo Local y Empleo &nbsp;·&nbsp; Ayuntamiento de San Sebastián de los Reyes</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(_LOGO_HTML, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ℹ️ Cómo funciona")
    st.caption(
        "El sistema procesa tus documentos en varios pasos automáticos: "
        "lectura, interpretación de datos, y generación de la memoria final "
        "en español e inglés."
    )
    st.divider()
    st.caption("Proyecto pedagógico · Factoría F5 & Ayuntamiento Sanse · 2026")

# ---------------------------------------------------------------------------
# Zona principal — carga
# ---------------------------------------------------------------------------
col_upload, col_info = st.columns([2, 1])
with col_upload:
    st.markdown('<p class="zona-titulo">📂 Sube los documentos de entrada</p>', unsafe_allow_html=True)
    archivos_subidos = st.file_uploader(
        "Formatos admitidos: PDF, Word (.docx), Excel (.xlsx)",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        help="Informes cuatrimestrales, convenios, memorias de la agencia de colocación.",
    )
with col_info:
    st.markdown('<p class="zona-titulo">📌 Documentos esperados</p>', unsafe_allow_html=True)
    st.info(
        "- Informe financiero cuatrimestral\n"
        "- Informes de seguimiento de convenios\n"
        "- Memoria agencia de colocación\n\n"
        "_Puedes subir varios archivos a la vez._"
    )

# ---------------------------------------------------------------------------
# Botón principal
# ---------------------------------------------------------------------------
st.divider()
generar_col, _ = st.columns([1, 3])
with generar_col:
    boton_generar = st.button(
        "Generar Memoria",
        type="primary",
        disabled=not archivos_subidos,
    )

# ---------------------------------------------------------------------------
# Pipeline de generación (src_agents.graph.workflow.pipeline — 3 nodos:
# ingesta -> analista -> generador -> END)
# ---------------------------------------------------------------------------
if boton_generar:
    # 1. Guardar los archivos subidos en una carpeta temporal — el agente
    #    Ingesta espera una carpeta (extractor_generico.extraer_carpeta),
    #    no una lista de rutas de archivo sueltas.
    with st.status("📄 Preparando documentos…", expanded=True) as status_carga:
        tmp_dir = Path(tempfile.mkdtemp(prefix="sanse_streamlit_"))
        for archivo in archivos_subidos:
            (tmp_dir / archivo.name).write_bytes(archivo.read())
            st.write(f"✅ **{archivo.name}** guardado para procesar")
        status_carga.update(label=f"✅ {len(archivos_subidos)} documento(s) listo(s)", state="complete")

    # 2. Ejecutar el pipeline completo, mostrando la fase en curso a medida
    #    que cada agente del grafo (ingesta/analista/generador) termina.
    resultado = {}
    t0 = time.time()
    with st.status("⏳ Generando el informe…", expanded=True) as status_pipeline:
        try:
            for paso in pipeline.stream(
                {"uploaded_files": [str(tmp_dir)]}, stream_mode="updates"
            ):
                for nodo, salida in paso.items():
                    resultado.update(salida)
                    etiqueta = FASES_PIPELINE.get(nodo, nodo)
                    st.write(etiqueta)
                    status_pipeline.update(label=etiqueta)
            elapsed = time.time() - t0
            status_pipeline.update(
                label=f"✅ Informe generado en {elapsed:.1f}s", state="complete"
            )
        except Exception as exc:
            status_pipeline.update(label="❌ Error generando el informe", state="error")
            st.error(f"Error generando el informe: {exc}")
            st.stop()

    ruta_final = resultado.get("final_document")
    st.session_state["resultado_pipeline"] = {
        "ruta_final": ruta_final,
        "elapsed": elapsed,
    }

if "resultado_pipeline" in st.session_state:
    datos = st.session_state["resultado_pipeline"]
    ruta_final = datos["ruta_final"]
    elapsed = datos["elapsed"]

    # 3. Mostrar resultado — se lee el .docx real que dejó el generador en
    #    state["final_document"], no un draft/draft_en que ya no existe.
    st.markdown("---")
    st.markdown('<p class="zona-titulo">📝 Informe generado</p>', unsafe_allow_html=True)

    if ruta_final and Path(ruta_final).exists():
        doc_final = DocxDocument(ruta_final)

        # Separamos el documento en 3 bloques (español / inglés /
        # incidencias) usando el estilo de párrafo que ya trae el propio
        # Word ("Title", "Heading 1"...) -- no hace falta volver a
        # analizar el texto, report_generator.py ya los distingue así:
        # doc.add_heading(nivel=0) -> "Title", nivel=1 -> "Heading 1".
        bloques_es, bloques_en, bloques_incidencias = [], [], []
        zona_actual = "es"
        for p in doc_final.paragraphs:
            if not p.text.strip():
                continue
            estilo = p.style.name if p.style else ""
            if estilo == "Title" and "English" in p.text:
                zona_actual = "en"
            elif estilo == "Heading 1" and "validaci" in p.text.lower():
                zona_actual = "incidencias"
            {"es": bloques_es, "en": bloques_en, "incidencias": bloques_incidencias}[zona_actual].append((estilo, p.text))

        def _render_bloques(bloques):
            html = ""
            for estilo, texto in bloques:
                if estilo == "Title":
                    html += f'<h3 style="color:var(--sanse-red);margin-top:1.1rem;">{texto}</h3>'
                elif estilo in ("Heading 1", "Heading 2"):
                    html += f'<h4 style="margin-top:.9rem;margin-bottom:.3rem;">{texto}</h4>'
                else:
                    html += f'<p>{texto}</p>'
            return html

        st.markdown(f"""
        <div class="section-card">
            <h3>Memoria generada (español) &nbsp; <span class="badge-ok">✔ Generado en {elapsed:.1f}s</span></h3>
            {_render_bloques(bloques_es)}
        </div>
        """, unsafe_allow_html=True)

        if bloques_en:
            st.markdown(f"""
            <div class="section-card">
                {_render_bloques(bloques_en)}
            </div>
            """, unsafe_allow_html=True)

        if bloques_incidencias:
            with st.expander("⚠️ Notas de validación — revisar antes de aprobar", expanded=True):
                st.markdown(_render_bloques(bloques_incidencias), unsafe_allow_html=True)

        # 4. Descarga — un único botón, con el archivo real generado.
        #    (Se retira el botón .txt: el generador no produce esa versión.)
        st.divider()
        st.markdown('<p class="zona-titulo">💾 Descargar resultado</p>', unsafe_allow_html=True)
        docx_bytes = Path(ruta_final).read_bytes()
        col_dl1, _ = st.columns([1, 3])
        with col_dl1:
            st.download_button(
                label="📥 Descargar .docx",
                data=docx_bytes,
                file_name="memoria_anual_sanse.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
    else:
        st.error("No se ha encontrado el documento generado. Revisa la consola para más detalle.")
