# test_env.py
import sys
import langchain
import chromadb
import ollama
import pandas as pd
import docx
import PyPDF2
import yaml

print("✅ Entorno configurado correctamente")
print(f"🐍 Python: {sys.version}")
print(f"📦 LangChain: {langchain.__version__}")
print(f"📦 ChromaDB: {chromadb.__version__}")

# Verificar que Ollama está funcionando
try:
    models = ollama.list()
    print(f"🦙 Ollama: OK ({len(models['models'])} modelos descargados)")
except Exception as e:
    print(f"❌ Error con Ollama: {e}")