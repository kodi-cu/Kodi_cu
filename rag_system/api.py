"""
API FastAPI para el sistema RAG.
Proporciona endpoints REST para indexar documentos y hacer consultas.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
import sys

# Agregar ruta al path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import RAGPipeline

# Inicializar FastAPI
app = FastAPI(
    title="RAG System API",
    description="API para sistema de pregunta-respuesta con Retrieval-Augmented Generation",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline global (se inicializa bajo demanda)
_pipeline: Optional[RAGPipeline] = None


def get_pipeline() -> RAGPipeline:
    """Obtiene o crea la instancia del pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


# Modelos Pydantic para request/response

class IndexRequest(BaseModel):
    """Request para indexar documentos."""
    directory: str = Field(..., description="Ruta al directorio con documentos")
    file_types: Optional[List[str]] = Field(
        default=None, 
        description="Tipos de archivo a indexar (ej: ['pdf', 'txt'])"
    )
    clear_existing: bool = Field(
        default=False, 
        description="Limpiar DB existente antes de indexar"
    )


class IndexResponse(BaseModel):
    """Respuesta de indexación."""
    success: bool
    documents_loaded: int
    chunks_created: int
    total_in_db: int
    message: str


class QueryRequest(BaseModel):
    """Request para consulta."""
    question: str = Field(..., description="Pregunta a realizar")
    temperature: float = Field(default=0.7, ge=0, le=1, description="Temperatura de generación")
    max_tokens: int = Field(default=512, ge=1, description="Máximo de tokens")
    include_sources: bool = Field(default=True, description="Incluir fuentes en respuesta")


class QueryResponse(BaseModel):
    """Respuesta de consulta."""
    answer: str
    sources: Optional[List[str]] = None
    scores: Optional[List[float]] = None
    context: Optional[List[str]] = None


class StatsResponse(BaseModel):
    """Respuesta de estadísticas."""
    total_documents: int
    db_path: str
    model_path: str
    embedding_model: str
    chunk_size: int
    top_k: int


# Endpoints

@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "name": "RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "Esta información",
            "GET /health": "Estado del sistema",
            "POST /index": "Indexar documentos",
            "POST /query": "Realizar consulta",
            "GET /stats": "Estadísticas"
        }
    }


@app.get("/health")
async def health_check():
    """Verifica el estado del sistema."""
    try:
        pipeline = get_pipeline()
        stats = pipeline.get_statistics()
        
        return {
            "status": "healthy",
            "vector_db_documents": stats["vector_db"]["total_documents"],
            "model_loaded": True
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest):
    """
    Indexa documentos desde un directorio.
    
    Proceso:
    1. Carga documentos (PDF, TXT, MD)
    2. Crea chunks
    3. Genera embeddings
    4. Almacena en vector DB
    """
    try:
        pipeline = get_pipeline()
        
        # Verificar que el directorio existe
        if not os.path.exists(request.directory):
            raise HTTPException(
                status_code=400, 
                detail=f"Directorio no encontrado: {request.directory}"
            )
        
        stats = pipeline.index_documents(
            directory=request.directory,
            file_types=request.file_types,
            clear_existing=request.clear_existing
        )
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return IndexResponse(
            success=True,
            documents_loaded=stats.get("documents_loaded", 0),
            chunks_created=stats.get("chunks_created", 0),
            total_in_db=stats.get("total_in_db", 0),
            message="Documentos indexados exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexando: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Realiza una consulta al sistema RAG.
    
    Proceso:
    1. Genera embedding de la pregunta
    2. Recupera contexto relevante
    3. Genera respuesta con LLM local
    """
    try:
        pipeline = get_pipeline()
        
        result = pipeline.query(
            question=request.question,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            include_sources=request.include_sources
        )
        
        return QueryResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources") if request.include_sources else None,
            scores=result.get("scores") if request.include_sources else None,
            context=result.get("context") if request.include_sources else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Retorna estadísticas del sistema."""
    try:
        pipeline = get_pipeline()
        stats = pipeline.get_statistics()
        
        return StatsResponse(
            total_documents=stats["vector_db"]["total_documents"],
            db_path=stats["vector_db"]["db_path"],
            model_path=stats["config"]["model_path"],
            embedding_model=stats["config"]["embedding_model"],
            chunk_size=stats["config"]["chunk_size"],
            top_k=stats["config"]["top_k"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo stats: {str(e)}")


@app.delete("/vector-db/clear")
async def clear_vector_db():
    """Limpia toda la base de datos vectorial."""
    try:
        pipeline = get_pipeline()
        pipeline.vector_db.clear()
        
        return {
            "success": True,
            "message": "Base de datos vectorial limpiada"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error limpiando DB: {str(e)}")


# Para ejecutar: uvicorn api:app --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
