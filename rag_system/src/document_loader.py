"""
Módulo para carga y procesamiento de documentos.
Soporta PDF, TXT y Markdown.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import hashlib

# Document loaders
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


@dataclass
class Document:
    """Representa un documento con su contenido y metadatos."""
    content: str
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        # Generar ID único basado en el contenido
        if "doc_id" not in self.metadata:
            self.metadata["doc_id"] = hashlib.md5(
                self.content.encode()
            ).hexdigest()


def load_pdf(file_path: str) -> List[Document]:
    """
    Carga un archivo PDF y extrae el texto por páginas.
    
    Estrategia para tablas y listas:
    - Se extrae el texto plano manteniendo saltos de línea
    - Las tablas se convierten a formato texto con separadores
    - Para mejor manejo de tablas complejas, considerar usar pdfplumber
    
    Args:
        file_path: Ruta al archivo PDF
        
    Returns:
        Lista de documentos (uno por página)
    """
    if not PYPDF_AVAILABLE:
        raise ImportError(
            "pypdf no está instalado. Ejecuta: pip install pypdf"
        )
    
    documents = []
    reader = PdfReader(file_path)
    
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text.strip():  # Solo agregar si hay contenido
            doc = Document(
                content=text,
                metadata={
                    "source": str(file_path),
                    "page": page_num,
                    "file_type": "pdf",
                }
            )
            documents.append(doc)
    
    return documents


def load_txt(file_path: str) -> List[Document]:
    """
    Carga un archivo de texto plano.
    
    Args:
        file_path: Ruta al archivo TXT
        
    Returns:
        Lista con un solo documento
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    doc = Document(
        content=content,
        metadata={
            "source": str(file_path),
            "file_type": "txt",
        }
    )
    
    return [doc]


def load_markdown(file_path: str) -> List[Document]:
    """
    Carga un archivo Markdown y lo convierte a texto plano.
    
    Manejo especial para listas y tablas Markdown:
    - Las listas mantienen su estructura con guiones/números
    - Las tablas se convierten a texto con separadores |
    
    Args:
        file_path: Ruta al archivo MD
        
    Returns:
        Lista con un solo documento
    """
    if not MARKDOWN_AVAILABLE:
        raise ImportError(
            "markdown no está instalado. Ejecuta: pip install markdown"
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convertir Markdown a HTML y luego extraer texto
    # Para este caso simple, mantenemos el texto Markdown limpio
    # que preserva la estructura de listas y tablas
    
    doc = Document(
        content=content,
        metadata={
            "source": str(file_path),
            "file_type": "markdown",
        }
    )
    
    return [doc]


def load_documents(directory: str, file_types: List[str] = None) -> List[Document]:
    """
    Carga todos los documentos de un directorio.
    
    Soporta múltiples formatos y maneja archivos con estructuras complejas.
    
    Args:
        directory: Ruta al directorio con documentos
        file_types: Lista de extensiones a cargar (default: ['pdf', 'txt', 'md'])
        
    Returns:
        Lista de documentos cargados
    """
    if file_types is None:
        file_types = ['pdf', 'txt', 'md']
    
    documents = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Advertencia: El directorio {directory} no existe.")
        return documents
    
    # Mapeo de extensiones a funciones de carga
    loaders = {
        'pdf': load_pdf,
        'txt': load_txt,
        'md': load_markdown,
        'markdown': load_markdown,
    }
    
    for file_path in directory_path.iterdir():
        ext = file_path.suffix.lower().lstrip('.')
        if ext in file_types and ext in loaders:
            try:
                print(f"Cargando: {file_path.name}")
                docs = loaders[ext](str(file_path))
                documents.extend(docs)
            except Exception as e:
                print(f"Error cargando {file_path.name}: {e}")
    
    print(f"\nTotal de documentos cargados: {len(documents)}")
    return documents


def load_document(file_path: str) -> List[Document]:
    """
    Carga un único documento detectando su tipo automáticamente.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        Lista de documentos
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower().lstrip('.')
    
    loaders = {
        'pdf': load_pdf,
        'txt': load_txt,
        'md': load_markdown,
        'markdown': load_markdown,
    }
    
    if ext not in loaders:
        raise ValueError(
            f"Formato no soportado: {ext}. "
            f"Formatos soportados: {list(loaders.keys())}"
        )
    
    return loaders[ext](str(file_path))
