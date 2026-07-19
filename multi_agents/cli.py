"""Script CLI interactivo para el sistema multi-agente de gestión documental"""

import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from agents.orchestrator import AgentOrchestrator


def print_welcome():
    """Imprime mensaje de bienvenida"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     SISTEMA MULTI-AGENTE DE GESTIÓN DOCUMENTAL            ║
║                                                           ║
║  Agentes disponibles:                                     ║
║  🔍 FileFinder      - Búsqueda de archivos               ║
║  📖 DocumentReader  - Lectura de documentos              ║
║  🏷️ Classifier      - Clasificación automática           ║
║  🧐 Analyzer        - Análisis profundo con LLM          ║
║  📝 Manager         - Crear/modificar documentos         ║
║  🎼 Orchestrator    - Coordinador central                ║
║                                                           ║
║  Optimizaciones:                                          ║
║  ✓ Cache de intenciones (evita llamadas LLM)             ║
║  ✓ Clasificación heurística (umbral 70%)                 ║
║  ✓ Patrones regex para consultas comunes                 ║
╚═══════════════════════════════════════════════════════════╝
    """)


def print_help():
    """Imprime ayuda de comandos"""
    print("""
Comandos disponibles:
  /help              - Muestra esta ayuda
  /search <query>    - Busca archivos (ej: /search pdf contrato)
  /read <archivo>    - Lee un documento
  /classify <archivo>- Clasifica un documento
  /summarize <arch>  - Resume un documento
  /analyze <archivo> - Analiza profundamente
  /extract <pregunta>- Extrae información específica
  /create <nombre>   - Crea nuevo documento
  /organize [dir]    - Organiza archivos por tipo
  /stats             - Muestra estadísticas del sistema
  /clear             - Limpia el cache
  /exit              - Sale del programa

Ejemplos:
  > /search pdf
  > /search odt informe
  > /read ./documents/contrato.pdf
  > /classify ./documents/presupuesto.xlsx
  > /summarize ./documents/reunion.odp
  > /analyze ./documents/proyecto.docx
  > /extract ¿Cuándo es la fecha límite?
  > /create reporte.md
    """)


def configure_client():
    """Configura el cliente OpenAI para llama.cpp local"""
    try:
        client = OpenAI(
            base_url="http://localhost:8081/v1",
            api_key="sk-no-key-required"
        )
        # Test de conexión
        models = client.models.list()
        print(f"✓ Conectado al servidor LLM en localhost:8081")
        return client
    except Exception as e:
        print(f"⚠ No se pudo conectar al servidor LLM: {str(e)}")
        print("  Continuando en modo limitado (sin LLM)")
        return None


def main():
    """Función principal del CLI interactivo"""
    print_welcome()
    
    # Configurar cliente LLM
    llm_client = configure_client()
    
    # Configurar paths de búsqueda
    search_paths = ["./documents", "./"]
    if len(sys.argv) > 1:
        search_paths = sys.argv[1:]
    
    # Inicializar orquestador
    orchestrator = AgentOrchestrator(
        llm_client=llm_client,
        vision_client=llm_client,  # Usar mismo cliente para visión si es compatible
        search_paths=search_paths,
        output_dir="./output",
        model_name="local-model",
        vision_model_name="local-vision-model"
    )
    
    print(f"\n📂 Directorios de búsqueda: {', '.join(search_paths)}")
    print("Escribe /help para ver comandos disponibles\n")
    
    # Bucle principal
    while True:
        try:
            # Leer input del usuario
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            # Comandos especiales
            if user_input.startswith('/'):
                command = user_input.lower().split()[0]
                
                if command == '/exit' or command == '/quit':
                    print("¡Hasta luego!")
                    break
                
                elif command == '/help':
                    print_help()
                    continue
                
                elif command == '/stats':
                    stats = orchestrator.get_stats()
                    print("\n=== Estadísticas del Sistema ===")
                    print(f"Cache de intenciones: {stats['cache_size']}/{stats['max_cache_size']}")
                    print(f"Eficiencia del cache: {stats.get('llm_calls_saved', {}).get('cache_efficiency', 'N/A')}")
                    print(f"Acciones soportadas: {', '.join(stats['supported_actions'])}")
                    print(f"Extensiones soportadas: {', '.join(stats['file_finder']['supported_extensions'][:10])}...")
                    continue
                
                elif command == '/clear':
                    orchestrator.clear_cache()
                    print("✓ Cache limpiado")
                    continue
                
                # Procesar comandos de acción
                elif command == '/search':
                    query = user_input[len(command):].strip()
                    if not query:
                        print("Uso: /search <término de búsqueda>")
                        continue
                    result = orchestrator.execute(query)
                    print_result(result)
                
                elif command == '/read':
                    file_path = user_input[len(command):].strip()
                    if not file_path:
                        print("Uso: /read <ruta_al_archivo>")
                        continue
                    result = orchestrator.execute(f"leer documento {file_path}", file_path=file_path)
                    print_result(result)
                
                elif command == '/classify':
                    file_path = user_input[len(command):].strip()
                    if not file_path:
                        print("Uso: /classify <ruta_al_archivo>")
                        continue
                    result = orchestrator.execute(f"clasificar documento", file_path=file_path)
                    print_result(result)
                
                elif command == '/summarize':
                    file_path = user_input[len(command):].strip()
                    if not file_path:
                        print("Uso: /summarize <ruta_al_archivo>")
                        continue
                    result = orchestrator.execute(f"resumir documento", file_path=file_path)
                    print_result(result)
                
                elif command == '/analyze':
                    file_path = user_input[len(command):].strip()
                    if not file_path:
                        print("Uso: /analyze <ruta_al_archivo>")
                        continue
                    result = orchestrator.execute(f"analizar documento", file_path=file_path)
                    print_result(result)
                
                elif command == '/extract':
                    question = user_input[len(command):].strip()
                    if not question:
                        print("Uso: /extract <pregunta>")
                        continue
                    result = orchestrator.execute(question)
                    print_result(result)
                
                elif command == '/create':
                    filename = user_input[len(command):].strip() or "documento_nuevo"
                    print("Ingresa el contenido (escribe END en una línea sola para terminar):")
                    lines = []
                    while True:
                        line = input()
                        if line.strip() == 'END':
                            break
                        lines.append(line)
                    content = '\n'.join(lines)
                    result = orchestrator.execute(
                        f"crear documento {filename}",
                        content=content,
                        filename=filename
                    )
                    print_result(result)
                
                elif command == '/organize':
                    directory = user_input[len(command):].strip() or "./documents"
                    result = orchestrator.execute(f"organizar archivos", directory=directory)
                    print_result(result)
                
                else:
                    print(f"Comando desconocido: {command}")
                    print("Escribe /help para ver comandos disponibles")
            
            else:
                # Consulta natural - dejar que el orchestrator detecte la intención
                result = orchestrator.execute(user_input)
                print_result(result)
        
        except KeyboardInterrupt:
            print("\n\nInterrumpido por el usuario")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


