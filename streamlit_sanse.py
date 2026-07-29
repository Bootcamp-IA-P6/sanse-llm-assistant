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
3. El botón de descarga secundario (.txt) fuerza su propio contraste, en vez
   de heredar los colores por defecto de Streamlit.
4. La generación del informe muestra un st.status con spinner y va
   actualizando la fase del pipeline en curso (ingesta, análisis, redacción,
   revisión, traducción), en vez de un spinner mudo sin detalle.
"""

import base64
import io
import os
import ssl
import sys
import tempfile
import time
from pathlib import Path

# ── Fix SSL corporativo ────────────────────────────────────────────────────
# Parcha el contexto SSL de Python a nivel global para que TODA conexión
# HTTPS (httpx, requests, aiohttp…) use certifi en vez del store corporativo.
import certifi
_CERTIFI = certifi.where()
os.environ["SSL_CERT_FILE"]      = _CERTIFI
os.environ["REQUESTS_CA_BUNDLE"] = _CERTIFI
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=_CERTIFI)
# ──────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
# Local: carga .env
load_dotenv(Path(__file__).resolve().parent / ".env")

import streamlit as st
from docx import Document as DocxDocument

# Streamlit Cloud: inyecta secrets como variables de entorno
# (en local no hay st.secrets, por lo que el bloque es silencioso)
for _k in ["GROQ_API_KEY", "GROQ_MODEL_ADAPTADOR", "GROQ_MODEL_REDACTOR", "GROQ_MODEL_MEMORIA"]:
    if _k not in os.environ:
        try:
            os.environ[_k] = st.secrets[_k]
        except Exception:
            pass
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src_agents.graph.workflow import pipeline

# ---------------------------------------------------------------------------
# Fases del pipeline (para mostrar progreso real durante la generación)
# ---------------------------------------------------------------------------
FASES_PIPELINE = {
    "ingesta": "📥 Leyendo y extrayendo los documentos…",
    "analista": "🔎 Interpretando los datos…",
    "redactor": "✍️ Redactando el informe…",
    "revisor": "🔍 Revisando y validando las cifras…",
    "adaptador": "🌐 Traduciendo el informe al inglés…",
}


# ---------------------------------------------------------------------------
# Helper — construir .docx en memoria (español + inglés + incidencias)
# ---------------------------------------------------------------------------
def _construir_docx(draft_es: str, draft_en: str, incidencias: list[str]) -> bytes:
    doc = DocxDocument()
    doc.add_heading("Memoria Anual de Actividades", level=0)
    doc.add_paragraph(
        "Departamento de Desarrollo Local y Empleo\n"
        "Ayuntamiento de San Sebastián de los Reyes\n"
        "Generado por el Asistente IA · Factoría F5"
    )
    doc.add_page_break()

    doc.add_heading("Informe (Español)", level=1)
    doc.add_paragraph(draft_es)

    if draft_en:
        doc.add_page_break()
        doc.add_heading("Report (English)", level=1)
        doc.add_paragraph(draft_en)

    if incidencias:
        doc.add_page_break()
        doc.add_heading("Notas de validación (revisión humana)", level=1)
        nota = doc.add_paragraph()
        nota.add_run(
            "Estos datos no se han encontrado literalmente en el texto generado. "
            "No bloquea el informe — queda para revisión humana:"
        ).italic = True
        for inc in incidencias:
            doc.add_paragraph(inc, style="List Bullet")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


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
#MainMenu, footer { display: none !important; }
/* Header oculto completamente — el botón de sidebar lo gestiona nuestro propio botón flotante */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
    box-shadow: none !important;
    height: 0 !important;
    min-height: 0 !important;
    overflow: visible !important;
    pointer-events: none !important;
}

.block-container {
    padding-top: 0.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}
/* Sidebar con margen superior para que no quede tapado por nuestro botón */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 3.2rem !important;
}
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
[data-testid="stFileUploaderDropzone"] button { background:var(--sanse-red) !important; color:white !important; border:none !important; border-radius:var(--radius) !important; font-weight:600 !important; font-size:0 !important; padding:.5rem 1.2rem !important; }
[data-testid="stFileUploaderDropzone"] button { gap:.9rem !important; }
[data-testid="stFileUploaderDropzone"] button::before { content:"Seleccionar archivos"; font-size:.85rem; font-weight:600; color:white; margin-right:.9rem; }
[data-testid="stFileUploaderDropzone"] button:hover { background:var(--sanse-red-dk) !important; }

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

.zona-titulo { font-size:1rem; font-weight:700; color:var(--sanse-text); border-left:4px solid var(--sanse-red); padding-left:.7rem; margin:1.4rem 0 .8rem; }
hr { border-color: var(--sanse-border) !important; }
@media (max-width: 768px) {
    .sanse-header { flex-direction:column; align-items:flex-start; gap:.6rem; padding:.7rem .9rem .7rem 3.2rem; }
    .sanse-header img { height:40px !important; }
    .sanse-header-text h1 { font-size:1rem; }
    .sanse-header-text p { font-size:.75rem; }
    .block-container { padding-left:.5rem !important; padding-right:.5rem !important; padding-top:0.5rem !important; }
    [data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
    div.stButton > button[kind="primary"] { width:100% !important; font-size:.85rem !important; padding:.6rem 1rem !important; }
    div[data-testid="stDownloadButton"] button { width:100% !important; }
    .section-card { padding:.7rem .8rem; }
    .section-card h3 { font-size:.9rem; }
    [data-testid="stFileUploaderDropzone"] { padding:.7rem !important; }
    /* Columnas de descarga: apilar en móvil */
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: .5rem !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: 100% !important; }
    /* Status cards */
    [data-testid="stStatusWidget"] { font-size:.82rem; }
    /* Expander */
    [data-testid="stExpander"] summary { font-size:.85rem; }
    /* Zona titulo */
    .zona-titulo { font-size:.9rem; }
}
@media (max-width: 480px) {
    .sanse-header-text h1 { font-size:.9rem; }
    .sanse-header img { height:34px !important; }
    div.stButton > button[kind="primary"] { font-size:.8rem !important; padding:.55rem .8rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Botón flotante PROPIO para abrir/cerrar sidebar — siempre visible
# No depende del botón nativo de Streamlit (que puede desaparecer).
# Usa JS para detectar el estado real del sidebar en el DOM y hacer click
# en el botón nativo, o bien colapsar/expandir directamente el elemento.
# ---------------------------------------------------------------------------
st.markdown("""
<button id="sanse-sidebar-toggle"
  onclick="toggleSanseSidebar()"
  title="Abrir / cerrar panel lateral"
  aria-label="Abrir o cerrar el panel lateral">
  <svg id="sanse-icon-open"  width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  <svg id="sanse-icon-close" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:none"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
