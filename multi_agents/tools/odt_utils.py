"""Utilidades para procesamiento de archivos ODT, ODS, ODP, ODG (OpenDocument)"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO


def extract_text_from_odt(file_path: Path) -> str:
    """
    Extrae texto de un archivo ODT (OpenDocument Text).
    
    Args:
        file_path: Ruta al archivo ODT
    
    Returns:
        Texto extraído del documento
    """
    try:
        if not zipfile.is_zipfile(file_path):
            return "Error: El archivo no es un ODT válido"
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if 'content.xml' not in zip_ref.namelist():
                return "Error: No se encontró content.xml en el ODT"
            
            xml_content = zip_ref.read('content.xml')
            return parse_odt_xml(xml_content)
    except Exception as e:
        return f"Error leyendo ODT: {str(e)}"


def parse_odt_xml(xml_content: bytes) -> str:
    """Parsea el XML de un ODT y extrae el texto"""
    try:
        root = ET.fromstring(xml_content)
        text_parts = []
        
        # Namespace de OpenDocument
        ns = {
            'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
            'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
            'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
        }
        
        # Buscar todos los elementos de párrafo
        for paragraph in root.iter('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'):
            p_text = ''.join(paragraph.itertext())
            if p_text.strip():
                text_parts.append(p_text.strip())
        
        return '\n'.join(text_parts)
    except Exception as e:
        return f"Error parseando XML: {str(e)}"


def extract_text_from_ods(file_path: Path) -> str:
    """
    Extrae texto de un archivo ODS (OpenDocument Spreadsheet).
    
    Args:
        file_path: Ruta al archivo ODS
    
    Returns:
        Texto extraído de la hoja de cálculo
    """
    try:
        if not zipfile.is_zipfile(file_path):
            return "Error: El archivo no es un ODS válido"
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if 'content.xml' not in zip_ref.namelist():
                return "Error: No se encontró content.xml en el ODS"
            
            xml_content = zip_ref.read('content.xml')
            return parse_ods_xml(xml_content)
    except Exception as e:
        return f"Error leyendo ODS: {str(e)}"


def parse_ods_xml(xml_content: bytes) -> str:
    """Parsea el XML de un ODS y extrae el texto de las celdas"""
    try:
        root = ET.fromstring(xml_content)
        text_parts = []
        
        # Buscar todas las celdas de tabla
        for cell in root.iter('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-cell'):
            cell_text = ''.join(cell.itertext())
            if cell_text.strip():
                text_parts.append(cell_text.strip())
        
        return ' | '.join(text_parts)
    except Exception as e:
        return f"Error parseando XML: {str(e)}"


def extract_text_from_odp(file_path: Path) -> str:
    """
    Extrae texto de un archivo ODP (OpenDocument Presentation).
    
    Args:
        file_path: Ruta al archivo ODP
    
    Returns:
        Texto extraído de la presentación
    """
    try:
        if not zipfile.is_zipfile(file_path):
            return "Error: El archivo no es un ODP válido"
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if 'content.xml' not in zip_ref.namelist():
                return "Error: No se encontró content.xml en el ODP"
            
            xml_content = zip_ref.read('content.xml')
            return parse_odp_xml(xml_content)
    except Exception as e:
        return f"Error leyendo ODP: {str(e)}"


def parse_odp_xml(xml_content: bytes) -> str:
    """Parsea el XML de un ODP y extrae el texto de las diapositivas"""
    try:
        root = ET.fromstring(xml_content)
        text_parts = []
        
        # Buscar todos los elementos de texto en la presentación
        for text_elem in root.iter('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'):
            p_text = ''.join(text_elem.itertext())
            if p_text.strip():
                text_parts.append(p_text.strip())
        
        return '\n'.join(text_parts)
    except Exception as e:
        return f"Error parseando XML: {str(e)}"


def get_odf_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extrae metadatos de un archivo OpenDocument.
    
    Args:
        file_path: Ruta al archivo ODF
    
    Returns:
        Diccionario con metadatos
    """
    try:
        if not zipfile.is_zipfile(file_path):
            return {"error": "Archivo no válido"}
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if 'meta.xml' not in zip_ref.namelist():
                return {"error": "No se encontró meta.xml"}
            
            xml_content = zip_ref.read('meta.xml')
            root = ET.fromstring(xml_content)
            
            metadata = {}
            ns = {'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
                  'dc': 'http://purl.org/dc/elements/1.1/'}
            
            # Elementos comunes de metadatos
            for tag in ['title', 'creator', 'date', 'subject', 'description']:
                elem = root.find(f'.//{{http://purl.org/dc/elements/1.1/}}{tag}')
                if elem is not None and elem.text:
                    metadata[tag] = elem.text
            
            return metadata
    except Exception as e:
        return {"error": str(e)}


def is_odf_valid(file_path: Path) -> bool:
    """Verifica si un archivo es un OpenDocument válido"""
    try:
        if not zipfile.is_zipfile(file_path):
            return False
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            return 'content.xml' in zip_ref.namelist()
    except:
        return False
