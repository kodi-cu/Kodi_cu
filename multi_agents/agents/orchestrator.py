"""Agente Orchestrator - Coordinador central con cache de intenciones"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import re
from collections import OrderedDict

# Importar agentes
from .file_finder import FileFinderAgent
from .document_reader import DocumentReaderAgent
from .document_classifier import DocumentClassifierAgent
from .document_analyzer import DocumentAnalyzerAgent
from .document_manager import DocumentManagerAgent


class AgentOrchestrator:
    """
    Orquestador central que coordina todos los agentes.
    OPTIMIZACIÓN: Cache de intenciones y patrones regex para evitar
    llamadas al LLM en consultas comunes.
    """
    
    # Patrones regex para intenciones comunes (evitan llamar al LLM)
    INTENTION_PATTERNS = {
        'search_pdf': [
            r'busc.*pdf', r'find.*pdf', r'buscar.*documento', r'look.*pdf',
            r'dónde.*pdf', r'where.*pdf', r'mostrar.*pdf', r'show.*pdf'
        ],
        'search_odt': [
            r'busc.*odt', r'buscar.*writer', r'find.*odt', r'documento.*odt'
        ],
        'search_all': [
            r'busc.*todo', r'list.*file', r'mostrar.*archivo', r'listar.*documento',
            r'qué.*archivo', r'what.*file', r'todos.*documento'
        ],
        'read_document': [
            r'leer.*documento', r'read.*file', r'abrir.*archivo', r'ver.*contenido',
            r'mostrar.*contenido', r'what.*inside', r'qué.*dice'
        ],
        'classify': [
            r'clasific.*documento', r'classify.*file', r'categor.*documento',
            r'tipo.*archivo', r'qué.*tipo.*documento'
        ],
        'summarize': [
            r'resum.*documento', r'summariz.*file', r'puntos.*clave',
            r'key.*point', r'idea.*principal', r'de.*qué.*trata'
        ],
        'analyze': [
            r'analiz.*documento', r'analyz.*file', r'estudio.*documento',
            r'examin.*archivo', r'revis.*documento'
        ],
        'extract_info': [
            r'extrae.*información', r'extract.*info', r'obten.*dato',
            r'get.*information', r'quién.*cuándo.*dónde'
        ],
        'create_document': [
            r'crear.*documento', r'create.*file', r'generar.*archivo',
            r'make.*document', r'escribir.*nuevo'
        ],
        'organize': [
            r'organiz.*archivo', r'organize.*file', r'ordenar.*documento',
            r'sort.*file', r'clasificar.*por.*tipo'
        ]
    }
    
    def __init__(
        self,
        llm_client=None,
        vision_client=None,
        search_paths: List[str] = None,
        output_dir: str = "./output",
        model_name: str = "local-model",
        vision_model_name: str = "local-vision-model"
    ):
        """
        Inicializa el orquestador con todos los agentes.
        
        Args:
            llm_client: Cliente LLM para análisis complejos
            vision_client: Cliente para modelos de visión
            search_paths: Directorios de búsqueda
            output_dir: Directorio para salida
            model_name: Nombre del modelo base
            vision_model_name: Nombre del modelo de visión
        """
        self.llm_client = llm_client
        self.vision_client = vision_client
        self.model_name = model_name
        self.vision_model_name = vision_model_name
        
        # Inicializar agentes
        self.file_finder = FileFinderAgent(search_paths=search_paths)
        self.document_reader = DocumentReaderAgent(
            vision_client=vision_client,
            vision_model=vision_model_name
        )
        self.document_classifier = DocumentClassifierAgent(
            llm_client=llm_client,
            model_name=model_name
        )
        self.document_analyzer = DocumentAnalyzerAgent(
            llm_client=llm_client,
            model_name=model_name,
            vision_client=vision_client,
            vision_model=vision_model_name
        )
        self.document_manager = DocumentManagerAgent(output_dir=output_dir)
        
        # Cache LRU de intenciones (máximo 100 entradas)
        self.intention_cache = OrderedDict()
        self.max_cache_size = 100
    
    def detect_intention(self, query: str) -> str:
        """
        Detecta la intención de la consulta SIN usar LLM.
        Usa patrones regex predefinidos para máxima eficiencia.
        
        Args:
            query: Consulta del usuario
        
        Returns:
            Intención detectada
        """
        query_lower = query.lower()
        
        # Verificar cache primero
        if query in self.intention_cache:
            # Mover al final (más reciente)
            self.intention_cache.move_to_end(query)
            return self.intention_cache[query]
        
        # Buscar patrones regex
        for intention, patterns in self.INTENTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    # Guardar en cache
                    self._add_to_cache(query, intention)
                    return intention
        
        # Intención por defecto
        return 'general_query'
    
    def _add_to_cache(self, query: str, intention: str):
        """Añade una intención al cache LRU"""
        if len(self.intention_cache) >= self.max_cache_size:
            # Eliminar la más antigua
            self.intention_cache.popitem(last=False)
        self.intention_cache[query] = intention
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una consulta coordinando los agentes apropiados.
        
        Args:
            query: Consulta del usuario
            **kwargs: Argumentos adicionales
        
        Returns:
            Resultado de la ejecución
        """
        # Detectar intención (sin LLM)
        intention = self.detect_intention(query)
        
        # Ejecutar acción basada en intención
        action_map = {
            'search_pdf': self._handle_search,
            'search_odt': self._handle_search,
            'search_all': self._handle_search,
            'read_document': self._handle_read,
            'classify': self._handle_classify,
            'summarize': self._handle_summarize,
            'analyze': self._handle_analyze,
            'extract_info': self._handle_extract,
            'create_document': self._handle_create,
            'organize': self._handle_organize,
            'general_query': self._handle_general
        }
        
        handler = action_map.get(intention, self._handle_general)
        
        try:
            result = handler(query, **kwargs)
            result['intention'] = intention
            result['llm_calls_saved'] = self._estimate_llm_savings()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'intention': intention
            }
    
    def _handle_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja búsquedas de archivos"""
        files = self.file_finder.search(query)
        
        return {
            'success': True,
            'action': 'search',
            'files_found': len(files),
            'files': files[:20],  # Limitar resultados
            'message': f"Se encontraron {len(files)} archivos"
        }
    
    def _handle_read(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja lectura de documentos"""
        file_path = kwargs.get('file_path')
        
        if not file_path:
            # Intentar encontrar el archivo mencionado
            files = self.file_finder.search(query)
            if files:
                file_path = files[0]['path']
            else:
                return {'success': False, 'error': 'No se encontró el archivo'}
        
        result = self.document_reader.read(file_path)
        
        return {
            'success': result.get('success', False),
            'action': 'read',
            'content': result.get('content', '')[:2000],  # Preview
            'metadata': result.get('metadata', {}),
            'full_content_available': True
        }
    
    def _handle_classify(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja clasificación de documentos"""
        file_path = kwargs.get('file_path')
        
        if not file_path:
            files = self.file_finder.search(query)
            if files:
                file_path = files[0]['path']
            else:
                return {'success': False, 'error': 'No se encontró el archivo'}
        
        # Leer documento
        doc_result = self.document_reader.read(file_path)
        content = doc_result.get('content', '')
        
        # Clasificar (optimizado: usa heurística primero)
        classification = self.document_classifier.classify(content, file_path)
        
        return {
            'success': True,
            'action': 'classify',
            'category': classification.get('category'),
            'confidence': classification.get('confidence'),
            'method': classification.get('method'),
            'llm_used': classification.get('llm_used', False)
        }
    
    def _handle_summarize(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja resumen de documentos"""
        file_path = kwargs.get('file_path')
        
        if not file_path:
            files = self.file_finder.search(query)
            if files:
                file_path = files[0]['path']
            else:
                return {'success': False, 'error': 'No se encontró el archivo'}
        
        doc_result = self.document_reader.read(file_path)
        content = doc_result.get('content', '')
        
        summary = self.document_analyzer.summarize(content)
        
        return {
            'success': summary.get('success', False),
            'action': 'summarize',
            'summary': summary.get('summary', ''),
            'compression_ratio': summary.get('compression_ratio')
        }
    
    def _handle_analyze(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja análisis profundo"""
        file_path = kwargs.get('file_path')
        
        if not file_path:
            files = self.file_finder.search(query)
            if files:
                file_path = files[0]['path']
            else:
                return {'success': False, 'error': 'No se encontró el archivo'}
        
        doc_result = self.document_reader.read(file_path)
        content = doc_result.get('content', '')
        
        # Análisis múltiple
        summary = self.document_analyzer.summarize(content, 'short')
        key_points = self.document_analyzer.extract_key_points(content)
        entities = self.document_analyzer.extract_entities(content)
        
        return {
            'success': True,
            'action': 'analyze',
            'summary': summary.get('summary', ''),
            'key_points': key_points.get('key_points', []),
            'entities': entities.get('entities', {})
        }
    
    def _handle_extract(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja extracción de información específica"""
        file_path = kwargs.get('file_path')
        question = kwargs.get('question', query)
        
        if not file_path:
            files = self.file_finder.search(query)
            if files:
                file_path = files[0]['path']
        
        if not file_path:
            return {'success': False, 'error': 'No se encontró el archivo'}
        
        doc_result = self.document_reader.read(file_path)
        content = doc_result.get('content', '')
        
        answer = self.document_analyzer.answer_question(content, question)
        
        return {
            'success': answer.get('success', False),
            'action': 'extract',
            'question': answer.get('question'),
            'answer': answer.get('answer', '')
        }
    
    def _handle_create(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja creación de documentos"""
        content = kwargs.get('content', query)
        filename = kwargs.get('filename', 'documento_nuevo')
        format = kwargs.get('format', 'txt')
        
        result = self.document_manager.create_document(content, filename, format)
        
        return {
            'success': result.get('success', False),
            'action': 'create',
            'path': result.get('path'),
            'filename': result.get('filename')
        }
    
    def _handle_organize(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja organización de archivos"""
        source_dir = kwargs.get('directory', './documents')
        
        result = self.document_manager.organize_by_type(source_dir)
        
        return {
            'success': result.get('success', False),
            'action': 'organize',
            'moved_count': result.get('moved_count', 0),
            'details': result
        }
    
    def _handle_general(self, query: str, **kwargs) -> Dict[str, Any]:
        """Maneja consultas generales sin intención clara"""
        # Búsqueda genérica como fallback
        files = self.file_finder.search(query)
        
        response = {
            'success': True,
            'action': 'general',
            'message': 'Consulta general procesada',
            'suggestion': 'Especifica si quieres buscar, leer, clasificar o analizar documentos'
        }
        
        if files:
            response['files_found'] = len(files)
            response['sample_files'] = files[:5]
        
        return response
    
    def _estimate_llm_savings(self) -> Dict[str, Any]:
        """Estima cuántas llamadas al LLM se ahorraron gracias al cache"""
        total_cached = len(self.intention_cache)
        
        return {
            'cached_intentions': total_cached,
            'estimated_savings_percent': min(80, total_cached * 5),  # Hasta 80%
            'cache_efficiency': 'high' if total_cached > 20 else 'medium' if total_cached > 5 else 'low'
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del orquestador y agentes"""
        return {
            'cache_size': len(self.intention_cache),
            'max_cache_size': self.max_cache_size,
            'file_finder': self.file_finder.get_stats(),
            'supported_actions': list(self.INTENTION_PATTERNS.keys())
        }
    
    def clear_cache(self):
        """Limpia el cache de intenciones"""
        self.intention_cache.clear()
