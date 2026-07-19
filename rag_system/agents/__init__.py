"""
Sistema de Agentes IA para Gestión Documental

Este módulo implementa múltiples agentes especializados para:
- Analizar documentos (PDF, ODT, ODP, ODG)
- Clasificar por tipo y contenido
- Buscar en directorios
- Leer y extraer información
- Modificar y crear nuevos documentos

Configuración local con llama.cpp via OpenAI-compatible API
"""

from .file_finder import FileFinderAgent
from .document_reader import DocumentReaderAgent
from .document_classifier import DocumentClassifierAgent
from .document_analyzer import DocumentAnalyzerAgent
from .document_manager import DocumentManagerAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    'FileFinderAgent',
    'DocumentReaderAgent',
    'DocumentClassifierAgent',
    'DocumentAnalyzerAgent',
    'DocumentManagerAgent',
    'AgentOrchestrator'
]
