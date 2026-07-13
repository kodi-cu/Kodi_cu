"""
Configuración del sistema RAG.
Carga parámetros desde archivo .env o valores por defecto.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Cargar variables de entorno
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / "config" / ".env")


class Config:
    """Clase singleton para configuración del sistema RAG."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Model Configuration
        self.model_path: str = os.getenv(
            "MODEL_PATH", 
            str(BASE_DIR / "models" / "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
        )
        self.embedding_model: str = os.getenv(
            "EMBEDDING_MODEL", 
            "all-MiniLM-L6-v2"
        )
        
        # Vector Database
        self.vector_db_path: str = os.getenv(
            "VECTOR_DB_PATH",
            str(BASE_DIR / "vector_store" / "chroma_db")
        )
        
        # Document Processing
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
        
        # Retrieval
        self.top_k: int = int(os.getenv("TOP_K", "4"))
        
        # LLM Generation
        self.temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "512"))
        self.context_window: int = int(os.getenv("CONTEXT_WINDOW", "4096"))
        
        # Hardware Optimization
        self.n_gpu_layers: int = int(os.getenv("N_GPU_LAYERS", "0"))
        self.n_threads: int = int(os.getenv("N_THREADS", "4"))
        
        # Cache
        self.embedding_cache_path: str = os.getenv(
            "EMBEDDING_CACHE_PATH",
            str(BASE_DIR / "cache" / "embeddings_cache.pkl")
        )
        
        # Create necessary directories
        self._create_directories()
        
        self._initialized = True
    
    def _create_directories(self):
        """Crea los directorios necesarios si no existen."""
        directories = [
            BASE_DIR / "models",
            BASE_DIR / "vector_store",
            BASE_DIR / "docs",
            BASE_DIR / "cache",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Valida que la configuración sea correcta."""
        # Verificar que el modelo exista (si se especificó ruta)
        if self.model_path and not Path(self.model_path).exists():
            print(f"Advertencia: El modelo no existe en {self.model_path}")
            print("Debes descargar el modelo GGUF antes de usar el sistema.")
            return False
        return True
    
    def __repr__(self) -> str:
        return (
            f"Config(\n"
            f"  model_path={self.model_path},\n"
            f"  embedding_model={self.embedding_model},\n"
            f"  chunk_size={self.chunk_size},\n"
            f"  top_k={self.top_k},\n"
            f"  n_gpu_layers={self.n_gpu_layers},\n"
            f"  n_threads={self.n_threads}\n"
            f")"
        )


# Instancia global de configuración
config = Config()
