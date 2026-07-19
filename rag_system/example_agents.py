"""
Ejemplo de uso del sistema de agentes para gestión documental.

Muestra cómo configurar y usar los agentes con un LLM local via llama.cpp.
"""

import sys
from pathlib import Path

# Agregar ruta al sistema
sys.path.insert(0, str(Path(__file__).parent))


def setup_llm_client(base_url: str = "http://localhost:8081/v1", 
                     api_key: str = "sk-no-key-required"):
    """
    Configura el cliente OpenAI-compatible para el LLM local.
    
    Args:
        base_url: URL del servidor llama.cpp
        api_key: API key (no requerida para local)
        
    Returns:
        Cliente OpenAI configurado
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        
        # Verificar conexión
        models = client.models.list()
        print(f"✓ Conectado al LLM local")
        print(f"  Modelos disponibles: {[m.id for m in models.data][:3]}")
        
        return client
    except Exception as e:
        print(f"⚠ Error conectando al LLM: {e}")
        print("  Asegúrate de tener llama.cpp corriendo en el puerto especificado")
        print("  Ejemplo: ./server -m modelo.gguf --port 8081")
        return None


def example_basic_usage():
    """Ejemplo básico de uso de agentes."""
    print("\n" + "="*60)
    print("EJEMPLO BÁSICO DE USO DE AGENTES")
    print("="*60)
    
    # Configurar LLM
    llm_client = setup_llm_client()
    
    if not llm_client:
        print("\nContinuando sin LLM (funcionalidad limitada)")
    
    # Inicializar orquestador
    from agents.orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator(
        llm_client=llm_client,
        base_directory="."  # Directorio actual
    )
    
    # Ejemplo 1: Buscar archivos PDF
    print("\n--- Ejemplo 1: Buscar archivos PDF ---")
    result = orchestrator.process_instruction("Busca todos los archivos PDF en el directorio")
    print(f"Archivos encontrados: {result.get('files_found', 0)}")
    if result.get('files'):
        for f in result['files'][:3]:
            print(f"  - {f['name']} ({f['size_kb']} KB)")
    
    # Ejemplo 2: Leer documento
    print("\n--- Ejemplo 2: Leer documento ---")
    # Primero necesitamos un archivo existente
    from agents.file_finder import FileFinderAgent
    finder = FileFinderAgent(".")
    txt_files = finder.find_files(pattern="*.md")
    
    if txt_files:
        file_path = txt_files[0].path
        result = orchestrator.process_instruction(f"Lee el archivo {file_path}")
        if result.get('success'):
            print(f"Contenido (primeros 200 chars): {result.get('content', '')[:200]}")
    
    # Ejemplo 3: Analizar documento
    print("\n--- Ejemplo 3: Analizar documento ---")
    if txt_files:
        result = orchestrator.process_instruction(
            f"Analiza el documento {txt_files[0].path} y dame un resumen"
        )
        if result.get('success'):
            print(f"Resumen: {result.get('summary', 'N/A')[:300]}")
    
    # Ejemplo 4: Crear documento
    print("\n--- Ejemplo 4: Crear documento ---")
    result = orchestrator.process_instruction(
        "Crea un documento con una lista de tareas pendientes para esta semana"
    )
    if result.get('success'):
        print(f"Documento creado en: {result.get('file_path')}")
    
    # Ejemplo 5: Clasificar documento
    print("\n--- Ejemplo 5: Clasificar documento ---")
    if txt_files:
        result = orchestrator.process_instruction(
            f"Clasifica el documento {txt_files[0].path}"
        )
        if result.get('success'):
            classification = result.get('classification', {})
            print(f"Categoría: {classification.get('category', 'N/A')}")
            print(f"Tags: {', '.join(classification.get('tags', [])[:5])}")
    
    # Mostrar estado del sistema
    print("\n--- Estado del Sistema ---")
    status = orchestrator.get_status()
    print(f"Agentes inicializados: {len(status['agents_initialized'])}")
    print(f"Acciones en historial: {status['actions_in_history']}")
    print(f"LLM configurado: {status['llm_configured']}")


def example_individual_agents():
    """Ejemplo usando agentes individualmente."""
    print("\n" + "="*60)
    print("USO INDIVIDUAL DE AGENTES")
    print("="*60)
    
    # Agente buscador
    from agents.file_finder import FileFinderAgent
    
    finder = FileFinderAgent("/workspace/rag_system")
    files = finder.find_documents(recursive=True)
    stats = finder.get_statistics(files)
    
    print(f"\n📁 Documentos en /workspace/rag_system:")
    print(f"   Total: {stats.get('total_files', 0)}")
    print(f"   Por tipo: {stats.get('by_extension', {})}")
    
    # Agente lector
    from agents.document_reader import DocumentReaderAgent
    
    reader = DocumentReaderAgent()
    md_files = finder.find_by_type('md')
    
    if md_files:
        print(f"\n📖 Leyendo: {md_files[0].name}")
        content = reader.read_document(md_files[0].path)
        print(f"   Tipo: {content.metadata.get('file_type')}")
        print(f"   Primeros 100 chars: {content.content[:100]}...")
    
    # Agente clasificador (sin LLM)
    from agents.document_classifier import DocumentClassifierAgent
    
    classifier = DocumentClassifierAgent(llm_client=None)
    
    if md_files:
        content = reader.read_document(md_files[0].path)
        classification = classifier.classify(content.content, md_files[0].path)
        
        print(f"\n🏷️ Clasificación:")
        print(f"   Categoría: {classification.category}")
        print(f"   Complejidad: {classification.complexity}")
        print(f"   Idioma: {classification.language}")
        print(f"   Tags: {classification.tags[:5]}")


def example_with_vision_model():
    """Ejemplo usando modelo de visión para documentos con imágenes."""
    print("\n" + "="*60)
    print("USO CON MODELO DE VISIÓN")
    print("="*60)
    
    # Nota: Esto requiere un modelo multimodal en llama.cpp
    # Ejemplo conceptual
    
    llm_client = setup_llm_client()
    
    if llm_client:
        print("\nPara usar visión, necesitas:")
        print("1. Un modelo multimodal (ej: LLaVA)")
        print("2. Extraer imágenes de los documentos")
        print("3. Usar la API de visión del LLM")
        
        # Ejemplo conceptual
        prompt = """
        Este es un ejemplo de cómo se usaría con imágenes:
        
        from agents.document_reader import DocumentReaderAgent
        
        reader = DocumentReaderAgent()
        content = reader.read_document("documento_con_imagenes.pdf")
        
        if content.images_info:
            for img in content.images_info:
                # Enviar imagen al modelo de visión
                response = llm_client.chat.completions.create(
                    model="llava-model",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "¿Qué muestra esta imagen?"},
                            {"type": "image_url", "image_url": {"url": f"file://{img['path']}"}}
                        ]
                    }]
                )
        """
        print(prompt)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SISTEMA DE AGENTES PARA GESTIÓN DOCUMENTAL")
    print("="*60)
    print("\nEste sistema incluye:")
    print("  🔍 FileFinderAgent - Búsqueda de archivos")
    print("  📖 DocumentReaderAgent - Lectura de PDF, ODT, ODP, ODG, etc.")
    print("  🏷️ DocumentClassifierAgent - Clasificación automática")
    print("  🧐 DocumentAnalyzerAgent - Análisis profundo con LLM")
    print("  📝 DocumentManagerAgent - Crear/modificar/organizar")
    print("  🎼 AgentOrchestrator - Coordinación de todos los agentes")
    
    # Ejecutar ejemplos
    example_individual_agents()
    example_basic_usage()
    example_with_vision_model()
    
    print("\n" + "="*60)
    print("PARA MÁS INFORMACIÓN:")
    print("="*60)
    print("""
Requisitos:
1. Instalar dependencias adicionales:
   pip install odfpy python-docx openpyxl python-pptx

2. Iniciar servidor llama.cpp:
   ./server -m tu-modelo.gguf --port 8081
   
   Para visión (imágenes):
   ./server -m llava-model.gguf --port 8081 --mmproj projector.gguf

3. Usar el orquestador:
   from agents.orchestrator import AgentOrchestrator
   orchestrator = AgentOrchestrator(llm_client, base_directory=".")
   result = orchestrator.process_instruction("tu instrucción aquí")

Formatos soportados:
- PDF, ODT, ODS, ODP, ODG (OpenDocument)
- TXT, MD, CSV
- DOCX, XLSX, PPTX (Microsoft Office)
""")
