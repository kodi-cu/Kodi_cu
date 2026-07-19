#!/usr/bin/env python3
"""
CLI para el sistema RAG.
Permite indexar documentos y hacer consultas desde la terminal.
"""

import argparse
import sys
from pathlib import Path

# Agregar ruta al path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import RAGPipeline

def cmd_index(args):
    """Comando para indexar documentos."""
    pipeline = RAGPipeline(
        n_gpu_layers=args.gpu_layers if args.gpu_layers is not None else None,
        n_threads=args.threads if args.threads is not None else None,
    )
    
    stats = pipeline.index_documents(
        directory=args.directory,
        file_types=args.types.split(',') if args.types else None,
        clear_existing=args.clear
    )
    
    if "error" in stats:
        print(f"Error: {stats['error']}")
        sys.exit(1)
    
    print("\n✓ Indexación completada exitosamente")


def cmd_query(args):
    """Comando para hacer consultas."""
    pipeline = RAGPipeline(
        n_gpu_layers=args.gpu_layers if args.gpu_layers is not None else None,
        n_threads=args.threads if args.threads is not None else None,
    )
    
    if args.question:
        # Consulta única
        result = pipeline.query(
            question=args.question,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            include_sources=not args.no_sources
        )
        
        print("\n" + "="*60)
        print("RESPUESTA:")
        print("="*60)
        print(result["answer"])
        
        if not args.no_sources and result.get('sources'):
            print("\n" + "-"*40)
            print("FUENTES:")
            for i, (source, score) in enumerate(zip(result['sources'], result['scores']), 1):
                print(f"  [{i}] {source} (score: {score:.3f})")
    
    elif args.interactive:
        # Modo interactivo
        print("\n" + "="*60)
        print("MODO INTERACTIVO - Escribe 'quit' para salir")
        print("="*60)
        
        while True:
            try:
                question = input("\n❓ Pregunta: ").strip()
                
                if question.lower() in ['quit', 'exit', 'salir']:
                    print("¡Hasta luego!")
                    break
                
                if not question:
                    continue
                
                result = pipeline.query(
                    question=question,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    include_sources=True
                )
                
                print("\n🤖 Respuesta:")
                print(result["answer"])
                
            except KeyboardInterrupt:
                print("\n\n¡Hasta luego!")
                break
            except Exception as e:
                print(f"\nError: {e}")
    else:
        print("Error: Debes proporcionar una pregunta con -q o usar --interactive")
        sys.exit(1)


def cmd_stats(args):
    """Comando para mostrar estadísticas."""
    pipeline = RAGPipeline()
    stats = pipeline.get_statistics()
    
    print("\n" + "="*60)
    print("ESTADÍSTICAS DEL SISTEMA RAG")
    print("="*60)
    
    print("\n📊 Base de Datos Vectorial:")
    print(f"   Total de chunks: {stats['vector_db']['total_documents']}")
    print(f"   Ruta: {stats['vector_db']['db_path']}")
    
    print("\n⚙️ Configuración:")
    print(f"   Modelo LLM: {stats['config']['model_path']}")
    print(f"   Embeddings: {stats['config']['embedding_model']}")
    print(f"   Chunk size: {stats['config']['chunk_size']} tokens")
    print(f"   Top-K: {stats['config']['top_k']}")
    print(f"   GPU layers: {stats['config']['n_gpu_layers']}")


def main():
    parser = argparse.ArgumentParser(
        description="Sistema RAG local para pregunta-respuesta con documentos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s index ./docs                      # Indexar documentos
  %(prog)s index ./docs --clear              # Indexar limpiando DB previa
  %(prog)s query -q "¿Qué es Python?"        # Hacer consulta
  %(prog)s query --interactive               # Modo interactivo
  %(prog)s stats                             # Ver estadísticas
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando INDEX
    parser_index = subparsers.add_parser('index', help='Indexar documentos')
    parser_index.add_argument('directory', help='Directorio con documentos')
    parser_index.add_argument('--types', '-t', help='Tipos de archivo (ej: pdf,txt,md)')
    parser_index.add_argument('--clear', '-c', action='store_true', 
                             help='Limpiar DB existente antes de indexar')
    parser_index.add_argument('--gpu-layers', type=int, 
                             help='Capas a offload a GPU')
    parser_index.add_argument('--threads', type=int, 
                             help='Número de hilos CPU')
    parser_index.set_defaults(func=cmd_index)
    
    # Comando QUERY
    parser_query = subparsers.add_parser('query', help='Hacer consultas')
    parser_query.add_argument('--question', '-q', help='Pregunta a realizar')
    parser_query.add_argument('--interactive', '-i', action='store_true',
                             help='Modo interactivo')
    parser_query.add_argument('--temperature', type=float, default=0.7,
                             help='Temperatura de generación (0.0-1.0)')
    parser_query.add_argument('--max-tokens', type=int, default=512,
                             help='Máximo de tokens a generar')
    parser_query.add_argument('--no-sources', action='store_true',
                             help='No mostrar fuentes')
    parser_query.add_argument('--gpu-layers', type=int,
                             help='Capas a offload a GPU')
    parser_query.add_argument('--threads', type=int,
                             help='Número de hilos CPU')
    parser_query.set_defaults(func=cmd_query)
    
    # Comando STATS
    parser_stats = subparsers.add_parser('stats', help='Mostrar estadísticas')
    parser_stats.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == '__main__':
    main()