</button>
<style>
#sanse-sidebar-toggle {
  position: fixed;
  top: 0.65rem;
  left: 0.65rem;
  z-index: 99999;
  background: #A3132F;
  border: none;
  border-radius: 7px;
  width: 2.4rem;
  height: 2.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(163,19,47,.45);
  transition: background .18s, box-shadow .18s, transform .12s;
  padding: 0;
}
#sanse-sidebar-toggle:hover {
  background: #7D0E22;
  box-shadow: 0 4px 16px rgba(163,19,47,.55);
  transform: scale(1.07);
}
#sanse-sidebar-toggle:active { transform: scale(.96); }
</style>
<script>
(function() {
  function isSidebarOpen() {
    var sb = window.parent.document.querySelector('[data-testid="stSidebar"]');
    if (!sb) return false;
    // Streamlit marca el sidebar colapsado con aria-expanded="false" o con una clase/atributo
    var collapsed = sb.getAttribute('aria-expanded');
    if (collapsed !== null) return collapsed !== 'false';
    // Fallback: comprobar si tiene ancho visible
    return sb.offsetWidth > 60;
  }

  function clickNativeToggle() {
    var doc = window.parent.document;
    // Intentar todos los selectores conocidos del botón nativo
    var selectors = [
      '[data-testid="collapsedControl"]',
      '[data-testid="stSidebarCollapsedControl"]',
      'button[kind="header"]',
      'header button',
      '[data-testid="stHeader"] button',
    ];
    for (var i = 0; i < selectors.length; i++) {
      var btn = doc.querySelector(selectors[i]);
      if (btn) { btn.click(); return true; }
    }
    return false;
  }

  function forceSidebarToggle() {
    var doc = window.parent.document;
    var sb = doc.querySelector('[data-testid="stSidebar"]');
    if (!sb) return;
    if (isSidebarOpen()) {
      sb.style.display = 'none';
      sb.setAttribute('aria-expanded', 'false');
    } else {
      sb.style.display = '';
      sb.removeAttribute('aria-expanded');
      // Forzar re-render
      sb.style.transform = 'translateX(0)';
    }
  }

  window.toggleSanseSidebar = function() {
    var open = isSidebarOpen();
    // Primero intentar el botón nativo de Streamlit
    var clicked = clickNativeToggle();
    // Si no encontramos botón nativo, forzar directamente
    if (!clicked) forceSidebarToggle();
    // Actualizar iconos del botón propio
    setTimeout(function() {
      var nowOpen = isSidebarOpen();
      document.getElementById('sanse-icon-open').style.display  = nowOpen ? 'none' : '';
      document.getElementById('sanse-icon-close').style.display = nowOpen ? ''     : 'none';
    }, 200);
  };

  // Sincronizar icono al cargar y al cambiar tamaño
  function syncIcon() {
    var open = isSidebarOpen();
    var btnOpen  = document.getElementById('sanse-icon-open');
    var btnClose = document.getElementById('sanse-icon-close');
    if (btnOpen && btnClose) {
      btnOpen.style.display  = open ? 'none' : '';
      btnClose.style.display = open ? ''     : 'none';
    }
  }
  // Esperar a que el DOM de Streamlit esté listo
  var tries = 0;
  var interval = setInterval(function() {
    syncIcon();
    tries++;
    if (tries > 20) clearInterval(interval);
  }, 300);
  window.addEventListener('resize', syncIcon);
})();
</script>
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
# Sidebar — sin selectores de modelo/temperatura/secciones (no aplican al
# pipeline nuevo: el modelo es una decisión interna, no del usuario, y el
# pipeline siempre genera el informe completo en español + inglés).
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(_LOGO_HTML, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ℹ️ Cómo funciona")
    st.caption(
        "El sistema procesa tus documentos en varios pasos automáticos: "
        "lectura, interpretación de datos, redacción, revisión y traducción. "
        "El resultado se genera en español e inglés."
    )
    st.divider()

    # ── API Key ───────────────────────────────────────────────────────────
    st.markdown("### 🔑 API Key de Groq")
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] input[type="password"] {
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] input:-webkit-autofill,
    section[data-testid="stSidebar"] input:-webkit-autofill:focus {
        -webkit-box-shadow: 0 0 0px 1000px #FFFFFF inset !important;
        -webkit-text-fill-color: #1A1A1A !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ¿La clave viene de st.secrets (Streamlit Cloud)?
    _key_from_secrets = False
    try:
        if st.secrets.get("GROQ_API_KEY"):
            os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
            _key_from_secrets = True
    except Exception:
        pass

    if _key_from_secrets:
        # Streamlit Cloud: clave configurada en el dashboard, no mostrar nada
        st.success("✅ Clave configurada.")
        if st.checkbox("Usar una clave diferente", key="override_key"):
            _override = st.text_input(
                "Tu clave de Groq:",
                type="password",
                placeholder="gsk_...",
                help="Sobreescribe la clave por defecto. Obtenla en console.groq.com",
            )
            if _override:
                os.environ["GROQ_API_KEY"] = _override
    elif os.environ.get("GROQ_API_KEY"):
        # Local con .env: clave cargada, no mostrar el valor
        st.success("✅ Clave cargada desde configuración.")
    else:
        # Docker sin --env-file, o cualquier entorno sin clave: pedir al usuario
        _user_api_key = st.text_input(
            "Introduce tu clave de Groq:",
            type="password",
            placeholder="gsk_...",
            help="Obtenla en console.groq.com · Necesaria para generar el informe.",
        )
        if _user_api_key:
            os.environ["GROQ_API_KEY"] = _user_api_key
        else:
            st.warning("Introduce tu API Key para poder generar el informe.")
    # ─────────────────────────────────────────────────────────────────────

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
        disabled=not archivos_subidos or not os.environ.get("GROQ_API_KEY"),
    )

