"""
Funciones utilitarias para el agente PDF.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Asegura que un directorio existe, lo crea si es necesario.
    
    Args:
        path: Ruta del directorio
        
    Returns:
        Path object del directorio
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """
    Calcula el hash de un archivo.
    
    Args:
        file_path: Ruta del archivo
        algorithm: Algoritmo de hash (md5, sha1, sha256)
        
    Returns:
        Hash del archivo en hexadecimal
    """
    hash_func = getattr(hashlib, algorithm, hashlib.md5)()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def format_bytes(size: int) -> str:
    """
    Formatea un tamaño en bytes a formato legible.
    
    Args:
        size: Tamaño en bytes
        
    Returns:
        String con tamaño formateado
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def parse_json_safely(json_string: str) -> Dict[str, Any]:
    """
    Intenta parsear un string JSON de forma segura.
    
    Args:
        json_string: String con contenido JSON
        
    Returns:
        Diccionario parseado o dict vacío si falla
    """
    try:
        # Intentar extraer JSON de un texto más largo
        start = json_string.find('{')
        end = json_string.rfind('}') + 1
        
        if start != -1 and end > start:
            json_string = json_string[start:end]
        
        return json.loads(json_string)
    except json.JSONDecodeError:
        return {}


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Trunca un texto a una longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a añadir si se trunca
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_numbers_from_text(text: str) -> List[int]:
    """
    Extrae todos los números de un texto.
    
    Args:
        text: Texto a procesar
        
    Returns:
        Lista de números encontrados
    """
    import re
    return [int(n) for n in re.findall(r'\b\d+\b', text)]


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo eliminando caracteres inválidos.
    
    Args:
        filename: Nombre de archivo original
        
    Returns:
        Nombre de archivo sanitizado
    """
    # Caracteres inválidos en Windows y Unix
    invalid_chars = '<>:"/\\|?*'
    
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Eliminar espacios al inicio y final
    sanitized = sanitized.strip()
    
    # Limitar longitud
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


def get_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    Obtiene un timestamp formateado.
    
    Args:
        format_str: Formato de fecha
        
    Returns:
        Timestamp formateado
    """
    return datetime.now().strftime(format_str)


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Carga un archivo JSON.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Contenido del archivo como diccionario
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
    """
    Guarda datos en un archivo JSON.
    
    Args:
        data: Datos a guardar
        file_path: Ruta del archivo
        indent: Indentación del JSON
        
    Returns:
        True si éxito, False si error
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return True
    except Exception:
        return False


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusiona dos diccionarios de forma recursiva.
    
    Args:
        dict1: Primer diccionario
        dict2: Segundo diccionario
        
    Returns:
        Diccionario fusionado
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    Aplana una lista anidada.
    
    Args:
        nested_list: Lista posiblemente anidada
        
    Returns:
        Lista plana
    """
    flat = []
    for item in nested_list:
        if isinstance(item, list):
            flat.extend(flatten_list(item))
        else:
            flat.append(item)
    return flat


def count_words(text: str) -> int:
    """
    Cuenta el número de palabras en un texto.
    
    Args:
        text: Texto a contar
        
    Returns:
        Número de palabras
    """
    return len(text.split())


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estima el tiempo de lectura de un texto en minutos.
    
    Args:
        text: Texto a evaluar
        words_per_minute: Palabras por minuto
        
    Returns:
        Minutos estimados de lectura
    """
    word_count = count_words(text)
    return max(1, round(word_count / words_per_minute))
