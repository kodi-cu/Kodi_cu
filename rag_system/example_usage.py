#!/usr/bin/env python3
"""
Script de ejemplo para usar el sistema RAG.
Muestra cómo indexar documentos y hacer consultas programáticamente.
"""

import sys
from pathlib import Path

# Agregar ruta al path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import RAGPipeline


def main():
    """Ejemplo completo de uso del sistema RAG."""
    
    print("="*60)
    print("EJEMPLO DE USO DEL SISTEMA RAG")
    print("="*60)
    
    # Paso 1: Inicializar el pipeline
    print("\n[1/4] Inicializando pipeline...")
    pipeline = RAGPipeline()
    
    # Paso 2: Indexar documentos de ejemplo
    print("\n[2/4] Indexando documentos de ejemplo...")
    docs_directory = str(Path(__file__).parent / "docs")
    
    stats = pipeline.index_documents(
        directory=docs_directory,
        file_types=['md', 'txt'],
        clear_existing=True  # Limpiar DB previa para este ejemplo
    )
    
    if "error" in stats:
        print(f"Error: {stats['error']}")
        return
    
    print(f"✓ Documentos indexados: {stats['documents_loaded']}")
    print(f"✓ Chunks creados: {stats['chunks_created']}")
    
    # Paso 3: Hacer consultas de ejemplo
    print("\n[3/4] Realizando consultas de ejemplo...")
    
    preguntas = [
        "¿Qué es Python?",
        "¿Cuáles son las características principales de Python?",
        "¿Qué frameworks web existen para Python?"
    ]
    
    for i, pregunta in enumerate(preguntas, 1):
        print(f"\n{'-'*60}")
        print(f"Consulta {i}: {pregunta}")
        print('-'*60)
        
        result = pipeline.query(
            question=pregunta,
            temperature=0.7,
            max_tokens=256,
            include_sources=True
        )
        
        print(f"\nRespuesta:\n{result['answer']}")
        
        if result.get('sources'):
            print(f"\nFuentes consultadas:")
            for j, (source, score) in enumerate(zip(result['sources'], result['scores']), 1):
                print(f"  [{j}] {Path(source).name} (score: {score:.3f})")
    
    # Paso 4: Mostrar estadísticas finales
    print("\n[4/4] Estadísticas finales...")
    stats = pipeline.get_statistics()
    
    print(f"\n📊 Base de Datos Vectorial:")
    print(f"   Total chunks: {stats['vector_db']['total_documents']}")
    print(f"   Ruta: {stats['vector_db']['db_path']}")
    
    print(f"\n⚙️ Configuración:")
    print(f"   Modelo: {stats['config']['model_path']}")
    print(f"   Embeddings: {stats['config']['embedding_model']}")
    print(f"   Chunk size: {stats['config']['chunk_size']} tokens")
    
    print("\n" + "="*60)
    print("EJEMPLO COMPLETADO EXITOSAMENTE")
    print("="*60)
    
    print("\n💡 Próximos pasos:")
    print("   1. Agrega tus propios documentos a ./docs/")
    print("   2. Ejecuta: python cli.py index ./docs")
    print("   3. Consulta: python cli.py query --interactive")
    print("   4. O usa la API: uvicorn api:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
