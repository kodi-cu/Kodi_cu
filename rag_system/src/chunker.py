"""
Módulo para chunking de documentos.
Implementa estrategias inteligentes de división de texto.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

# Importar Document del loader
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from document_loader import Document


@dataclass
class Chunk:
    """Representa un fragmento de documento."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    start_char: int
    end_char: int
    
    def __len__(self) -> int:
        """Retorna el número aproximado de tokens (estimado por caracteres)."""
        return len(self.content) // 4  # Aproximación: 1 token ≈ 4 caracteres


def count_tokens(text: str) -> int:
    """
    Cuenta el número aproximado de tokens en un texto.
    
    Nota: Esta es una estimación. Para conteo exacto, usar el tokenizer
    específico del modelo (ej: llama-cpp-python tiene métodos para esto).
    
    Args:
        text: Texto a contar
        
    Returns:
        Número estimado de tokens
    """
    # Aproximación común: 1 token ≈ 4 caracteres en inglés
    # Para español puede variar ligeramente
    return len(text) // 4


def split_by_paragraphs(text: str) -> List[str]:
    """
    Divide el texto por párrafos (doble salto de línea).
    
    Útil para mantener coherencia semántica dentro de cada chunk.
    
    Args:
        text: Texto completo
        
    Returns:
        Lista de párrafos
    """
    # Dividir por dobles saltos de línea
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def split_by_sentences(text: str) -> List[str]:
    """
    Divide el texto por oraciones.
    
    Más granular que párrafos, útil para chunks más pequeños.
    
    Args:
        text: Texto completo
        
    Returns:
        Lista de oraciones
    """
    # Patrón para dividir por oraciones (punto, signo de interrogación, exclamación)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def create_chunks_recursive(
    text: str,
    max_tokens: int,
    metadata: Dict[str, Any],
    start_char: int = 0
) -> List[Chunk]:
    """
    Crea chunks recursivamente, intentando mantener límites semánticos.
    
    Estrategia:
    1. Si el texto cabe en max_tokens, crear un solo chunk
    2. Si no, intentar dividir por párrafos
    3. Si los párrafos son muy grandes, dividir por oraciones
    4. Si aún son muy grandes, dividir por espacio
    
    Esta estrategia preserva mejor el contexto que una división fija.
    
    Args:
        text: Texto a dividir
        max_tokens: Máximo de tokens por chunk
        metadata: Metadatos base para todos los chunks
        start_char: Posición inicial en el documento original
        
    Returns:
        Lista de chunks
    """
    chunks = []
    max_chars = max_tokens * 4  # Convertir tokens a caracteres aproximados
    
    # Caso base: el texto cabe en un chunk
    if count_tokens(text) <= max_tokens:
        chunk = Chunk(
            content=text,
            metadata=metadata.copy(),
            chunk_id=f"{metadata.get('doc_id', 'unknown')}_{len(chunks)}",
            start_char=start_char,
            end_char=start_char + len(text)
        )
        return [chunk]
    
    # Intentar dividir por párrafos
    paragraphs = split_by_paragraphs(text)
    
    if len(paragraphs) > 1:
        current_chunk = ""
        current_start = start_char
        paragraph_positions = []
        
        # Reconstruir posiciones
        pos = start_char
        for para in paragraphs:
            paragraph_positions.append((pos, pos + len(para)))
            pos += len(para) + 2  # +2 para los saltos de línea
        
        idx = 0
        for i, para in enumerate(paragraphs):
            if count_tokens(current_chunk + para) <= max_tokens:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunk = Chunk(
                        content=current_chunk.strip(),
                        metadata=metadata.copy(),
                        chunk_id=f"{metadata.get('doc_id', 'unknown')}_{len(chunks)}",
                        start_char=current_start,
                        end_char=current_start + len(current_chunk)
                    )
                    chunks.append(chunk)
                
                # Si el párrafo individual es muy grande, dividir recursivamente
                if count_tokens(para) > max_tokens:
                    sub_chunks = create_chunks_recursive(
                        para,
                        max_tokens,
                        metadata,
                        paragraph_positions[i][0]
                    )
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                    current_start = paragraph_positions[i][1]
                else:
                    current_chunk = para + "\n\n"
                    current_start = paragraph_positions[i][0]
        
        # Agregar último chunk
        if current_chunk.strip():
            chunk = Chunk(
                content=current_chunk.strip(),
                metadata=metadata.copy(),
                chunk_id=f"{metadata.get('doc_id', 'unknown')}_{len(chunks)}",
                start_char=current_start,
                end_char=current_start + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    # Si no hay párrafos, intentar con oraciones
    sentences = split_by_sentences(text)
    
    if len(sentences) > 1:
        current_chunk = ""
        current_start = start_char
        
        for sentence in sentences:
            if count_tokens(current_chunk + sentence) <= max_tokens:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunk = Chunk(
                        content=current_chunk.strip(),
                        metadata=metadata.copy(),
                        chunk_id=f"{metadata.get('doc_id', 'unknown')}_{len(chunks)}",
                        start_char=current_start,
                        end_char=current_start + len(current_chunk)
                    )
                    chunks.append(chunk)
                
                current_chunk = sentence + " "
                current_start = text.find(sentence, current_start)
        
        if current_chunk.strip():
            chunk = Chunk(
                content=current_chunk.strip(),
                metadata=metadata.copy(),
                chunk_id=f"{metadata.get('doc_id', 'unknown')}_{len(chunks)}",
                start_char=current_start,
                end_char=current_start + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    # Último recurso: dividir por espacio (chunks fijos)
    words = text.split()
    current_chunk = ""
    current_start = start_char
    
    for word in words:
        if count_tokens(current_chunk + word) <= max_tokens:
            current_chunk += word + " "
        else:
            if current_chunk:
                chunk = Chunk(
                    content=current_chunk.strip(),
                    metadata=metadata.copy(),
                    chunk_id=f"{metadata.get('doc_id', 'unknown')}_{len(chunks)}",
                    start_char=current_start,
                    end_char=current_start + len(current_chunk)
                )
                chunks.append(chunk)
            
            current_chunk = word + " "
            # Encontrar posición aproximada
            current_start = text.find(word, current_start)
    
    if current_chunk.strip():
        chunk = Chunk(
            content=current_chunk.strip(),
            metadata=metadata.copy(),
            chunk_id=f"{metadata.get('doc_id', 'unknown')}_{len(chunks)}",
            start_char=current_start,
            end_char=current_start + len(current_chunk)
        )
        chunks.append(chunk)
    
    return chunks


def create_chunks(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Chunk]:
    """
    Crea chunks a partir de documentos con solapamiento.
    
    Estrategia recomendada para documentos largos:
    - Usar chunk_size ~500 tokens para balance entre contexto y precisión
    - Usar chunk_overlap ~50 tokens (10%) para mantener continuidad
    - El solapamiento ayuda a que información importante no se pierda
      en los límites de chunks
    
    Manejo de tablas y listas:
    - Las tablas en texto plano se mantienen juntas si es posible
    - Las listas con viñetas/numeración se preservan dentro de chunks
    - Para tablas complejas, considerar pre-procesamiento especial
    
    Args:
        documents: Lista de documentos
        chunk_size: Tamaño máximo de chunk en tokens
        chunk_overlap: Solapamiento entre chunks en tokens
        
    Returns:
        Lista de chunks
    """
    all_chunks = []
    
    for doc in documents:
        # Primero crear chunks sin solapamiento
        doc_chunks = create_chunks_recursive(
            text=doc.content,
            max_tokens=chunk_size,
            metadata=doc.metadata
        )
        
        # Aplicar solapamiento si es necesario
        if chunk_overlap > 0 and len(doc_chunks) > 1:
            overlapped_chunks = []
            overlap_chars = chunk_overlap * 4  # Convertir a caracteres
            
            for i, chunk in enumerate(doc_chunks):
                if i == 0:
                    # Primer chunk: agregar solapamiento al final
                    if len(doc_chunks) > 1:
                        next_chunk_start = doc_chunks[i + 1].start_char
                        # Extender hasta incluir parte del siguiente chunk
                        extended_end = min(
                            chunk.end_char + overlap_chars,
                            next_chunk_start + (doc_chunks[i + 1].end_char - next_chunk_start) // 2
                        )
                        extended_content = doc.content[chunk.start_char:extended_end]
                        
                        overlapped_chunk = Chunk(
                            content=extended_content,
                            metadata=chunk.metadata.copy(),
                            chunk_id=chunk.chunk_id,
                            start_char=chunk.start_char,
                            end_char=extended_end
                        )
                        overlapped_chunks.append(overlapped_chunk)
                    else:
                        overlapped_chunks.append(chunk)
                elif i == len(doc_chunks) - 1:
                    # Último chunk: mantener solapamiento del anterior
                    prev_chunk_end = doc_chunks[i - 1].end_char
                    extended_start = max(chunk.start_char - overlap_chars, prev_chunk_end - overlap_chars)
                    extended_content = doc.content[extended_start:chunk.end_char]
                    
                    overlapped_chunk = Chunk(
                        content=extended_content,
                        metadata=chunk.metadata.copy(),
                        chunk_id=chunk.chunk_id,
                        start_char=extended_start,
                        end_char=chunk.end_char
                    )
                    overlapped_chunks.append(overlapped_chunk)
                else:
                    # Chunks intermedios: solapamiento en ambos lados
                    prev_overlap_start = max(
                        chunk.start_char - overlap_chars,
                        doc_chunks[i - 1].start_char + (chunk.start_char - doc_chunks[i - 1].start_char) // 2
                    )
                    next_overlap_end = min(
                        chunk.end_char + overlap_chars,
                        doc_chunks[i + 1].end_char - (doc_chunks[i + 1].end_char - chunk.end_char) // 2
                    )
                    extended_content = doc.content[prev_overlap_start:next_overlap_end]
                    
                    overlapped_chunk = Chunk(
                        content=extended_content,
                        metadata=chunk.metadata.copy(),
                        chunk_id=chunk.chunk_id,
                        start_char=prev_overlap_start,
                        end_char=next_overlap_end
                    )
                    overlapped_chunks.append(overlapped_chunk)
            
            all_chunks.extend(overlapped_chunks)
        else:
            all_chunks.extend(doc_chunks)
    
    print(f"Total de chunks creados: {len(all_chunks)}")
    return all_chunks


def merge_small_chunks(
    chunks: List[Chunk],
    min_tokens: int = 100,
    max_tokens: int = 500
) -> List[Chunk]:
    """
    Fusiona chunks pequeños adyacentes para evitar fragmentación excesiva.
    
    Útil cuando el chunking produce muchos fragments muy pequeños.
    
    Args:
        chunks: Lista de chunks
        min_tokens: Tamaño mínimo deseado
        max_tokens: Tamaño máximo permitido
        
    Returns:
        Lista de chunks fusionados
    """
    if not chunks:
        return []
    
    merged = []
    current_content = chunks[0].content
    current_start = chunks[0].start_char
    current_metadata = chunks[0].metadata.copy()
    
    for i in range(1, len(chunks)):
        chunk = chunks[i]
        
        # Verificar si fusionar
        combined_tokens = count_tokens(current_content + " " + chunk.content)
        
        if combined_tokens <= max_tokens and count_tokens(current_content) < min_tokens:
            # Fusionar
            current_content += " " + chunk.content
            current_metadata['merged_from'] = current_metadata.get('merged_from', []) + [chunk.chunk_id]
        else:
            # Guardar chunk actual y comenzar nuevo
            merged_chunk = Chunk(
                content=current_content,
                metadata=current_metadata,
                chunk_id=f"merged_{len(merged)}",
                start_char=current_start,
                end_char=current_start + len(current_content)
            )
            merged.append(merged_chunk)
            
            current_content = chunk.content
            current_start = chunk.start_char
            current_metadata = chunk.metadata.copy()
    
    # Agregar último chunk
    merged_chunk = Chunk(
        content=current_content,
        metadata=current_metadata,
        chunk_id=f"merged_{len(merged)}",
        start_char=current_start,
        end_char=current_start + len(current_content)
    )
    merged.append(merged_chunk)
    
    return merged
