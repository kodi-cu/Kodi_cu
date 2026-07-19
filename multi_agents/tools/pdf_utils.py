"""Utilidades para procesamiento de archivos PDF"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import io


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extrae texto de un archivo PDF.
    
    Args:
        file_path: Ruta al archivo PDF
    
    Returns:
        Texto extraído del PDF
    """
    try:
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except ImportError:
        raise ImportError("PyPDF2 no está instalado. Ejecuta: pip install PyPDF2")
    except Exception as e:
        return f"Error leyendo PDF: {str(e)}"


def extract_metadata_from_pdf(file_path: Path) -> Dict[str, Any]:
    """
    Extrae metadatos de un archivo PDF.
    
    Args:
        file_path: Ruta al archivo PDF
    
    Returns:
        Diccionario con metadatos del PDF
    """
    try:
        import PyPDF2
        
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            metadata = reader.metadata
            
            return {
                "title": metadata.get('/Title', '') if metadata else '',
                "author": metadata.get('/Author', '') if metadata else '',
                "subject": metadata.get('/Subject', '') if metadata else '',
                "creator": metadata.get('/Creator', '') if metadata else '',
                "producer": metadata.get('/Producer', '') if metadata else '',
                "pages": len(reader.pages),
                "encrypted": reader.is_encrypted
            }
    except Exception as e:
        return {"error": str(e)}


def get_pdf_images(file_path: Path, output_dir: Optional[Path] = None) -> List[Path]:
    """
    Extrae imágenes de un PDF (requiere pdf2image).
    
    Args:
        file_path: Ruta al archivo PDF
        output_dir: Directorio para guardar imágenes
    
    Returns:
        Lista de rutas a las imágenes extraídas
    """
    try:
        from pdf2image import convert_from_path
        
        if output_dir is None:
            output_dir = file_path.parent / f"{file_path.stem}_images"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        images = convert_from_path(file_path)
        image_paths = []
        
        for i, image in enumerate(images):
            image_path = output_dir / f"page_{i+1}.png"
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        
        return image_paths
    except ImportError:
        raise ImportError("pdf2image no está instalado. Ejecuta: pip install pdf2image")
    except Exception as e:
        print(f"Error extrayendo imágenes: {str(e)}")
        return []


def is_pdf_valid(file_path: Path) -> bool:
    """Verifica si un archivo es un PDF válido"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            len(reader.pages)  # Intenta leer las páginas
            return True
    except:
        return False
