"""
Módulo para generación y gestión de embeddings.
Usa sentence-transformers para embeddings locales.
Incluye sistema de caché para evitar reprocesamiento.
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

import numpy as np
from sentence_transformers import SentenceTransformer

# Importar Chunk del chunker
import sys
sys.path.insert(0, str(Path(__file__).parent))
from chunker import Chunk


class EmbeddingCache:
    """
    Sistema de caché para embeddings.
    
    Evita generar embeddings repetidos para el mismo contenido,
    lo cual es útil cuando:
    - Se agregan nuevos documentos (solo procesar los nuevos)
    - Se reinicia el sistema (no reprocesar todo)
    """
    
    def __init__(self, cache_path: str):
        self.cache_path = Path(cache_path)
        self.cache: Dict[str, np.ndarray] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Carga el caché desde disco si existe."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'rb') as f:
                    self.cache = pickle.load(f)
                print(f"Caché cargado: {len(self.cache)} embeddings")
            except Exception as e:
                print(f"Error cargando caché: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Guarda el caché en disco."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache, f)
        print(f"Caché guardado: {len(self.cache)} embeddings")
    
    def _get_key(self, text: str) -> str:
        """Genera una clave única para el texto."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """Obtiene embedding del caché si existe."""
        key = self._get_key(text)
        return self.cache.get(key)
    
    def set(self, text: str, embedding: np.ndarray):
        """Guarda embedding en el caché."""
        key = self._get_key(text)
        self.cache[key] = embedding
    
    def has(self, text: str) -> bool:
        """Verifica si el texto ya tiene embedding en caché."""
        return self._get_key(text) in self.cache


class EmbeddingGenerator:
    """
    Generador de embeddings usando sentence-transformers.
    
    Modelo recomendado: all-MiniLM-L6-v2
    - 384 dimensiones
    - Rápido en CPU
    - Buen balance calidad/rendimiento
    - Soporte multilingüe (incluye español)
    
    Alternativas:
    - all-mpnet-base-v2: Mejor calidad, más lento
    - paraphrase-multilingual-MiniLM-L12-v2: Mejor para múltiples idiomas
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_path: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Inicializa el generador de embeddings.
        
        Args:
            model_name: Nombre del modelo sentence-transformers
            cache_path: Ruta para guardar caché de embeddings
            device: Dispositivo ('cpu', 'cuda', etc.) o None para auto
        """
        self.model_name = model_name
        self.device = device
        
        print(f"Cargando modelo de embeddings: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"Modelo cargado. Dimensión de embeddings: {self.model.get_sentence_embedding_dimension()}")
        
        # Inicializar caché
        self.cache = EmbeddingCache(cache_path) if cache_path else None
    
    def generate_embeddings(
        self,
        texts: List[str],
        use_cache: bool = True,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[np.ndarray]:
        """
        Genera embeddings para una lista de textos.
        
        Args:
            texts: Lista de textos
            use_cache: Usar caché si está disponible
            batch_size: Tamaño de lote para procesamiento
            show_progress: Mostrar barra de progreso
            
        Returns:
            Lista de embeddings (numpy arrays)
        """
        embeddings = []
        texts_to_process = []
        indices_to_process = []
        
        # Verificar caché
        if use_cache and self.cache:
            for i, text in enumerate(texts):
                cached = self.cache.get(text)
                if cached is not None:
                    embeddings.append(cached)
                else:
                    texts_to_process.append(text)
                    indices_to_process.append(i)
        else:
            texts_to_process = texts
            indices_to_process = list(range(len(texts)))
            embeddings = [None] * len(texts)
        
        # Generar embeddings para textos no cacheados
        if texts_to_process:
            print(f"Generando {len(texts_to_process)} embeddings...")
            
            new_embeddings = self.model.encode(
                texts_to_process,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            # Guardar en caché y en la lista
            for i, (text, emb) in enumerate(zip(texts_to_process, new_embeddings)):
                if use_cache and self.cache:
                    self.cache.set(text, emb)
                    self.cache._save_cache()
                
                if indices_to_process:
                    embeddings[indices_to_process[i]] = emb
                else:
                    embeddings.append(emb)
        
        return embeddings
    
    def generate_single(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Genera embedding para un solo texto.
        
        Args:
            text: Texto a embedir
            use_cache: Usar caché si está disponible
            
        Returns:
            Embedding como numpy array
        """
        if use_cache and self.cache:
            cached = self.cache.get(text)
            if cached is not None:
                return cached
        
        embedding = self.model.encode([text], convert_to_numpy=True)[0]
        
        if use_cache and self.cache:
            self.cache.set(text, embedding)
            self.cache._save_cache()
        
        return embedding
    
    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calcula similitud coseno entre dos embeddings.
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
            
        Returns:
            Similitud coseno (0 a 1)
        """
        # Normalizar vectores
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Coseno de similitud
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # Convertir a rango 0-1 (el coseno va de -1 a 1)
        return (similarity + 1) / 2


def generate_embeddings(
    chunks: List[Chunk],
    model_name: str = "all-MiniLM-L6-v2",
    cache_path: Optional[str] = None,
    batch_size: int = 32
) -> tuple[List[np.ndarray], List[Dict[str, Any]]]:
    """
    Genera embeddings para una lista de chunks.
    
    Función principal que orquesta la generación de embeddings.
    
    Args:
        chunks: Lista de chunks a embedir
        model_name: Modelo sentence-transformers a usar
        cache_path: Ruta para caché de embeddings
        batch_size: Tamaño de lote
        
    Returns:
        Tupla con (lista de embeddings, lista de metadatos)
    """
    generator = EmbeddingGenerator(
        model_name=model_name,
        cache_path=cache_path
    )
    
    # Extraer textos de los chunks
    texts = [chunk.content for chunk in chunks]
    
    # Generar embeddings
    embeddings = generator.generate_embeddings(
        texts,
        use_cache=True,
        batch_size=batch_size
    )
    
    # Preparar metadatos para vector DB
    metadata_list = []
    for chunk, emb in zip(chunks, embeddings):
        meta = {
            **chunk.metadata,
            'chunk_id': chunk.chunk_id,
            'start_char': chunk.start_char,
            'end_char': chunk.end_char,
        }
        metadata_list.append(meta)
    
    return embeddings, metadata_list