def print_result(result: dict):
    """Imprime el resultado de forma formateada"""
    print("\n" + "=" * 60)
    
    if result.get('success', False):
        action = result.get('action', 'unknown')
        
        if action == 'search':
            print(f"🔍 Búsqueda completada: {result.get('message', '')}")
            files = result.get('files', [])
            for i, file in enumerate(files[:10], 1):
                print(f"  {i}. {file.get('name', 'N/A')} ({file.get('size_human', 'N/A')})")
                print(f"     Ruta: {file.get('path', 'N/A')}")
            if len(files) > 10:
                print(f"  ... y {len(files) - 10} más")
        
        elif action == 'read':
            print("📖 Contenido del documento:")
            print("-" * 40)
            content = result.get('content', '')
            print(content[:2000] if len(content) > 2000 else content)
            if len(content) > 2000:
                print("\n... (contenido truncado, usa herramientas externas para ver completo)")
        
        elif action == 'classify':
            print(f"🏷️ Clasificación:")
            print(f"  Categoría: {result.get('category', 'N/A')}")
            print(f"  Confianza: {result.get('confidence', 0) * 100:.1f}%")
            print(f"  Método: {result.get('method', 'N/A')}")
            print(f"  ¿Usó LLM?: {'Sí' if result.get('llm_used') else 'No'} ✓")
        
        elif action == 'summarize':
            print("📝 Resumen:")
            print("-" * 40)
            print(result.get('summary', 'No disponible'))
        
        elif action == 'analyze':
            print("🧐 Análisis completo:")
            print("\nResumen:")
            print(result.get('summary', 'No disponible'))
            print("\nPuntos clave:")
            for point in result.get('key_points', [])[:5]:
                print(f"  • {point}")
        
        elif action == 'extract':
            print("💡 Información extraída:")
            print(f"  Pregunta: {result.get('question', 'N/A')}")
            print(f"  Respuesta: {result.get('answer', 'No disponible')}")
        
        elif action == 'create':
            print("📄 Documento creado:")
            print(f"  Nombre: {result.get('filename', 'N/A')}")
            print(f"  Ruta: {result.get('path', 'N/A')}")
        
        elif action == 'organize':
            print("📁 Organización completada:")
            print(f"  Archivos movidos: {result.get('moved_count', 0)}")
        
        else:
            print(result.get('message', 'Operación completada'))
            if 'files_found' in result:
                print(f"  Archivos encontrados: {result['files_found']}")
    
    else:
        print(f"❌ Error: {result.get('error', 'Error desconocido')}")
    
    # Mostrar estadísticas de optimización
    llm_savings = result.get('llm_calls_saved', {})
    if llm_savings:
        savings_pct = llm_savings.get('estimated_savings_percent', 0)
        if savings_pct > 0:
            print(f"\n⚡ Optimización: ~{savings_pct}% menos llamadas al LLM gracias al cache")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
