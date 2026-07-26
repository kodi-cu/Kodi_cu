"""
Punto de entrada principal para PDF Agent CLI
"""
import sys
from pathlib import Path

# Añadir el path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

from src.core.agent import PDFAgent
from src.config.settings import MODEL_NAME
from colorama import Fore, Style, init

init(autoreset=True)


def main():
    """Ejecuta el agente en modo consola"""
    print(f"{Fore.CYAN}🚀 PDF Agent - Agente Profesional de IA{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📂 Herramientas disponibles:{Style.RESET_ALL}")
    print(f"  • Básicas: leer_archivo, listar_archivos, ejecutar_comando_seguro")
    print(f"  • PDF: analizar_pdf, clasificar_pdfs, buscar_en_pdfs, resumen_ejecutivo_pdfs")
    print(f"  • TODO: todo_write, todo_add, todo_update, todo_list")
    print(f"{Fore.GREEN}💬 Escribe 'salir' para terminar{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'═' * 60}{Style.RESET_ALL}\n")
    
    agent = PDFAgent()
    
    while True:
        try:
            pregunta = input(f"{Fore.GREEN}👤 [TÚ]: {Style.RESET_ALL}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Fore.CYAN}👋 ¡Hasta luego!{Style.RESET_ALL}")
            break
        
        if pregunta.lower() in ["salir", "exit", "quit"]:
            print(f"{Fore.CYAN}👋 ¡Hasta luego!{Style.RESET_ALL}")
            break
        
        if not pregunta.strip():
            continue
        
        print(f"\n{Fore.MAGENTA}🤖 [AGENTE]{Style.RESET_ALL}")
        result = agent.procesar_pregunta(pregunta)
        
        if "error" in result:
            print(f"{Fore.RED}❌ Error: {result['error']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Asegúrate de que llama-server esté corriendo{Style.RESET_ALL}")
        else:
            if result.get('respuesta'):
                print(f"\n{Fore.GREEN}✅ [RESPUESTA]{Style.RESET_ALL}")
                print(result['respuesta'])
            
            # Mostrar estadísticas si hay tareas
            if result.get('todo_stats') and result['todo_stats']['total'] > 0:
                print(f"\n{Fore.BLUE}📊 Estado de tareas:{Style.RESET_ALL}")
                stats = result['todo_stats']
                print(f"  Total: {stats['total']} | Completadas: {stats['completed']} | Pendientes: {stats['pending']}")
        
        print(f"\n{Fore.MAGENTA}{'─' * 60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
