"""
Sistema de logging para el agente PDF.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(name: str = "pdf_agent", 
                 log_file: Optional[str] = None,
                 level: int = logging.INFO) -> logging.Logger:
    """
    Configura y retorna un logger para la aplicación.
    
    Args:
        name: Nombre del logger
        log_file: Ruta al archivo de log (None para solo consola)
        level: Nivel de logging
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicar handlers si ya está configurado
    if logger.handlers:
        return logger
    
    # Formato del log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "pdf_agent") -> logging.Logger:
    """
    Obtiene una instancia de logger existente o crea una nueva.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger
    """
    return logging.getLogger(name)


class LoggerContext:
    """Contexto para logging con información adicional."""
    
    def __init__(self, logger: logging.Logger, context: dict):
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def add_context(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(add_context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_with_context(logger: logging.Logger, level: int, message: str, context: dict):
    """
    Loguea un mensaje con contexto adicional.
    
    Args:
        logger: Logger a usar
        level: Nivel de log
        message: Mensaje a loguear
        context: Diccionario con contexto adicional
    """
    with LoggerContext(logger, context):
        logger.log(level, message)
