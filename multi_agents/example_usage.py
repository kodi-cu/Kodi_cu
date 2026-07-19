#!/usr/bin/env python3
"""
Ejemplo de uso del sistema multi-agente de gestión documental

Este script demuestra cómo usar los agentes individualmente y a través del orquestador.
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from agents import (
    FileFinderAgent,
    DocumentReaderAgent,
    DocumentClassifierAgent,
    DocumentAnalyzerAgent,
    DocumentManagerAgent,
    AgentOrchestrator
)


def setup_client():
    """Configura el cliente OpenAI para llama.cpp local"""
    try:
        client = OpenAI(
            base_url="http://localhost:8081/v1",
            api_key="sk-no-key-required"
        )
        # Test de conexión
        client.models.list()
        print("✓ Conectado al servidor LLM")
        return client
    except Exception as e:
        print(f"⚠ No hay servidor LLM disponible: {str(e)}")
        print("  Continuando en modo limitado (sin funciones que requieren LLM)")
        return None


def example_file_finder():
    """Ejemplo: Agente buscador de archivos"""
    print("\n" + "="*60)
    print("🔍 EJEMPLO: FileFinderAgent")
    print("="*60)
    
    finder = FileFinderAgent(search_paths=["./documents", "./"])
    
    # Búsqueda simple
    print("\nBuscando archivos PDF...")
    results = finder.search("pdf")
    print(f"Encontrados: {len(results)} archivos")
    
    for file in results[:5]:
        print(f"  - {file['name']} ({file['size_human']})")
    
    # Ver estadísticas
    stats = finder.get_stats()
    print(f"\nCache size: {stats['cache_size']}")
    print(f"Extensiones soportadas: {len(stats['supported_extensions'])}")


def example_document_reader():
    """Ejemplo: Agente lector de documentos"""
    print("\n" + "="*60)
    print("📖 EJEMPLO: DocumentReaderAgent")
    print("="*60)
    
    reader = DocumentReaderAgent()
    
    # Crear un archivo de prueba
    test_file = Path("./test_document.txt")
    test_file.write_text("""
    Este es un documento de prueba para demostrar la lectura.
    Contiene información sobre contratos y aspectos legales.
    La fecha del contrato es 15 de enero de 2024.
    Las partes involucradas son Empresa ABC y Cliente XYZ.
    """)
    
    print(f"\nLeyendo archivo: {test_file}")
    result = reader.read(test_file)
    
    if result.get('success'):
        print(f"Tipo: {result['type']}")
        print(f"Contenido (preview): {result['content'][:100]}...")
        print(f"Líneas: {result['metadata'].get('lines', 'N/A')}")
    
    # Limpiar
    test_file.unlink()


def example_document_classifier():
    """Ejemplo: Agente clasificador con optimización heurística"""
    print("\n" + "="*60)
    print("🏷️ EJEMPLO: DocumentClassifierAgent")
    print("="*60)
    
    classifier = DocumentClassifierAgent(llm_client=None)  # Sin LLM para demostración
    
    # Texto claramente legal
    legal_text = """
    CONTRATO DE SERVICIOS PROFESIONALES
    
    Entre Empresa ABC S.A., sociedad constituida bajo las leyes,
    con domicilio en Madrid, y el licenciado Juan Pérez, abogado
    en ejercicio, acuerdan las siguientes cláusulas:
    
    PRIMERA: El prestador se obliga a proporcionar servicios jurídicos.
    SEGUNDA: La contraprestación económica será de 5000 euros.
    TERCERA: Vigencia del contrato por 12 meses.
    """
    
    print("\nClasificando documento LEGAL (texto claro)...")
    result = classifier.classify(legal_text)
    print(f"Categoría: {result['category']}")
    print(f"Confianza: {result['confidence']*100:.1f}%")
    print(f"Método: {result['method']}")
    print(f"¿Usó LLM?: {'Sí' if result.get('llm_used') else 'No'} ✓")
    print(f"Keywords encontradas: {result.get('keywords_matched', [])[:5]}")
    
    # Texto ambiguo (requeriría LLM en producción)
    ambiguous_text = "Informe mensual de actividades del departamento"
    
    print("\nClasificando documento AMBIGUO...")
    result = classifier.classify(ambiguous_text)
    print(f"Categoría: {result['category']}")
    print(f"Confianza: {result['confidence']*100:.1f}%")
    print(f"Método: {result['method']}")


def example_orchestrator():
    """Ejemplo: Orquestador coordinando múltiples agentes"""
    print("\n" + "="*60)
    print("🎼 EJEMPLO: AgentOrchestrator")
    print("="*60)
    
    llm_client = setup_client()
    
    orchestrator = AgentOrchestrator(
        llm_client=llm_client,
        search_paths=["./documents", "./"],
        output_dir="./output"
    )
    
    # Ejemplo 1: Búsqueda (no requiere LLM)
    print("\n1. Búsqueda de archivos PDF:")
    result = orchestrator.execute("busca todos los pdf")
    print(f"   Intención detectada: {result['intention']}")
    print(f"   Archivos encontrados: {result.get('files_found', 0)}")
    print(f"   ¿Requirió LLM? No ✓")
    
    # Ejemplo 2: Clasificación (puede evitar LLM si confianza alta)
    print("\n2. Clasificación de documento:")
    result = orchestrator.execute("clasifica este documento legal")
    print(f"   Intención detectada: {result['intention']}")
    if 'category' in result:
        print(f"   Categoría: {result['category']}")
        print(f"   ¿Usó LLM?: {'Sí' if result.get('llm_used') else 'No'}")
    
    # Mostrar estadísticas de optimización
    print("\n3. Estadísticas de optimización:")
    stats = orchestrator.get_stats()
    print(f"   Cache de intenciones: {stats['cache_size']}/{stats['max_cache_size']}")
    print(f"   Acciones soportadas: {len(stats['supported_actions'])}")
    
    savings = orchestrator._estimate_llm_savings()
    print(f"   Ahorro estimado: ~{savings['estimated_savings_percent']}% menos llamadas al LLM")


def example_create_and_organize():
    """Ejemplo: Crear y organizar documentos"""
    print("\n" + "="*60)
    print("📝 EJEMPLO: DocumentManagerAgent")
    print("="*60)
    
    manager = DocumentManagerAgent(output_dir="./output")
    
    # Crear documento
    print("\n1. Creando documento Markdown...")
    content = """# Reporte de Prueba
    
    Este es un reporte generado automáticamente.
    
    ## Sección 1
    Contenido de la primera sección.
    
    ## Sección 2
    Contenido de la segunda sección.
    """
    
    result = manager.create_document(
        content=content,
        filename="reporte_prueba",
        format="md"
    )
    
    if result.get('success'):
        print(f"   ✓ Documento creado: {result['filename']}")
        print(f"   Ruta: {result['path']}")
        print(f"   Tamaño: {result['size']} bytes")
    
    # Crear backup
    print("\n2. Creando backup del directorio actual...")
    result = manager.backup_directory("./", "ejemplo_backup")
    if result.get('success'):
        print(f"   ✓ Backup creado: {result['backup_path']}")
        print(f"   Archivos respaldados: {result['files_count']}")


def main():
    """Ejecuta todos los ejemplos"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     SISTEMA MULTI-AGENTE - DEMOSTRACIÓN                   ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Ejecutar ejemplos
    example_file_finder()
    example_document_reader()
    example_document_classifier()
    example_orchestrator()
    example_create_and_organize()
    
    print("\n" + "="*60)
    print("✅ TODOS LOS EJEMPLOS COMPLETADOS")
    print("="*60)
    print("""
Próximos pasos:
1. Inicia el servidor llama.cpp: ./llama-server -m modelo.gguf --port 8081
2. Ejecuta el CLI interactivo: python cli.py
3. Explora la documentación en README.md
    """)


if __name__ == "__main__":
    main()
