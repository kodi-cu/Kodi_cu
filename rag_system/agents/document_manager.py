"""
Agente especializado en gestión y manipulación de documentos.

Permite:
- Crear nuevos documentos
- Modificar existentes
- Convertir entre formatos
- Organizar en directorios
- Generar reportes
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class DocumentManagerAgent:
    """
    Agente para crear, modificar y organizar documentos.
    
    Funcionalidades:
    - Crear documentos desde texto
    - Mover/copiar/renombrar archivos
    - Organizar por categoría
    - Generar reportes consolidados
    - Eliminar/archivar documentos
    """
    
    def __init__(self, base_directory: str = "./managed_documents"):
        """
        Inicializa el gestor de documentos.
        
        Args:
            base_directory: Directorio base para operaciones
        """
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)
    
    def create_document(
        self,
        content: str,
        filename: str,
        directory: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Crea un nuevo documento.
        
        Args:
            content: Contenido del documento
            filename: Nombre del archivo (con extensión)
            directory: Subdirectorio (opcional)
            metadata: Metadatos para incluir como comentario
            
        Returns:
            Ruta del archivo creado
        """
        if directory:
            target_dir = self.base_directory / directory
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.base_directory
        
        file_path = target_dir / filename
        
        # Agregar metadata como encabezado si es texto plano
        if metadata and filename.endswith('.txt'):
            header = f"""# Metadata
# Created: {datetime.now().isoformat()}
# Source: {metadata.get('source', 'unknown')}
# Category: {metadata.get('category', 'general')}

"""
            content = header + content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)
    
    def create_report(
        self,
        title: str,
        sections: List[Dict[str, str]],
        output_filename: str = "reporte.md"
    ) -> str:
        """
        Crea un reporte estructurado en Markdown.
        
        Args:
            title: Título del reporte
            sections: Lista de secciones {title, content}
            output_filename: Nombre del archivo de salida
            
        Returns:
            Ruta del reporte creado
        """
        content = f"# {title}\n\n"
        content += f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        content += "---\n\n"
        
        for i, section in enumerate(sections, 1):
            content += f"## {section.get('title', f'Sección {i}')}\n\n"
            content += section.get('content', '') + "\n\n"
        
        return self.create_document(content, output_filename, directory="reports")
    
    def move_file(self, source_path: str, destination_dir: str) -> str:
        """
        Mueve un archivo a otro directorio.
        
        Args:
            source_path: Ruta original
            destination_dir: Directorio destino
            
        Returns:
            Nueva ruta del archivo
        """
        source = Path(source_path)
        dest_dir = self.base_directory / destination_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_dir / source.name
        
        shutil.move(str(source), str(dest_path))
        return str(dest_path)
    
    def copy_file(self, source_path: str, destination_dir: str, 
                  new_name: Optional[str] = None) -> str:
        """
        Copia un archivo a otro directorio.
        
        Args:
            source_path: Ruta original
            destination_dir: Directorio destino
            new_name: Nuevo nombre (opcional)
            
        Returns:
            Ruta de la copia
        """
        source = Path(source_path)
        dest_dir = self.base_directory / destination_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_name = new_name if new_name else source.name
        dest_path = dest_dir / dest_name
        
        shutil.copy2(str(source), str(dest_path))
        return str(dest_path)
    
    def rename_file(self, file_path: str, new_name: str) -> str:
        """
        Renombra un archivo.
        
        Args:
            file_path: Ruta actual
            new_name: Nuevo nombre
            
        Returns:
            Nueva ruta
        """
        file = Path(file_path)
        new_path = file.parent / new_name
        file.rename(new_path)
        return str(new_path)
    
    def organize_by_type(self, directory: str = ".") -> Dict[str, List[str]]:
        """
        Organiza archivos por tipo en subdirectorios.
        
        Args:
            directory: Directorio a organizar
            
        Returns:
            Diccionario con organización realizada
        """
        dir_path = Path(directory)
        organized = {}
        
        # Agrupar por extensión
        by_extension = {}
        for file in dir_path.iterdir():
            if file.is_file():
                ext = file.suffix.lower().lstrip('.') or 'sin_extension'
                if ext not in by_extension:
                    by_extension[ext] = []
                by_extension[ext].append(file)
        
        # Crear subdirectorios y mover
        for ext, files in by_extension.items():
            ext_dir = dir_path / ext
            ext_dir.mkdir(exist_ok=True)
            organized[ext] = []
            
            for file in files:
                try:
                    new_path = ext_dir / file.name
                    shutil.move(str(file), str(new_path))
                    organized[ext].append(str(new_path))
                except Exception as e:
                    print(f"Error moviendo {file}: {e}")
        
        return organized
    
    def delete_file(self, file_path: str, permanent: bool = False) -> bool:
        """
        Elimina un archivo.
        
        Args:
            file_path: Ruta del archivo
            permanent: Si True, elimina permanentemente; si False, mueve a trash
            
        Returns:
            True si éxito
        """
        try:
            file = Path(file_path)
            
            if permanent:
                file.unlink()
            else:
                trash_dir = self.base_directory / "_trash"
                trash_dir.mkdir(exist_ok=True)
                shutil.move(str(file), str(trash_dir / file.name))
            
            return True
        except Exception as e:
            print(f"Error eliminando archivo: {e}")
            return False
    
    def archive_documents(self, file_paths: List[str], 
                         archive_name: str = "archivo.zip") -> str:
        """
        Archiva múltiples documentos en un ZIP.
        
        Args:
            file_paths: Lista de rutas a archivar
            archive_name: Nombre del archivo ZIP
            
        Returns:
            Ruta del archivo ZIP
        """
        import zipfile
        
        archive_path = self.base_directory / "archives" / archive_name
        archive_path.parent.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                file = Path(file_path)
                if file.exists():
                    zipf.write(file, file.name)
        
        return str(archive_path)
    
    def consolidate_texts(
        self,
        file_paths: List[str],
        output_filename: str = "consolidado.txt",
        include_sources: bool = True
    ) -> str:
        """
        Consolida múltiples archivos de texto en uno solo.
        
        Args:
            file_paths: Lista de archivos a consolidar
            output_filename: Nombre del archivo de salida
            include_sources: Incluir indicadores de fuente
            
        Returns:
            Ruta del archivo consolidado
        """
        content_parts = []
        
        for file_path in file_paths:
            file = Path(file_path)
            if not file.exists():
                continue
            
            if include_sources:
                content_parts.append(f"\n{'='*60}")
                content_parts.append(f"FUENTE: {file.name}")
                content_parts.append(f"{'='*60}\n")
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content_parts.append(f.read())
            except Exception as e:
                content_parts.append(f"[Error leyendo {file.name}: {e}]")
        
        consolidated_content = "\n\n".join(content_parts)
        return self.create_document(consolidated_content, output_filename)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Diccionario con información
        """
        file = Path(file_path)
        
        if not file.exists():
            return {"error": "Archivo no encontrado"}
        
        stat = file.stat()
        
        return {
            "name": file.name,
            "path": str(file),
            "extension": file.suffix.lower().lstrip('.'),
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_readable": os.access(file, os.R_OK),
            "is_writable": os.access(file, os.W_OK),
        }
    
    def list_directory(self, directory: str = ".", 
                       recursive: bool = False) -> List[Dict[str, Any]]:
        """
        Lista contenido de un directorio.
        
        Args:
            directory: Directorio a listar
            recursive: Si True, incluye subdirectorios
            
        Returns:
            Lista de información de archivos
        """
        dir_path = Path(directory)
        results = []
        
        if recursive:
            items = dir_path.rglob('*')
        else:
            items = dir_path.iterdir()
        
        for item in items:
            info = {
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
            }
            
            if item.is_file():
                info["extension"] = item.suffix.lower().lstrip('.')
                info["size_bytes"] = item.stat().st_size
            
            results.append(info)
        
        return sorted(results, key=lambda x: (x['type'] != 'directory', x['name']))
    
    def search_in_content(self, directory: str, pattern: str,
                          case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Busca un patrón en el contenido de archivos de texto.
        
        Args:
            directory: Directorio donde buscar
            pattern: Patrón a buscar
            case_sensitive: Distinguir mayúsculas/minúsculas
            
        Returns:
            Lista de coincidencias encontradas
        """
        results = []
        dir_path = Path(directory)
        
        for file in dir_path.glob('*'):
            if not file.is_file():
                continue
            
            # Solo buscar en archivos de texto
            ext = file.suffix.lower()
            if ext not in ['.txt', '.md', '.csv', '.log']:
                continue
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                flags = 0 if case_sensitive else re.IGNORECASE
                import re
                matches = re.findall(pattern, content, flags)
                
                if matches:
                    results.append({
                        "file": str(file),
                        "matches_count": len(matches),
                        "sample_matches": matches[:5],  # Primeras 5 coincidencias
                    })
            except Exception:
                continue
        
        return results