# ---------------------------------------------------------------------------
# Pipeline de generación (nuevo: src_agents.graph.workflow.pipeline)
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
    #    que cada agente del grafo (ingesta/analista/redactor/revisor/
    #    adaptador) termina su trabajo — en vez de un spinner mudo.
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

    draft_es = resultado.get("draft", "")
    draft_en = resultado.get("draft_en", "")
    review = resultado.get("review")
    incidencias = review.incidencias if review else []

    st.session_state["resultado_pipeline"] = {
        "draft_es": draft_es,
        "draft_en": draft_en,
        "incidencias": incidencias,
        "elapsed": elapsed,
    }

if "resultado_pipeline" in st.session_state:
    datos = st.session_state["resultado_pipeline"]
    draft_es = datos["draft_es"]
    draft_en = datos["draft_en"]
    incidencias = datos["incidencias"]
    elapsed = datos["elapsed"]

    # 3. Mostrar resultado
    st.markdown("---")
    st.markdown('<p class="zona-titulo">📝 Informe generado</p>', unsafe_allow_html=True)

    badge = (
        '<span class="badge-ok">✔ Validado</span>' if not incidencias
        else f'<span class="badge-warn">⚠ {len(incidencias)} incidencia(s)</span>'
    )
    st.markdown(f"""
    <div class="section-card">
        <h3>Informe (Español) &nbsp; {badge}</h3>
        <p style="color:#555;font-size:.82rem">⏱ {elapsed:.1f}s</p>
        <p>{draft_es.replace(chr(10), "<br>")}</p>
    </div>
    """, unsafe_allow_html=True)

    if draft_en:
        st.markdown(f"""
        <div class="section-card">
            <h3>Report (English)</h3>
            <p>{draft_en.replace(chr(10), "<br>")}</p>
        </div>
        """, unsafe_allow_html=True)

    if incidencias:
        with st.expander(f"⚠️ {len(incidencias)} incidencia(s) para revisión humana"):
            for inc in incidencias:
                st.warning(inc)

    # 4. Descarga
    st.divider()
    st.markdown('<p class="zona-titulo">💾 Descargar resultado</p>', unsafe_allow_html=True)
    docx_buffer = _construir_docx(draft_es, draft_en, incidencias)
    col_dl1, col_dl2, _ = st.columns([1, 1, 2])
    with col_dl1:
        st.download_button(
            label="📥 Descargar .docx",
            data=docx_buffer,
            file_name="memoria_anual_sanse.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
    with col_dl2:
        texto_plano = f"INFORME (ESPAÑOL)\n\n{draft_es}\n\n\nREPORT (ENGLISH)\n\n{draft_en}"
        st.download_button(
            label="📥 Descargar .txt",
            data=texto_plano.encode("utf-8"),
            file_name="memoria_anual_sanse.txt",
            mime="text/plain",
        )
