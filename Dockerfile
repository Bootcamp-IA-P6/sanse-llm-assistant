# ── Imagen base ────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Variables de entorno básicas
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Directorio de trabajo
WORKDIR /app

# Dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer puerto de Streamlit
EXPOSE 8507

# Comando de arranque
CMD ["python", "-m", "streamlit", "run", "streamlit_sanse.py", \
     "--server.port=8507", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
