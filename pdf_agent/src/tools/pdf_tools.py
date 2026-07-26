"""
Herramientas para análisis y manipulación de documentos PDF.
Integración con el agente principal.
"""

import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from pdfplumber import open as pdf_open
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class PDFTools:
    """Clase para herramientas de análisis de PDF integradas con el agente."""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text(self, pdf_path: str, pages: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Extrae texto de un documento PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            pages: Lista de páginas a extraer (None para todas)
            
        Returns:
            Diccionario con el texto extraído y metadatos
        """
        if not PDF_AVAILABLE:
            return {"success": False, "error": "PyMuPDF no está instalado"}
        
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            metadata = {
                "num_pages": len(doc),
                "file_path": pdf_path,
                "pages_extracted": []
            }
            
            page_range = pages if pages else range(len(doc))
            
            for page_num in page_range:
                if page_num < len(doc):
                    page = doc[page_num]
                    text = page.get_text()
                    text_content.append({
                        "page": page_num + 1,
                        "text": text
                    })
                    metadata["pages_extracted"].append(page_num + 1)
            
            doc.close()
            
            return {
                "success": True,
                "text": "\n".join([item["text"] for item in text_content]),
                "pages": text_content,
                "metadata": metadata
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Obtiene metadatos de un documento PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con metadatos del PDF
        """
        if not PDF_AVAILABLE:
            return {"success": False, "error": "PyMuPDF no está instalado"}
        
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            result = {
                "success": True,
                "metadata": {
                    "title": metadata.get("title", "N/A"),
                    "author": metadata.get("author", "N/A"),
                    "subject": metadata.get("subject", "N/A"),
                    "creator": metadata.get("creator", "N/A"),
                    "producer": metadata.get("producer", "N/A"),
                    "creation_date": metadata.get("creationDate", "N/A"),
                    "modification_date": metadata.get("modDate", "N/A"),
                    "num_pages": len(doc),
                    "file_size": os.path.getsize(pdf_path),
                    "file_path": pdf_path
                }
            }
            
            doc.close()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_in_pdf(self, pdf_path: str, pattern: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """
        Busca un patrón en un documento PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            pattern: Patrón a buscar
            case_sensitive: Si la búsqueda distingue mayúsculas/minúsculas
            
        Returns:
            Diccionario con los resultados de la búsqueda
        """
        if not PDF_AVAILABLE:
            return {"success": False, "error": "PyMuPDF no está instalado"}
        
        try:
            doc = fitz.open(pdf_path)
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                matches = re.finditer(pattern, text, flags)
                for match in matches:
                    results.append({
                        "page": page_num + 1,
                        "match": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "context": text[max(0, match.start()-50):min(len(text), match.end()+50)]
                    })
            
            doc.close()
            
            return {
                "success": True,
                "pattern": pattern,
                "total_matches": len(results),
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_tables(self, pdf_path: str, pages: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Extrae tablas de un documento PDF usando pdfplumber.
        
        Args:
            pdf_path: Ruta al archivo PDF
            pages: Lista de páginas a procesar
            
        Returns:
            Diccionario con las tablas extraídas
        """
        if not PDFPLUMBER_AVAILABLE:
            return {"success": False, "error": "pdfplumber no está instalado"}
        
        try:
            tables_found = []
            
            with pdf_open(pdf_path) as pdf:
                page_range = pages if pages else range(len(pdf.pages))
                
                for page_num in page_range:
                    if page_num < len(pdf.pages):
                        page = pdf.pages[page_num]
                        tables = page.extract_tables()
                        
                        for table_idx, table in enumerate(tables):
                            tables_found.append({
                                "page": page_num + 1,
                                "table_index": table_idx,
                                "data": table,
                                "rows": len(table) if table else 0,
                                "columns": max([len(row) for row in table]) if table else 0
                            })
            
            return {
                "success": True,
                "total_tables": len(tables_found),
                "tables": tables_found
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def summarize_pdf(self, pdf_path: str, max_length: int = 500) -> Dict[str, Any]:
        """
        Genera un resumen básico de un PDF (extractivo).
        
        Args:
            pdf_path: Ruta al archivo PDF
            max_length: Longitud máxima del resumen
            
        Returns:
            Diccionario con el resumen
        """
        extraction = self.extract_text(pdf_path)
        
        if not extraction.get("success"):
            return extraction
        
        text = extraction["text"]
        
        # Dividir en oraciones
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Seleccionar las primeras oraciones significativas
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence) + 2  # +2 para el punto y espacio
            else:
                break
        
        summary = ". ".join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(text) if len(text) > 0 else 0
        }
    
    def classify_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Clasifica un documento basándose en su contenido.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con la clasificación del documento
        """
        extraction = self.extract_text(pdf_path, pages=[0, 1, 2])
        
        if not extraction.get("success"):
            return extraction
        
        text = extraction["text"].lower()
        
        # Palabras clave para clasificación
        categories = {
            "contract": ["contrato", "agreement", "partes", "cláusula", "firmado"],
            "invoice": ["factura", "invoice", "pago", "total", "impuesto", "iva"],
            "report": ["informe", "report", "análisis", "conclusiones", "resultados"],
            "manual": ["manual", "guía", "instrucciones", "cómo", "tutorial"],
            "academic": ["tesis", "dissertation", "abstract", "bibliografía", "referencias"],
            "legal": ["ley", "artículo", "normativa", "reglamento", "jurídico"],
            "financial": ["financiero", "balance", "estado", "cuenta", "presupuesto"]
        }
        
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[category] = score
        
        # Obtener categoría con mayor puntuación
        if scores:
            best_category = max(scores, key=scores.get)
            confidence = scores[best_category] / sum(scores.values()) if sum(scores.values()) > 0 else 0
        else:
            best_category = "unknown"
            confidence = 0
        
        return {
            "success": True,
            "category": best_category,
            "confidence": confidence,
            "all_scores": scores,
            "keywords_found": {
                cat: [kw for kw in keywords if kw in text]
                for cat, keywords in categories.items()
            }
        }
