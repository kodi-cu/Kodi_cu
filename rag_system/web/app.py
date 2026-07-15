"""
Web Server para el sistema RAG.
Integra una interfaz web con la API existente.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys

# Agregar ruta al path para importar api
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import app as api_app

# Crear nueva aplicación FastAPI que incluye la API y la web
web_app = FastAPI(
    title="RAG System Web",
    description="Interfaz web para el sistema RAG",
    version="1.0.0"
)

# Obtener rutas del directorio actual
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Montar archivos estáticos
web_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configurar templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Incluir los endpoints de la API
for route in api_app.routes:
    web_app.router.routes.append(route)


@web_app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Sirve la página principal de la interfaz web."""
    return templates.TemplateResponse("index.html", {"request": request})


@web_app.get("/health")
async def health_check():
    """Verifica el estado del sistema web."""
    return {
        "status": "healthy",
        "web_server": "running",
        "api": "available"
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Iniciando RAG System Web Server")
    print("="*60)
    print("📍 Accede a: http://localhost:8080")
    print("📍 API Docs: http://localhost:8080/docs")
    print("="*60 + "\n")
    uvicorn.run(web_app, host="0.0.0.0", port=8080)
