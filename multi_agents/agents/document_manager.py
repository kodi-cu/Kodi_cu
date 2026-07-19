"""Agente DocumentManager - Gestión y manipulación de documentos"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import shutil
import json


class DocumentManagerAgent:
    """
    Agente especializado en crear, modificar, organizar y gestionar documentos.
    """
    
    def __init__(self, output_dir: str = "./output"):
        """
        Inicializa el gestor de documentos.
        
        Args:
            output_dir: Directorio base para operaciones de salida
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_document(
        self,
        content: str,
        filename: str,
        format: str = "txt",
        directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo documento.
        
        Args:
            content: Contenido del documento
            filename: Nombre del archivo (sin extensión)
            format: Formato del archivo (txt, md, json, csv)
            directory: Directorio donde guardar (por defecto output_dir)
        
        Returns:
            Información del archivo creado
        """
        target_dir = Path(directory) if directory else self.output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Determinar extensión
        ext_map = {
            'txt': '.txt',
            'md': '.md',
            'json': '.json',
            'csv': '.csv'
        }
        extension = ext_map.get(format.lower(), '.txt')
        
        file_path = target_dir / f"{filename}{extension}"
        
        try:
            # Procesar contenido según formato
            if format.lower() == 'json':
                # Intentar parsear como JSON si es válido
                try:
                    json_content = json.loads(content)
                    write_content = json.dumps(json_content, indent=2, ensure_ascii=False)
                except:
                    write_content = content
            else:
                write_content = content
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(write_content)
            
            return {
                'success': True,
                'path': str(file_path.absolute()),
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'format': format
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def copy_file(
        self,
        source_path: Union[str, Path],
        destination_path: Union[str, Path],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Copia un archivo.
        
        Args:
            source_path: Ruta del archivo origen
            destination_path: Ruta de destino
            overwrite: Si True, sobrescribe si existe
        
        Returns:
            Información de la operación
        """
        source = Path(source_path)
        dest = Path(destination_path)
        
        if not source.exists():
            return {'success': False, 'error': 'Archivo origen no encontrado'}
        
        if dest.exists() and not overwrite:
            return {'success': False, 'error': 'Archivo destino ya existe'}
        
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            
            return {
                'success': True,
                'source': str(source),
                'destination': str(dest),
                'size': dest.stat().st_size
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def move_file(
        self,
        source_path: Union[str, Path],
        destination_path: Union[str, Path],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Mueve/renombra un archivo.
        
        Args:
            source_path: Ruta del archivo origen
            destination_path: Ruta de destino
            overwrite: Si True, sobrescribe si existe
        
        Returns:
            Información de la operación
        """
        source = Path(source_path)
        dest = Path(destination_path)
        
        if not source.exists():
            return {'success': False, 'error': 'Archivo origen no encontrado'}
        
        if dest.exists() and not overwrite:
            return {'success': False, 'error': 'Archivo destino ya existe'}
        
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            
            return {
                'success': True,
                'source': str(source),
                'destination': str(dest)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_file(
        self,
        file_path: Union[str, Path],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Elimina un archivo.
        
        Args:
            file_path: Ruta del archivo a eliminar
            force: Si True, no pregunta confirmación
        
        Returns:
            Información de la operación
        """
        path = Path(file_path)
        
        if not path.exists():
            return {'success': False, 'error': 'Archivo no encontrado'}
        
        if not path.is_file():
            return {'success': False, 'error': 'No es un archivo'}
        
        try:
            path.unlink()
            return {
                'success': True,
                'deleted': str(path)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def organize_by_type(
        self,
        source_dir: Union[str, Path],
        target_base: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Organiza archivos por tipo de extensión en subdirectorios.
        
        Args:
            source_dir: Directorio con archivos a organizar
            target_base: Directorio base para organización (por defecto source_dir)
        
        Returns:
            Información de la organización
        """
        source = Path(source_dir)
        target = Path(target_base) if target_base else source
        
        if not source.exists():
            return {'success': False, 'error': 'Directorio no encontrado'}
        
        moved_files = []
        errors = []
        
        # Agrupar por extensión
        for file in source.glob("*"):
            if not file.is_file():
                continue
            
            ext = file.suffix.lower().replace('.', '')
            if not ext:
                ext = 'sin_extension'
            
            target_dir = target / ext
            target_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = target_dir / file.name
            
            try:
                if dest_path.exists():
                    # Añadir timestamp para evitar colisiones
                    dest_path = target_dir / f"{file.stem}_{int(file.stat().st_mtime)}{file.suffix}"
                
                shutil.move(str(file), str(dest_path))
                moved_files.append({
                    'original': str(file),
                    'new': str(dest_path),
                    'category': ext
                })
            except Exception as e:
                errors.append({'file': str(file), 'error': str(e)})
        
        return {
            'success': len(errors) == 0,
            'moved_count': len(moved_files),
            'error_count': len(errors),
            'moved_files': moved_files,
            'errors': errors
        }
    
    def create_summary_report(
        self,
        documents: List[Dict[str, Any]],
        output_filename: str = "reporte_documentos"
    ) -> Dict[str, Any]:
        """
        Crea un reporte resumen de múltiples documentos.
        
        Args:
            documents: Lista de información de documentos
            output_filename: Nombre del archivo de reporte
        
        Returns:
            Información del reporte creado
        """
        report_lines = [
            "# Reporte de Documentos",
            "=" * 50,
            f"Total documentos: {len(documents)}",
            "",
        ]
        
        for i, doc in enumerate(documents, 1):
            report_lines.append(f"\n## Documento {i}")
            report_lines.append(f"Nombre: {doc.get('name', 'N/A')}")
            report_lines.append(f"Ruta: {doc.get('path', 'N/A')}")
            report_lines.append(f"Tamaño: {doc.get('size_human', 'N/A')}")
            report_lines.append(f"Tipo: {doc.get('extension', 'N/A')}")
            
            if 'category' in doc:
                report_lines.append(f"Categoría: {doc['category']}")
            if 'summary' in doc:
                report_lines.append(f"Resumen: {doc['summary'][:200]}...")
            
            report_lines.append("-" * 30)
        
        return self.create_document(
            content='\n'.join(report_lines),
            filename=output_filename,
            format='md'
        )
    
    def backup_directory(
        self,
        source_dir: Union[str, Path],
        backup_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea una copia de seguridad de un directorio.
        
        Args:
            source_dir: Directorio a respaldar
            backup_name: Nombre del backup (por defect: timestamp)
        
        Returns:
            Información del backup
        """
        source = Path(source_dir)
        
        if not source.exists():
            return {'success': False, 'error': 'Directorio no encontrado'}
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"backup_{timestamp}"
        
        backup_dir = self.output_dir / backup_name
        
        try:
            shutil.copytree(source, backup_dir)
            
            file_count = sum(1 for _ in backup_dir.rglob("*") if _.is_file())
            
            return {
                'success': True,
                'backup_path': str(backup_dir),
                'files_count': file_count,
                'timestamp': timestamp
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
