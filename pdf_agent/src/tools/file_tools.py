"""
Herramientas para gestión de archivos y directorios.
"""

import os
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


class FileTools:
    """Clase para herramientas de gestión de archivos."""
    
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def list_files(self, directory: Optional[str] = None, extension: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista archivos en un directorio.
        
        Args:
            directory: Directorio a listar (None para base_dir)
            extension: Filtrar por extensión (ej: '.pdf')
            
        Returns:
            Diccionario con la lista de archivos
        """
        target_dir = Path(directory) if directory else self.base_dir
        
        if not target_dir.exists():
            return {"success": False, "error": f"El directorio {target_dir} no existe"}
        
        try:
            files = []
            for item in target_dir.iterdir():
                if item.is_file():
                    if extension is None or item.suffix.lower() == extension.lower():
                        stat = item.stat()
                        files.append({
                            "name": item.name,
                            "path": str(item),
                            "size": stat.st_size,
                            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "extension": item.suffix
                        })
            
            return {
                "success": True,
                "directory": str(target_dir),
                "total_files": len(files),
                "files": files
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_directory(self, dir_name: str, parent: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un nuevo directorio.
        
        Args:
            dir_name: Nombre del directorio a crear
            parent: Directorio padre (None para base_dir)
            
        Returns:
            Diccionario con el resultado
        """
        parent_dir = Path(parent) if parent else self.base_dir
        new_dir = parent_dir / dir_name
        
        try:
            new_dir.mkdir(parents=True, exist_ok=True)
            return {
                "success": True,
                "path": str(new_dir),
                "message": f"Directorio creado: {new_dir}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Mueve un archivo de una ubicación a otra.
        
        Args:
            source: Ruta del archivo origen
            destination: Ruta del archivo destino
            
        Returns:
            Diccionario con el resultado
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return {"success": False, "error": f"El archivo {source} no existe"}
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))
            
            return {
                "success": True,
                "source": str(source_path),
                "destination": str(dest_path),
                "message": "Archivo movido exitosamente"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copia un archivo de una ubicación a otra.
        
        Args:
            source: Ruta del archivo origen
            destination: Ruta del archivo destino
            
        Returns:
            Diccionario con el resultado
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return {"success": False, "error": f"El archivo {source} no existe"}
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source_path), str(dest_path))
            
            return {
                "success": True,
                "source": str(source_path),
                "destination": str(dest_path),
                "message": "Archivo copiado exitosamente"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Elimina un archivo.
        
        Args:
            file_path: Ruta del archivo a eliminar
            
        Returns:
            Diccionario con el resultado
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"success": False, "error": f"El archivo {file_path} no existe"}
            
            if path.is_file():
                path.unlink()
                return {
                    "success": True,
                    "file": file_path,
                    "message": "Archivo eliminado exitosamente"
                }
            else:
                return {"success": False, "error": f"{file_path} no es un archivo"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Diccionario con la información del archivo
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"success": False, "error": f"El archivo {file_path} no existe"}
            
            stat = path.stat()
            
            return {
                "success": True,
                "info": {
                    "name": path.name,
                    "path": str(path),
                    "size": stat.st_size,
                    "size_human": self._human_readable_size(stat.st_size),
                    "extension": path.suffix,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                    "is_file": path.is_file(),
                    "is_directory": path.is_dir()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _human_readable_size(self, size: int) -> str:
        """Convierte tamaño en bytes a formato legible."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def search_files(self, pattern: str, directory: Optional[str] = None, recursive: bool = True) -> Dict[str, Any]:
        """
        Busca archivos que coincidan con un patrón.
        
        Args:
            pattern: Patrón de búsqueda (puede usar * como comodín)
            directory: Directorio donde buscar (None para base_dir)
            recursive: Si buscar recursivamente en subdirectorios
            
        Returns:
            Diccionario con los archivos encontrados
        """
        target_dir = Path(directory) if directory else self.base_dir
        
        if not target_dir.exists():
            return {"success": False, "error": f"El directorio {target_dir} no existe"}
        
        try:
            files = []
            
            if recursive:
                matcher = target_dir.rglob(pattern)
            else:
                matcher = target_dir.glob(pattern)
            
            for item in matcher:
                if item.is_file():
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": str(target_dir),
                "recursive": recursive,
                "total_found": len(files),
                "files": files
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
