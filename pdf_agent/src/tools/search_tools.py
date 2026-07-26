"""
Herramientas de búsqueda en documentos y contenido.
"""

import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


class SearchTools:
    """Clase para herramientas de búsqueda avanzada."""
    
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def search_text_in_files(self, pattern: str, directory: Optional[str] = None, 
                             file_extension: Optional[str] = ".pdf", 
                             case_sensitive: bool = False) -> Dict[str, Any]:
        """
        Busca un patrón de texto en múltiples archivos.
        
        Args:
            pattern: Patrón a buscar (regex soportado)
            directory: Directorio donde buscar
            file_extension: Extensión de archivo a filtrar
            case_sensitive: Si la búsqueda distingue mayúsculas
            
        Returns:
            Diccionario con los resultados
        """
        target_dir = Path(directory) if directory else self.base_dir
        
        if not target_dir.exists():
            return {"success": False, "error": f"El directorio {target_dir} no existe"}
        
        try:
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            
            for file_path in target_dir.rglob(f"*{file_extension}" if file_extension else "*"):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        matches = list(re.finditer(pattern, content, flags))
                        
                        if matches:
                            file_results = []
                            for match in matches:
                                start = max(0, match.start() - 50)
                                end = min(len(content), match.end() + 50)
                                context = content[start:end]
                                
                                file_results.append({
                                    "match": match.group(),
                                    "position": match.start(),
                                    "context": context,
                                    "line": content[:match.start()].count('\n') + 1
                                })
                            
                            results.append({
                                "file": str(file_path),
                                "total_matches": len(matches),
                                "matches": file_results
                            })
                    except Exception:
                        continue
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": str(target_dir),
                "files_searched": sum(1 for _ in target_dir.rglob(f"*{file_extension}" if file_extension else "*") if _.is_file()),
                "files_with_matches": len(results),
                "total_matches": sum(r["total_matches"] for r in results),
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_similar_documents(self, reference_file: str, directory: Optional[str] = None, 
                               top_n: int = 5) -> Dict[str, Any]:
        """
        Encuentra documentos similares basándose en palabras clave comunes.
        
        Args:
            reference_file: Archivo de referencia
            directory: Directorio donde buscar
            top_n: Número de resultados similares a devolver
            
        Returns:
            Diccionario con documentos similares
        """
        ref_path = Path(reference_file)
        
        if not ref_path.exists():
            return {"success": False, "error": f"El archivo {reference_file} no existe"}
        
        target_dir = Path(directory) if directory else self.base_dir
        
        try:
            # Extraer palabras clave del archivo de referencia
            with open(ref_path, 'r', encoding='utf-8', errors='ignore') as f:
                ref_content = f.read()
            
            ref_keywords = self._extract_keywords(ref_content)
            
            similarities = []
            
            for file_path in target_dir.rglob("*.pdf"):
                if file_path.is_file() and str(file_path) != str(ref_path):
                    try:
                        # Para PDFs, usamos una extracción básica
                        # En producción, usaríamos pdf_tools.extract_text
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='ignore')
                        
                        file_keywords = self._extract_keywords(content)
                        
                        # Calcular similitud (intersección de keywords)
                        common_keywords = ref_keywords.intersection(file_keywords)
                        similarity_score = len(common_keywords) / max(len(ref_keywords), 1)
                        
                        if similarity_score > 0:
                            similarities.append({
                                "file": str(file_path),
                                "similarity_score": similarity_score,
                                "common_keywords": list(common_keywords)[:10],
                                "common_keywords_count": len(common_keywords)
                            })
                    except Exception:
                        continue
            
            # Ordenar por similitud
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "success": True,
                "reference_file": str(ref_path),
                "top_n": top_n,
                "total_compared": len(similarities),
                "similar_documents": similarities[:top_n]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_keywords(self, text: str, top_n: int = 20) -> set:
        """Extrae palabras clave de un texto."""
        # Eliminar caracteres especiales y convertir a minúsculas
        words = re.findall(r'\b[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]{4,}\b', text.lower())
        
        # Palabras vacías comunes en español e inglés
        stop_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'has',
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'del', 'al',
            'por', 'para', 'con', 'sin', 'sobre', 'entre', 'hasta', 'como',
            'que', 'de', 'en', 'es', 'ser', 'estar', 'haber', 'hacer'
        }
        
        # Contar frecuencia de palabras
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Obtener las más frecuentes
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return set(word for word, _ in sorted_words[:top_n])
    
    def search_by_date_range(self, start_date: str, end_date: str, 
                            directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Busca archivos dentro de un rango de fechas.
        
        Args:
            start_date: Fecha inicial (formato YYYY-MM-DD)
            end_date: Fecha final (formato YYYY-MM-DD)
            directory: Directorio donde buscar
            
        Returns:
            Diccionario con los archivos encontrados
        """
        target_dir = Path(directory) if directory else self.base_dir
        
        if not target_dir.exists():
            return {"success": False, "error": f"El directorio {target_dir} no existe"}
        
        try:
            from datetime import datetime as dt
            
            start = dt.strptime(start_date, "%Y-%m-%d")
            end = dt.strptime(end_date, "%Y-%m-%d")
            
            results = []
            
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    mtime = dt.fromtimestamp(stat.st_mtime)
                    
                    if start <= mtime <= end:
                        results.append({
                            "file": str(file_path),
                            "modified": mtime.isoformat(),
                            "size": stat.st_size
                        })
            
            return {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "total_found": len(results),
                "files": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def index_documents(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un índice de documentos en un directorio.
        
        Args:
            directory: Directorio a indexar
            
        Returns:
            Diccionario con el índice creado
        """
        target_dir = Path(directory) if directory else self.base_dir
        
        if not target_dir.exists():
            return {"success": False, "error": f"El directorio {target_dir} no existe"}
        
        try:
            index = {
                "created": datetime.now().isoformat(),
                "directory": str(target_dir),
                "total_documents": 0,
                "by_extension": {},
                "documents": []
            }
            
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    ext = file_path.suffix.lower()
                    
                    doc_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "extension": ext,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    
                    index["documents"].append(doc_info)
                    index["total_documents"] += 1
                    
                    if ext not in index["by_extension"]:
                        index["by_extension"][ext] = 0
                    index["by_extension"][ext] += 1
            
            return {
                "success": True,
                "index": index
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
