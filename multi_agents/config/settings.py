"""Configuración del sistema multi-agente"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuración del cliente LLM local"""
    base_url: str = "http://localhost:8081/v1"
    api_key: str = "sk-no-key-required"
    model_name: str = "local-model"
    vision_model_name: str = "local-vision-model"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 120


@dataclass
class CacheConfig:
    """Configuración del cache de intenciones"""
    max_size: int = 100
    ttl_seconds: int = 300


@dataclass
class ClassifierConfig:
    """Configuración del clasificador de documentos"""
    heuristic_threshold: float = 0.7  # Umbral de confianza para usar LLM
    categories: list = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = [
                "legal", "financiero", "tecnico", "administrativo",
                "comercial", "rrhh", "marketing", "otros"
            ]


@dataclass
class SystemConfig:
    """Configuración principal del sistema"""
    llm: LLMConfig = None
    cache: CacheConfig = None
    classifier: ClassifierConfig = None
    search_paths: list = None
    output_dir: str = "./output"
    
    def __post_init__(self):
        if self.llm is None:
            self.llm = LLMConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.classifier is None:
            self.classifier = ClassifierConfig()
        if self.search_paths is None:
            self.search_paths = ["./documents", "./"]


# Configuración por defecto
DEFAULT_CONFIG = SystemConfig()
