"""
Configuración del sistema PDF Agent
"""
import os
from pathlib import Path
from typing import Optional

# Configuración del servidor llama.cpp
LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://localhost:8081/v1")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY", "sk-no-key-required")
MODEL_NAME = os.getenv("MODEL_NAME", "InternScience/Agents-A1-4B-Q4_K_M-GGUF")

# Configuración de la interfaz web
UI_HOST = os.getenv("UI_HOST", "0.0.0.0")
UI_PORT = int(os.getenv("UI_PORT", "8501"))
UI_THEME = os.getenv("UI_THEME", "light")

# Límites de procesamiento
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "8000"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))

# Timeout para comandos
COMMAND_TIMEOUT_SECONDS = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "10"))

# Directorios
BASE_DIR = Path(__file__).parent.parent
PDF_UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
for directory in [PDF_UPLOAD_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Comandos peligrosos bloqueados
DANGEROUS_COMMANDS = ["rm", "sudo", "dd", "chmod", ">", ">>"]

# Estados válidos para TODO
TODO_STATUSES = ["pending", "in_progress", "completed"]
