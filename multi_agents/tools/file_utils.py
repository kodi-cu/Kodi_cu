"""Herramientas utilitarias para el sistema multi-agente"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def find_files(
    directory: str = ".",
    patterns: List[str] = None,
    extensions: List[str] = None,
    recursive: bool = True
) -> List[Path]:
    """
    Busca archivos en un directorio con patrones y extensiones específicas.
    
    Args:
        directory: Directorio de búsqueda
        patterns: Patrones regex para filtrar nombres
        extensions: Extensiones permitidas (ej: ['.pdf', '.odt'])
        recursive: Si True, busca recursivamente
    
    Returns:
        Lista de rutas de archivos encontrados
    """
    if patterns is None:
        patterns = []
    if extensions is None:
        extensions = []
    
    results = []
    path = Path(directory)
    
    if not path.exists():
        return results
    
    search_func = path.rglob if recursive else path.glob
    
    for file_path in search_func("*"):
        if not file_path.is_file():
            continue
        
        # Filtrar por extensión
        if extensions and file_path.suffix.lower() not in [e.lower() for e in extensions]:
            continue
        
        # Filtrar por patrones
        if patterns:
            matches = False
            for pattern in patterns:
                if re.search(pattern, file_path.name, re.IGNORECASE):
                    matches = True
                    break
            if not matches:
                continue
        
        results.append(file_path)
    
    return results


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Obtiene información detallada de un archivo.
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        Diccionario con información del archivo
    """
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "path": str(file_path.absolute()),
        "size": stat.st_size,
        "size_human": format_size(stat.st_size),
        "extension": file_path.suffix.lower(),
        "modified": stat.st_mtime,
        "created": stat.st_ctime
    }


def format_size(size_bytes: int) -> str:
    """Formatea el tamaño de bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def ensure_directory(path: str) -> Path:
    """Asegura que un directorio existe, lo crea si no"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def supported_extensions() -> List[str]:
    """Lista de extensiones soportadas por el sistema"""
    return [
        '.pdf',
        '.odt', '.ods', '.odp', '.odg',
        '.docx', '.doc',
        '.xlsx', '.xls',
        '.pptx', '.ppt',
        '.txt', '.md',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp'  # Para visión
    ]


def is_supported_file(file_path: Path) -> bool:
    """Verifica si un archivo tiene una extensión soportada"""
    return file_path.suffix.lower() in supported_extensions()
