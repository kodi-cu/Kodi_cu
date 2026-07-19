"""
Agente especializado en búsqueda y localización de archivos.

Encuentra documentos en directorios locales filtrando por:
- Nombre o patrón
- Tipo de archivo (pdf, odt, odp, odg, etc.)
- Fecha de modificación
- Tamaño
"""

import os
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Información sobre un archivo encontrado."""
    path: str
    name: str
    extension: str
    size_bytes: int
    modified_date: datetime
    directory: str


class FileFinderAgent:
    """
    Agente para buscar y localizar archivos en el sistema.
    
    Funcionalidades:
    - Búsqueda recursiva en directorios
    - Filtrado por extensión, nombre, fecha y tamaño
    - Retorno de metadatos completos
    """
    
    SUPPORTED_EXTENSIONS = [
        'pdf', 'odt', 'ods', 'odp', 'odg',  # OpenDocument formats
        'txt', 'md', 'markdown',             # Text formats
        'doc', 'docx',                       # Word formats
        'xls', 'xlsx',                       # Excel formats
        'ppt', 'pptx',                       # PowerPoint formats
        'rtf', 'csv',                        # Other formats
    ]
    
    def __init__(self, base_directory: str = "."):
        """
        Inicializa el agente buscador.
        
        Args:
            base_directory: Directorio base para búsquedas
        """
        self.base_directory = Path(base_directory).resolve()
        
    def find_files(
        self,
        pattern: str = "*",
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None,
    ) -> List[FileInfo]:
        """
        Busca archivos que coincidan con los criterios especificados.
        
        Args:
            pattern: Patrón de nombre (ej: "*.pdf", "informe_*")
            extensions: Lista de extensiones a incluir (sin punto)
            recursive: Si True, busca en subdirectorios
            min_size: Tamaño mínimo en bytes
            max_size: Tamaño máximo en bytes
            modified_after: Fecha mínima de modificación
            modified_before: Fecha máxima de modificación
            
        Returns:
            Lista de FileInfo con los archivos encontrados
        """
        results = []
        
        if recursive:
            file_iterator = self.base_directory.rglob(pattern)
        else:
            file_iterator = self.base_directory.glob(pattern)
        
        for file_path in file_iterator:
            if not file_path.is_file():
                continue
            
            # Filtrar por extensión
            ext = file_path.suffix.lower().lstrip('.')
            if extensions and ext not in extensions:
                continue
            
            # Obtener metadatos
            stat_info = file_path.stat()
            modified_date = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Filtrar por tamaño
            if min_size is not None and stat_info.st_size < min_size:
                continue
            if max_size is not None and stat_info.st_size > max_size:
                continue
            
            # Filtrar por fecha
            if modified_after and modified_date < modified_after:
                continue
            if modified_before and modified_date > modified_before:
                continue
            
            # Crear FileInfo
            file_info = FileInfo(
                path=str(file_path),
                name=file_path.name,
                extension=ext,
                size_bytes=stat_info.st_size,
                modified_date=modified_date,
                directory=str(file_path.parent),
            )
            results.append(file_info)
        
        return results
    
    def find_by_type(self, file_type: str, recursive: bool = True) -> List[FileInfo]:
        """
        Busca archivos por tipo específico.
        
        Args:
            file_type: Tipo de archivo (ej: "pdf", "odt")
            recursive: Búsqueda recursiva
            
        Returns:
            Lista de archivos encontrados
        """
        return self.find_files(
            pattern=f"*.{file_type}",
            extensions=[file_type],
            recursive=recursive
        )
    
    def find_documents(
        self,
        recursive: bool = True,
        include_all_supported: bool = True
    ) -> List[FileInfo]:
        """
        Busca todos los documentos soportados.
        
        Args:
            recursive: Búsqueda recursiva
            include_all_supported: Incluir todas las extensiones soportadas
            
        Returns:
            Lista de documentos encontrados
        """
        extensions = self.SUPPORTED_EXTENSIONS if include_all_supported else ['pdf', 'odt', 'odp', 'odg']
        return self.find_files(extensions=extensions, recursive=recursive)
    
    def search_by_name(self, name_pattern: str, recursive: bool = True) -> List[FileInfo]:
        """
        Busca archivos por patrón de nombre.
        
        Args:
            name_pattern: Patrón de nombre (ej: "informe*", "*2024*")
            recursive: Búsqueda recursiva
            
        Returns:
            Lista de archivos encontrados
        """
        return self.find_files(pattern=name_pattern, recursive=recursive)
    
    def get_directory_structure(
        self,
        max_depth: int = 3,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """
        Obtiene la estructura del directorio como árbol.
        
        Args:
            max_depth: Profundidad máxima a recorrer
            current_depth: Profundidad actual (uso interno)
            
        Returns:
            Diccionario con estructura de directorios y archivos
        """
        structure = {
            "name": self.base_directory.name,
            "path": str(self.base_directory),
            "type": "directory",
            "children": [],
        }
        
        if current_depth >= max_depth:
            return structure
        
        try:
            items = sorted(self.base_directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for item in items:
                if item.is_dir():
                    child_agent = FileFinderAgent(str(item))
                    child_structure = child_agent.get_directory_structure(
                        max_depth=max_depth,
                        current_depth=current_depth + 1
                    )
                    structure["children"].append(child_structure)
                else:
                    ext = item.suffix.lower().lstrip('.')
                    structure["children"].append({
                        "name": item.name,
                        "path": str(item),
                        "type": "file",
                        "extension": ext,
                        "size_bytes": item.stat().st_size,
                    })
        except PermissionError:
            pass
        
        return structure
    
    def get_statistics(self, files: List[FileInfo]) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre una lista de archivos.
        
        Args:
            files: Lista de FileInfo
            
        Returns:
            Diccionario con estadísticas
        """
        if not files:
            return {"total_files": 0}
        
        by_extension = {}
        total_size = 0
        
        for file in files:
            # Contar por extensión
            by_extension[file.extension] = by_extension.get(file.extension, 0) + 1
            # Sumar tamaño
            total_size += file.size_bytes
        
        return {
            "total_files": len(files),
            "by_extension": by_extension,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_size_bytes": round(total_size / len(files), 2),
        }
    
    def to_dict(self, file_info: FileInfo) -> Dict[str, Any]:
        """Convierte FileInfo a diccionario serializable."""
        return {
            "path": file_info.path,
            "name": file_info.name,
            "extension": file_info.extension,
            "size_bytes": file_info.size_bytes,
            "size_kb": round(file_info.size_bytes / 1024, 2),
            "modified_date": file_info.modified_date.isoformat(),
            "directory": file_info.directory,
        }
    
    def search_summary(self, query: str = "") -> str:
        """
        Genera un resumen de búsqueda para el LLM.
        
        Args:
            query: Descripción de lo que se busca
            
        Returns:
            Resumen formateado para el contexto del LLM
        """
        files = self.find_documents(recursive=True)
        stats = self.get_statistics(files)
        
        summary = f"""
BÚSQUEDA DE ARCHIVOS
====================
Directorio base: {self.base_directory}
Total de documentos encontrados: {stats['total_files']}

Distribución por tipo:
"""
        for ext, count in sorted(stats['by_extension'].items()):
            summary += f"  - {ext}: {count} archivos\n"
        
        summary += f"\nTamaño total: {stats['total_size_mb']} MB\n"
        
        if files:
            summary += "\nArchivos recientes:\n"
            recent = sorted(files, key=lambda x: x.modified_date, reverse=True)[:5]
            for f in recent:
                summary += f"  - {f.name} ({f.extension}, {f.size_kb} KB)\n"
        
        return summary
