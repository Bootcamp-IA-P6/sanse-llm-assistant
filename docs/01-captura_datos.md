# Fase 1 — Captura de datos

> Documento de referencia para la Fase 1 del proyecto. Ver `README.md` en la raíz para la visión general.

## Objetivo de la fase

Construir el componente que lee los documentos de entrada (PDF, Word, Excel) y los convierte en texto normalizado, listo para que el pipeline RAG (Fase 2) pueda trabajar con él, sin importar el formato original.

---

## Checklist de tareas

| # | Tarea | Estado | Responsable principal |
|---|---|---|---|
| 1.1 | Extracción de texto y tablas de PDF | ✅ Hecho | Data Engineer (RAG) |
| 1.2 | Extracción de texto de Word, preservando jerarquía de títulos | ✅ Hecho | Data Engineer (RAG) |
| 1.3 | Extracción de datos de Excel | ✅ Hecho | Data Engineer (RAG) |
| 1.4 | Unificación en un formato común (`DocumentoCargado`) | ✅ Hecho | Data Engineer (RAG) |
| 1.5 | Clasificación automática del tipo de documento por nombre de archivo | ✅ Hecho (heurística simple) | Data Engineer (RAG) |
| 1.6 | Pruebas del loader con los 3 documentos ficticios | ✅ Hecho | Data Engineer (RAG) + Product Owner (validación de contenido) |
| 1.7 | Documentar limitaciones conocidas del loader | ✅ Hecho (ver más abajo) | Product Owner |

---

## Qué se ha construido: `loader.py`

Ubicación: `src/rag/loader.py`

### Decisiones técnicas clave

- **`pdfplumber` en vez de `PyPDF2`** para la extracción de PDF: permite detectar y extraer tablas de forma estructurada, algo esencial para el informe financiero, donde perder la relación entre una cifra y su concepto haría inútil el dato para el LLM.
- **Exclusión del área de las tablas del texto narrativo**: se detecta primero dónde están las tablas y se extrae el texto narrativo *fuera* de esas zonas, para evitar que el mismo dato aparezca duplicado (una vez "aplanado" en el texto corrido, otra vez en formato estructurado). Esto ahorra contexto, algo relevante al trabajar con un modelo pequeño (Llama 3.2 3B) con ventana de contexto limitada.
- **Formato intermedio propio (`DocumentoCargado`)**, en vez de convertir directamente al formato `Document` de LangChain: da control total sobre qué metadata se guarda (fuente, tipo, formato, fecha de carga) antes de acoplarse a una librería externa. La conversión a `Document` de LangChain se hará en la Fase 2, cuando se construya el splitter.
- **Clasificación del tipo de documento por nombre de archivo** (`financiero`, `convenio`, `agencia_colocacion`): heurística simple, suficiente para el MVP. Es una limitación conocida (ver más abajo).

### Formatos soportados

| Formato | Librería | Función |
|---|---|---|
| `.pdf` | `pdfplumber` | `cargar_pdf()` |
| `.docx` | `python-docx` | `cargar_docx()` |
| `.xlsx` | `pandas` / `openpyxl` | `cargar_xlsx()` |

### Punto de entrada

```python
from src.rag.loader import cargar_carpeta
from pathlib import Path

documentos = cargar_carpeta(Path("data/raw"))
```

Devuelve una lista de objetos `DocumentoCargado`, cada uno con: `texto`, `fuente`, `tipo`, `formato`, `fecha_carga`.

---

## Limitaciones conocidas

- **Clasificación por nombre de archivo**: si el Ayuntamiento nombra los archivos de forma distinta a lo esperado (ej. sin la palabra "financiero" en el nombre), el documento se clasificará como `otro`. Cuando lleguen datos reales, revisar si esta heurística sigue siendo válida o si conviene que el usuario clasifique el documento manualmente desde la interfaz (Fase 5).
- **Extracción de tablas complejas en PDF**: `pdfplumber` funciona bien con tablas simples y bien definidas (como las de los datos ficticios). Si los informes reales del Ayuntamiento tienen tablas anidadas, fusionadas o con formato irregular, puede requerir ajustes.
- **No hay manejo de PDFs escaneados (imágenes)**: si los informes financieros reales llegan como PDF escaneado sin texto seleccionable, `pdfplumber` no podrá extraer nada y haría falta OCR (fuera de alcance del MVP salvo que se confirme que es necesario).

---

## Entregables de la fase

- [x] `src/rag/loader.py` funcionando y probado con los 3 documentos ficticios
- [x] Documentación de limitaciones conocidas
- [ ] Prueba del loader con al menos un documento real del Ayuntamiento (pendiente de recibir datos, ver Fase 0)

## Próxima fase

**Fase 2 — Validación del modelo**: probar la capacidad de generación de Llama 3.2 3B antes de construir el RAG completo.