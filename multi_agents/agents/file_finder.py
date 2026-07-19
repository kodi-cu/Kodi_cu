"""Agente FileFinder - Búsqueda inteligente de archivos"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from tools.file_utils import find_files, get_file_info, supported_extensions


class FileFinderAgent:
    """
    Agente especializado en búsqueda de archivos en el sistema.
    Optimizado para evitar llamadas al LLM usando patrones predefinidos.
    """
    
    # Cache de búsquedas recientes (intenciones comunes)
    _search_cache: Dict[str, List[Path]] = {}
    
    # Patrones predefinidos para intenciones comunes
    INTENTION_PATTERNS = {
        'pdf': [r'pdf', r'portable document'],
        'odt': [r'odt', r'open.*document', r'writer'],
        'odp': [r'odp', r'presentation', r'diapositiva'],
        'odg': [r'odg', r'dibujo', r'gráfico'],
        'excel': [r'xls', r'spreadsheet', r'hoja.*cálculo'],
        'word': [r'doc', r'word'],
        'powerpoint': [r'ppt', r'powerpoint'],
        'image': [r'png', r'jpg', r'jpeg', r'gif', r'image', r'imagen'],
        'recent': [r'reciente', r'último', r'nuevo'],
        'all': [r'todo', r'all', r'list']
    }
    
    def __init__(self, search_paths: List[str] = None):
        """
        Inicializa el agente buscador.
        
        Args:
            search_paths: Lista de directorios donde buscar
        """
        self.search_paths = search_paths or ["./documents", "./"]
    
    def detect_intention(self, query: str) -> Optional[str]:
        """
        Detecta la intención de búsqueda sin usar LLM.
        
        Args:
            query: Consulta del usuario
        
        Returns:
            Tipo de intención detectada o None
        """
        query_lower = query.lower()
        
        for intention, patterns in self.INTENTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intention
        
        return None
    
    def search(
        self,
        query: str,
        use_cache: bool = True,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca archivos basándose en una consulta.
        
        Args:
            query: Consulta de búsqueda
            use_cache: Si True, usa cache para intenciones comunes
            recursive: Si True, busca recursivamente
        
        Returns:
            Lista de información de archivos encontrados
        """
        # Verificar cache para intenciones comunes
        if use_cache:
            intention = self.detect_intention(query)
            cache_key = f"{intention}:{query}" if intention else None
            
            if cache_key and cache_key in self._search_cache:
                files = self._search_cache[cache_key]
                return [get_file_info(f) for f in files]
        
        # Determinar extensiones a buscar
        extensions = self._get_extensions_from_query(query)
        
        # Determinar patrones de nombre
        patterns = self._get_name_patterns_from_query(query)
        
        # Realizar búsqueda en todos los directorios configurados
        all_files = []
        for search_path in self.search_paths:
            path = Path(search_path)
            if not path.exists():
                continue
            
            files = find_files(
                directory=search_path,
                patterns=patterns,
                extensions=extensions if extensions else None,
                recursive=recursive
            )
            all_files.extend(files)
        
        # Eliminar duplicados
        unique_files = list(set(all_files))
        
        # Actualizar cache si es una intención común
        if use_cache and intention:
            cache_key = f"{intention}:{query}"
            self._search_cache[cache_key] = unique_files
            
            # Limitar tamaño del cache
            if len(self._search_cache) > 100:
                # Eliminar la entrada más antigua
                oldest_key = next(iter(self._search_cache))
                del self._search_cache[oldest_key]
        
        # Convertir a formato de información
        return [get_file_info(f) for f in unique_files]
    
    def _get_extensions_from_query(self, query: str) -> List[str]:
        """Extrae extensiones de archivo de la consulta"""
        query_lower = query.lower()
        extensions = []
        
        if any(word in query_lower for word in ['pdf']):
            extensions.append('.pdf')
        if any(word in query_lower for word in ['odt', 'writer']):
            extensions.append('.odt')
        if any(word in query_lower for word in ['odp', 'presentation', 'diapositiva']):
            extensions.append('.odp')
        if any(word in query_lower for word in ['odg', 'dibujo']):
            extensions.append('.odg')
        if any(word in query_lower for word in ['ods', 'spreadsheet', 'calc']):
            extensions.append('.ods')
        if any(word in query_lower for word in ['doc', 'word']):
            extensions.extend(['.doc', '.docx'])
        if any(word in query_lower for word in ['xls', 'excel']):
            extensions.extend(['.xls', '.xlsx'])
        if any(word in query_lower for word in ['ppt', 'powerpoint']):
            extensions.extend(['.ppt', '.pptx'])
        if any(word in query_lower for word in ['imagen', 'image', 'png', 'jpg']):
            extensions.extend(['.png', '.jpg', '.jpeg', '.gif', '.bmp'])
        
        return extensions
    
    def _get_name_patterns_from_query(self, query: str) -> List[str]:
        """Extrae patrones de nombre de archivo de la consulta"""
        patterns = []
        
        # Buscar palabras entre comillas como patrones exactos
        quoted = re.findall(r'"([^"]+)"', query)
        patterns.extend(quoted)
        
        # Buscar términos específicos (palabras de más de 3 caracteres)
        words = re.findall(r'\b\w{4,}\b', query)
        for word in words:
            if word.lower() not in ['buscar', 'find', 'look', 'archivo', 'file', 'documento']:
                patterns.append(word)
        
        return patterns
    
    def clear_cache(self):
        """Limpia el cache de búsquedas"""
        self._search_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del agente"""
        return {
            "cache_size": len(self._search_cache),
            "search_paths": self.search_paths,
            "supported_extensions": supported_extensions()
        }
