"""
test_groq.py — Verifica que la clave de Groq funciona correctamente.
Ejecutar desde la raíz del proyecto: uv run python test_groq.py
"""
import os
import sys
from pathlib import Path

# Fix SSL corporativo
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

key = os.getenv("GROQ_API_KEY", "")
if not key or key.startswith("gsk_xxx"):
    print("❌ GROQ_API_KEY no configurada en .env")
    sys.exit(1)

print(f"🔑 Clave cargada: {key[:15]}...")

try:
    import certifi
    import httpx
    from groq import Groq
    http_client = httpx.Client(verify=certifi.where(), timeout=15)
    client = Groq(api_key=key, http_client=http_client)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Responde solo con: OK"}],
        max_tokens=5,
    )
    print(f"✅ Groq conectado: {resp.choices[0].message.content.strip()}")
except Exception as e:
    print(f"❌ Error conectando con Groq: {e}")
    sys.exit(1)

print("\n✅ Todo OK — puedes lanzar la app.")
