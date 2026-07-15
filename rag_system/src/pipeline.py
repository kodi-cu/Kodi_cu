"""
Pipeline RAG completo.
Orquesta todos los módulos para proporcionar un sistema de pregunta-respuesta.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent))

# Importar configuración
from config.settings import config

# Importar módulos del pipeline
from src.document_loader import load_documents, load_document, Document
from src.chunker import create_chunks, Chunk
from src.embeddings import generate_embeddings, EmbeddingGenerator
from src.vector_store import VectorDatabase, store_in_vector_db, retrieve_context
from src.llm import LocalLLM, create_context_string, generate_response as llm_generate


class RAGPipeline:
    """
    Pipeline RAG completo para pregunta-respuesta con documentos locales.
    
    Flujo:
    1. Carga de documentos (PDF, TXT, MD)
    2. Chunking inteligente
    3. Generación de embeddings (con caché)
    4. Almacenamiento en vector DB
    5. Recuperación de contexto relevante
    6. Generación de respuesta con LLM local
    
    El pipeline es modular y permite:
    - Indexación incremental (agregar nuevos documentos)
    - Reutilización de embeddings cacheados
    - Configuración flexible de parámetros
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        vector_db_path: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        top_k: Optional[int] = None,
        n_gpu_layers: Optional[int] = None,
        n_threads: Optional[int] = None,
    ):
        """
        Inicializa el pipeline RAG.
        
        Args:
            model_path: Ruta al modelo GGUF (override de config)
            embedding_model: Modelo sentence-transformers (override)
            vector_db_path: Ruta a vector DB (override)
            chunk_size: Tamaño de chunks (override)
            chunk_overlap: Solapamiento entre chunks (override)
            top_k: Chunks a recuperar (override)
            n_gpu_layers: Capas en GPU (override)
            n_threads: Hilos CPU (override)
        """
        # Usar configuración por defecto o valores proporcionados
        self.config = config
        
        self.model_path = model_path or self.config.model_path
        self.embedding_model = embedding_model or self.config.embedding_model
        self.vector_db_path = vector_db_path or self.config.vector_db_path
        self.chunk_size = chunk_size or self.config.chunk_size
        self.chunk_overlap = chunk_overlap or self.config.chunk_overlap
        self.top_k = top_k or self.config.top_k
        self.n_gpu_layers = n_gpu_layers if n_gpu_layers is not None else self.config.n_gpu_layers
        self.n_threads = n_threads if n_threads is not None else self.config.n_threads
        
        # Componentes inicializados bajo demanda
        self._embedding_generator = None
        self._vector_db = None
        self._llm = None
        
        print("Pipeline RAG inicializado")
        print(f"  Modelo LLM: {self.model_path}")
        print(f"  Embeddings: {self.embedding_model}")
        print(f"  Chunk size: {self.chunk_size} tokens")
        print(f"  Top-K: {self.top_k}")
    
    @property
    def embedding_generator(self) -> EmbeddingGenerator:
        """Lazy loading del generador de embeddings."""
        if self._embedding_generator is None:
            self._embedding_generator = EmbeddingGenerator(
                model_name=self.embedding_model,
                cache_path=self.config.embedding_cache_path
            )
        return self._embedding_generator
    
    @property
    def vector_db(self) -> VectorDatabase:
        """Lazy loading de la base de datos vectorial."""
        if self._vector_db is None:
            self._vector_db = VectorDatabase(
                db_path=self.vector_db_path,
                collection_name="rag_documents"
            )
        return self._vector_db
    
    @property
    def llm(self) -> LocalLLM:
        """Lazy loading del modelo LLM."""
        if self._llm is None:
            self._llm = LocalLLM(
                model_path=self.model_path,
                n_ctx=self.config.context_window,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers
            )
        return self._llm
    
    def index_documents(
        self,
        directory: str,
        file_types: List[str] = None,
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Indexa documentos desde un directorio.
        
        Proceso:
        1. Cargar documentos
        2. Crear chunks
        3. Generar embeddings
        4. Almacenar en vector DB
        
        Args:
            directory: Ruta al directorio con documentos
            file_types: Tipos de archivo a cargar
            clear_existing: Limpiar DB existente antes de indexar
            
        Returns:
            Estadísticas de indexación
        """
        print("\n" + "="*50)
        print("INDEXANDO DOCUMENTOS")
        print("="*50)
        
        # Limpiar DB si se solicita
        if clear_existing:
            print("\nLimpiando base de datos existente...")
            self.vector_db.clear()
        
        # Paso 1: Cargar documentos
        print("\n[1/4] Cargando documentos...")
        documents = load_documents(directory, file_types)
        
        if not documents:
            return {"error": "No se encontraron documentos"}
        
        # Paso 2: Crear chunks
        print("\n[2/4] Creando chunks...")
        chunks = create_chunks(
            documents=documents,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Paso 3: Generar embeddings
        print("\n[3/4] Generando embeddings...")
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_generator.generate_embeddings_simple(
            texts=texts,
            use_cache=True,
            batch_size=32
        )
        
        # Preparar metadatos
        metadata_list = []
        ids = []
        for chunk in chunks:
            meta = {
                **chunk.metadata,
                'chunk_id': chunk.chunk_id,
                'start_char': chunk.start_char,
                'end_char': chunk.end_char,
            }
            metadata_list.append(meta)
            ids.append(chunk.chunk_id)
        
        # Paso 4: Almacenar en vector DB
        print("\n[4/4] Almacenando en vector DB...")
        documents_list = [chunk.content for chunk in chunks]
        embeddings_list = [emb.tolist() if hasattr(emb, 'tolist') else emb 
                          for emb in embeddings]
        
        self.vector_db.add_documents(
            embeddings=embeddings_list,
            documents=documents_list,
            metadatas=metadata_list,
            ids=ids
        )
        
        stats = {
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "total_in_db": self.vector_db.count(),
            "cache_size": len(self.embedding_generator.cache.cache) if self.embedding_generator.cache else 0
        }
        
        print("\n" + "="*50)
        print("INDEXACIÓN COMPLETADA")
        print(f"  Documentos: {stats['documents_loaded']}")
        print(f"  Chunks: {stats['chunks_created']}")
        print(f"  Total en DB: {stats['total_in_db']}")
        print("="*50 + "\n")
        
        return stats
    
    def query(
        self,
        question: str,
        temperature: float = None,
        max_tokens: int = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Realiza una consulta al sistema RAG.
        
        Proceso:
        1. Generar embedding de la pregunta
        2. Recuperar chunks relevantes
        3. Formatear contexto
        4. Generar respuesta con LLM
        
        Args:
            question: Pregunta del usuario
            temperature: Temperatura para generación (default: config)
            max_tokens: Máximo tokens a generar (default: config)
            include_sources: Incluir fuentes en la respuesta
            
        Returns:
            Diccionario con respuesta, contexto y metadatos
        """
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        print("\n" + "="*50)
        print(f"CONSULTA: {question[:80]}...")
        print("="*50)
        
        # Paso 1: Generar embedding de la pregunta
        print("\n[1/3] Generando embedding de consulta...")
        query_embedding = self.embedding_generator.generate_single(
            text=question,
            use_cache=False  # No cachear queries individuales
        )
        
        # Paso 2: Recuperar contexto relevante
        print("[2/3] Recuperando contexto relevante...")
        documents, metadatas, scores = retrieve_context(
            db=self.vector_db,
            query_embedding=query_embedding,
            top_k=self.top_k,
            score_threshold=0.3
        )
        
        if not documents:
            return {
                "answer": "No se encontró información relevante en los documentos indexados.",
                "context": [],
                "sources": [],
                "scores": []
            }
        
        print(f"  Chunks recuperados: {len(documents)}")
        print(f"  Score máximo: {max(scores):.3f}" if scores else "")
        
        # Paso 3: Formatear contexto
        context_string = create_context_string(documents, metadatas, scores)
        
        # Paso 4: Generar respuesta con LLM
        print("[3/3] Generando respuesta con LLM...")
        answer = self.llm.generate_response(
            context=context_string,
            question=question,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Preparar resultado
        result = {
            "answer": answer,
            "context": documents,
            "sources": [meta.get('source', 'Desconocido') for meta in metadatas],
            "scores": scores,
            "metadatas": metadatas
        }
        
        if include_sources:
            sources_info = "\n\nFuentes:"
            for i, (source, score) in enumerate(zip(result['sources'], result['scores']), 1):
                sources_info += f"\n  [{i}] {source} (relevancia: {score:.2f})"
            result["answer_with_sources"] = answer + sources_info
        
        print("\n" + "="*50)
        print("RESPUESTA GENERADA")
        print("="*50)
        
        return result
    
    def rag_pipeline(
        self,
        question: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Función principal del pipeline RAG.
        
        Orquesta todo el flujo desde la consulta hasta la respuesta.
        
        Args:
            question: Pregunta del usuario
            temperature: Temperatura para generación
            max_tokens: Máximo tokens a generar
            
        Returns:
            Respuesta como string
        """
        result = self.query(
            question=question,
            temperature=temperature,
            max_tokens=max_tokens,
            include_sources=False
        )
        return result.get("answer", "Error generando respuesta")
    
    def add_new_documents(
        self,
        directory: str,
        file_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega nuevos documentos sin borrar los existentes.
        
        Útil para actualización incremental de la base de conocimiento.
        
        Args:
            directory: Directorio con nuevos documentos
            file_types: Tipos de archivo a cargar
            
        Returns:
            Estadísticas de adición
        """
        print("\n" + "="*50)
        print("AGREGANDO NUEVOS DOCUMENTOS")
        print("="*50)
        
        # Cargar documentos
        documents = load_documents(directory, file_types)
        
        if not documents:
            return {"error": "No se encontraron documentos"}
        
        # Crear chunks
        chunks = create_chunks(
            documents=documents,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Generar embeddings (usará caché si ya existen)
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_generator.generate_embeddings(
            texts=texts,
            use_cache=True
        )
        
        # Preparar datos
        metadata_list = []
        ids = []
        for chunk in chunks:
            meta = {
                **chunk.metadata,
                'chunk_id': chunk.chunk_id,
                'start_char': chunk.start_char,
                'end_char': chunk.end_char,
            }
            metadata_list.append(meta)
            ids.append(chunk.chunk_id)
        
        # Almacenar (sin limpiar DB existente)
        documents_list = [chunk.content for chunk in chunks]
        embeddings_list = [emb.tolist() if hasattr(emb, 'tolist') else emb 
                          for emb in embeddings]
        
        self.vector_db.add_documents(
            embeddings=embeddings_list,
            documents=documents_list,
            metadatas=metadata_list,
            ids=ids
        )
        
        stats = {
            "new_documents": len(documents),
            "new_chunks": len(chunks),
            "total_in_db": self.vector_db.count()
        }
        
        print(f"\nNuevos documentos: {stats['new_documents']}")
        print(f"Nuevos chunks: {stats['new_chunks']}")
        print(f"Total en DB: {stats['total_in_db']}")
        
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del sistema."""
        return {
            "vector_db": self.vector_db.get_statistics(),
            "config": {
                "model_path": self.model_path,
                "embedding_model": self.embedding_model,
                "chunk_size": self.chunk_size,
                "top_k": self.top_k,
                "n_gpu_layers": self.n_gpu_layers
            }
        }


# Funciones convenience para uso directo

def initialize_pipeline() -> RAGPipeline:
    """Inicializa el pipeline con configuración por defecto."""
    return RAGPipeline()


def index_documents(pipeline: RAGPipeline, directory: str, clear: bool = False):
    """Indexa documentos en el pipeline."""
    return pipeline.index_documents(directory, clear_existing=clear)


def ask_question(pipeline: RAGPipeline, question: str) -> str:
    """Realiza una pregunta y retorna la respuesta."""
    return pipeline.rag_pipeline(question)
