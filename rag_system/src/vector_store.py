"""
Módulo para almacenamiento y recuperación vectorial.
Usa ChromaDB como base de datos vectorial persistente.

ChromaDB es recomendado porque:
- Persistencia en disco nativa
- API simple y Python-first
- Búsqueda por similitud eficiente
- Filtrado por metadatos
- Sin dependencias externas complejas
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import uuid
import chromadb
from chromadb.config import Settings
from datetime import datetime
import hashlib

# Importar tipos necesarios
import sys
sys.path.insert(0, str(Path(__file__).parent))
from chunker import Chunk


class VectorDatabase:
    """
    Wrapper alrededor de ChromaDB para operaciones RAG.

    Proporciona:
    - Persistencia automática en disco
    - Búsqueda por similitud coseno
    - Filtrado por metadatos
    - Actualización incremental (agregar nuevos documentos)
    """

    def __init__(self, db_path: str, collection_name: str = "rag_documents"):
        """
        Inicializa la base de datos vectorial.

        Args:
            db_path: Ruta al directorio de persistencia
            collection_name: Nombre de la colección
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name

        # Crear directorio si no existe
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Configurar cliente persistente
        print(f"Inicializando ChromaDB en: {db_path}")
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Obtener o crear colección
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Similitud coseno
        )

        print(f"Colección '{collection_name}': {self.collection.count()} documentos")

    def _generate_unique_id(self, base_id: str, content: str = "") -> str:
        """
        Genera un ID único combinando el base_id con un UUID.

        Args:
            base_id: ID base (generalmente del chunk)
            content: Contenido para generar hash adicional

        Returns:
            ID único
        """
        # Usar timestamp + uuid para garantizar unicidad
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        unique_suffix = uuid.uuid4().hex[:8]

        # Si hay contenido, generar hash para detectar duplicados
        if content:
            content_hash = hashlib.md5(content[:100].encode()).hexdigest()[:8]
            return f"{base_id}_{content_hash}_{timestamp}_{unique_suffix}"
        else:
            return f"{base_id}_{timestamp}_{unique_suffix}"

    def document_exists(self, doc_id: str) -> bool:
        """
        Verifica si un documento ya existe en la colección.

        Args:
            doc_id: ID del documento a verificar

        Returns:
            True si existe, False en caso contrario
        """
        try:
            result = self.collection.get(ids=[doc_id])
            return len(result['ids']) > 0
        except:
            return False

    def add_documents(
        self,
        embeddings: List[np.ndarray],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        force_unique: bool = True
    ):
        """
        Agrega documentos a la base de datos vectorial.

        Args:
            embeddings: Lista de embeddings (numpy arrays)
            documents: Lista de textos de los chunks
            metadatas: Lista de diccionarios con metadatos
            ids: IDs únicos para cada documento (opcional)
            force_unique: Si True, genera IDs únicos automáticamente
        """
        if ids is None:
            # Generar IDs únicos basados en el contenido
            ids = []
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                base_id = meta.get('chunk_id', f"chunk_{i}")
                unique_id = self._generate_unique_id(base_id, doc)
                ids.append(unique_id)
        elif force_unique:
            # Forzar unicidad incluso si se proporcionaron IDs
            new_ids = []
            for i, (doc, doc_id) in enumerate(zip(documents, ids)):
                if self.document_exists(doc_id):
                    # Si el ID ya existe, generar uno nuevo
                    base_id = doc_id
                    new_id = self._generate_unique_id(base_id, doc)
                    new_ids.append(new_id)
                    print(f"⚠️ ID duplicado '{doc_id}', generando nuevo: '{new_id}'")
                else:
                    new_ids.append(doc_id)
            ids = new_ids

        # Convertir embeddings a listas (ChromaDB requiere listas, no arrays)
        embeddings_list = [emb.tolist() if isinstance(emb, np.ndarray) else emb
                          for emb in embeddings]

        # Validar que todos tengan la misma longitud
        assert len(embeddings_list) == len(documents) == len(metadatas) == len(ids)

        # Verificar duplicados finales
        id_set = set()
        duplicate_ids = []
        for doc_id in ids:
            if doc_id in id_set:
                duplicate_ids.append(doc_id)
            else:
                id_set.add(doc_id)

        if duplicate_ids:
            print(f"⚠️ ADVERTENCIA: IDs duplicados encontrados en la misma lista: {duplicate_ids[:5]}")
            # Resolver duplicados añadiendo sufijos únicos
            for i, doc_id in enumerate(ids):
                if doc_id in duplicate_ids:
                    ids[i] = f"{doc_id}_{uuid.uuid4().hex[:8]}"

        # Agregar en lotes para evitar problemas de memoria
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))

            try:
                self.collection.add(
                    embeddings=embeddings_list[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )
            except chromadb.errors.DuplicateIDError as e:
                print(f"❌ Error de ID duplicado en lote {i}-{end_idx}: {e}")
                # Intentar agregar uno por uno con IDs únicos
                print("Reintentando con IDs únicos...")
                for j in range(i, end_idx):
                    try:
                        # Generar ID único usando timestamp
                        unique_id = f"{ids[j]}_{int(datetime.now().timestamp() * 1000)}_{j}"
                        self.collection.add(
                            embeddings=[embeddings_list[j]],
                            documents=[documents[j]],
                            metadatas=[metadatas[j]],
                            ids=[unique_id]
                        )
                    except Exception as e2:
                        print(f"❌ Error agregando documento {j}: {e2}")

        print(f"✅ Agregados {len(documents)} documentos. Total: {self.collection.count()}")

    def retrieve(
        self,
        query_embedding: np.ndarray,
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Dict[str, Any]], List[float]]:
        """
        Recupera los chunks más similares a la consulta.

        Args:
            query_embedding: Embedding de la consulta
            top_k: Número de resultados a recuperar
            filter_metadata: Filtro opcional por metadatos

        Returns:
            Tupla con (documentos, metadatos, distancias)
        """
        query_emb_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding

        results = self.collection.query(
            query_embeddings=[query_emb_list],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )

        # Extraer resultados
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        distances = results['distances'][0] if results['distances'] else []

        # Convertir distancias a similitudes (1 - distancia para coseno)
        similarities = [1 - d for d in distances]

        return documents, metadatas, similarities

    def retrieve_with_scores(
        self,
        query_embedding: np.ndarray,
        top_k: int = 4,
        score_threshold: float = 0.5
    ) -> Tuple[List[str], List[Dict[str, Any]], List[float]]:
        """
        Recupera chunks con umbral de calidad mínimo.

        Útil para filtrar resultados poco relevantes.

        Args:
            query_embedding: Embedding de la consulta
            top_k: Número máximo de resultados
            score_threshold: Mínima similitud requerida

        Returns:
            Tupla con (documentos, metadatos, similitudes)
        """
        docs, metas, scores = self.retrieve(query_embedding, top_k * 2)  # Pedir más para filtrar

        # Filtrar por threshold
        filtered_docs = []
        filtered_metas = []
        filtered_scores = []

        for doc, meta, score in zip(docs, metas, scores):
            if score >= score_threshold:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                filtered_scores.append(score)

        # Retornar top_k después del filtrado
        return (
            filtered_docs[:top_k],
            filtered_metas[:top_k],
            filtered_scores[:top_k]
        )

    def count(self) -> int:
        """Retorna el número total de documentos en la DB."""
        return self.collection.count()

    def clear(self):
        """Elimina todos los documentos de la colección."""
        # ChromaDB no tiene método clear directo, recreamos la colección
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print("✅ Colección limpiada")

    def delete_by_metadata(self, key: str, value: Any):
        """
        Elimina documentos que coincidan con un metadato específico.

        Útil para actualizar documentos específicos.

        Args:
            key: Clave del metadato
            value: Valor a buscar
        """
        # Obtener todos los IDs que coincidan
        results = self.collection.get(
            where={key: value},
            include=[]
        )

        if results['ids']:
            self.collection.delete(ids=results['ids'])
            print(f"✅ Eliminados {len(results['ids'])} documentos")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de la base de datos.

        Returns:
            Diccionario con estadísticas
        """
        return {
            'total_documents': self.collection.count(),
            'db_path': str(self.db_path),
            'collection_name': self.collection_name
        }


def store_in_vector_db(
    embeddings: List[np.ndarray],
    chunks: List[Chunk],
    db_path: str,
    collection_name: str = "rag_documents"
) -> VectorDatabase:
    """
    Almacena embeddings y chunks en la base de datos vectorial.

    Función principal para poblar la vector DB.

    Args:
        embeddings: Lista de embeddings
        chunks: Lista de chunks con contenido y metadatos
        db_path: Ruta para persistencia
        collection_name: Nombre de la colección

    Returns:
        Instancia de VectorDatabase
    """
    # Inicializar DB
    db = VectorDatabase(db_path=db_path, collection_name=collection_name)

    # Preparar datos
    documents = [chunk.content for chunk in chunks]
    metadatas = []
    ids = []

    for chunk in chunks:
        meta = {
            **chunk.metadata,
            'chunk_id': chunk.chunk_id,
            'start_char': chunk.start_char,
            'end_char': chunk.end_char,
        }
        metadatas.append(meta)
        ids.append(chunk.chunk_id)

    # Almacenar - ahora con manejo automático de duplicados
    db.add_documents(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        force_unique=True  # Forzar IDs únicos
    )

    return db


def retrieve_context(
    db: VectorDatabase,
    query_embedding: np.ndarray,
    top_k: int = 4,
    score_threshold: float = 0.3
) -> Tuple[List[str], List[Dict[str, Any]], List[float]]:
    """
    Recupera contexto relevante para una consulta.

    Función principal para retrieval en el pipeline RAG.

    Args:
        db: Instancia de VectorDatabase
        query_embedding: Embedding de la consulta
        top_k: Número de chunks a recuperar
        score_threshold: Mínima similitud requerida

    Returns:
        Tupla con (documentos, metadatos, scores)
    """
    return db.retrieve_with_scores(
        query_embedding=query_embedding,
        top_k=top_k,
        score_threshold=score_threshold
    )
