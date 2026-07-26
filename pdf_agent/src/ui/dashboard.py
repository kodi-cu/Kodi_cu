"""
Interfaz web principal para el agente PDF.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.components import (
    render_header,
    render_card,
    render_status_indicator,
    render_file_info,
    render_todo_item,
    render_reasoning_step,
    render_chat_message,
    render_metrics_grid,
    render_error_box,
    render_success_box,
    render_warning_box,
    render_info_box,
    create_sidebar_menu,
    render_document_stats
)

# Configuración de la página
st.set_page_config(
    page_title="PDF Agent - Gestor Inteligente de Documentos",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estado de la sesión
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'todos' not in st.session_state:
    st.session_state.todos = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []


def initialize_agent():
    """Inicializa el agente PDF."""
    try:
        from core.agent import PDFAgent
        
        agent = PDFAgent()
        st.session_state.agent = agent
        return True
    except Exception as e:
        st.error(f"Error al inicializar el agente: {e}")
        return False


def main():
    """Función principal de la aplicación."""
    
    # Renderizar encabezado
    render_header(
        "🤖 PDF Agent",
        "Asistente Inteligente para Gestión de Documentos PDF"
    )
    
    # Menú lateral
    selection = create_sidebar_menu()
    
    # Inicializar agente si es necesario
    if st.session_state.agent is None:
        if st.button("🚀 Inicializar Agente"):
            initialize_agent()
    
    # ===========================================
    # PÁGINA: CHAT CON AGENTE
    # ===========================================
    if selection == "💬 Chat con Agente":
        st.subheader("💬 Interactúa con el Agente")
        
        # Mostrar estado del agente
        if st.session_state.agent:
            render_status_indicator("success", "Agente Activo")
        else:
            render_status_indicator("warning", "Agente No Inicializado")
        
        # Área de chat
        chat_container = st.container()
        
        with chat_container:
            # Mostrar historial de chat
            for message in st.session_state.chat_history:
                render_chat_message(message, is_user=message.get('is_user', False))
        
        # Input de usuario
        user_input = st.chat_input("Escribe tu mensaje aquí...")
        
        if user_input and st.session_state.agent:
            # Añadir mensaje del usuario
            st.session_state.chat_history.append({
                'content': user_input,
                'is_user': True
            })
            
            # Procesar con el agente
            with st.spinner("🤔 El agente está pensando..."):
                try:
                    response = st.session_state.agent.procesar_pregunta(user_input)
                    
                    # Añadir respuesta del agente
                    st.session_state.chat_history.append({
                        'content': response.get('respuesta', ''),
                        'is_user': False,
                        'reasoning': response.get('state', {}).get('reasoning_steps', []),
                        'tools_used': response.get('state', {}).get('tools_used', [])
                    })
                    
                    # Actualizar TODO list si hay cambios
                    if 'todo_stats' in response:
                        st.session_state.todos = response.get('todo_stats', {})
                    
                    st.rerun()
                    
                except Exception as e:
                    render_error_box(str(e), "Error al procesar")
        
        elif user_input and not st.session_state.agent:
            render_warning_box("Por favor, inicializa el agente primero.", "Agente no disponible")
    
    # ===========================================
    # PÁGINA: GESTIÓN DE DOCUMENTOS
    # ===========================================
    elif selection == "📁 Gestión de Documentos":
        st.subheader("📁 Gestión de Documentos PDF")
        
        # Subir archivos
        uploaded_files = st.file_uploader(
            "Subir documentos PDF",
            type=['pdf'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in [f['name'] for f in st.session_state.uploaded_files]:
                    # Guardar archivo
                    save_path = Path("uploads") / uploaded_file.name
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    st.session_state.uploaded_files.append({
                        'name': uploaded_file.name,
                        'path': str(save_path),
                        'size': uploaded_file.size
                    })
                    
                    render_success_box(f"Archivo {uploaded_file.name} subido correctamente")
        
        # Mostrar archivos subidos
        if st.session_state.uploaded_files:
            st.subheader("📂 Documentos Disponibles")
            
            for file_info in st.session_state.uploaded_files:
                render_file_info(file_info)
        
        # Listar archivos en directorio uploads
        uploads_dir = Path("uploads")
        if uploads_dir.exists():
            pdf_files = list(uploads_dir.glob("*.pdf"))
            
            if pdf_files:
                st.subheader(f"📑 Archivos en uploads ({len(pdf_files)} encontrados)")
                
                for pdf_file in pdf_files:
                    with st.expander(f"📄 {pdf_file.name}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Tamaño", f"{pdf_file.stat().st_size / 1024:.2f} KB")
                        
                        with col2:
                            from datetime import datetime
                            mtime = datetime.fromtimestamp(pdf_file.stat().st_mtime)
                            st.metric("Modificado", mtime.strftime("%Y-%m-%d"))
                        
                        # Botones de acción
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        with action_col1:
                            if st.button("📝 Analizar", key=f"analyze_{pdf_file.name}"):
                                if st.session_state.agent:
                                    try:
                                        result = st.session_state.agent.analizar_pdf_smart(str(pdf_file))
                                        with st.expander("Vista previa del contenido"):
                                            st.text(result[:1000] + "...")
                                    except Exception as e:
                                        render_error_box(str(e))
                                else:
                                    render_warning_box("Inicializa el agente primero")
                        
                        with action_col2:
                            if st.button("📊 Metadatos", key=f"meta_{pdf_file.name}"):
                                if st.session_state.agent:
                                    try:
                                        # Usar pypdf directamente para metadatos
                                        from pypdf import PdfReader
                                        reader = PdfReader(str(pdf_file))
                                        metadata = reader.metadata
                                        st.json(metadata or {})
                                    except Exception as e:
                                        render_error_box(str(e))
                                else:
                                    render_warning_box("Inicializa el agente primero")
                        
                        with action_col3:
                            if st.button("🏷️ Clasificar", key=f"class_{pdf_file.name}"):
                                render_info_box("Funcionalidad de clasificación próximamente", "En desarrollo")
    
    # ===========================================
    # PÁGINA: LISTA DE TAREAS
    # ===========================================
    elif selection == "✅ Lista de Tareas":
        st.subheader("✅ Lista de Tareas del Agente")
        
        # Formulario para añadir tarea
        with st.form("add_todo_form"):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                task_description = st.text_input("Nueva tarea", placeholder="Describe la tarea...")
            
            with col2:
                priority = st.selectbox("Prioridad", ["low", "medium", "high"])
            
            with col3:
                submitted = st.form_submit_button("➕ Añadir", use_container_width=True)
            
            if submitted and task_description:
                new_todo = {
                    'task': task_description,
                    'status': 'pending',
                    'priority': priority,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'description': ''
                }
                st.session_state.todos.append(new_todo)
                render_success_box("Tarea añadida correctamente")
        
        # Mostrar tareas
        if st.session_state.todos:
            st.divider()
            st.subheader(f"Tareas ({len(st.session_state.todos)})")
            
            # Filtrar por estado
            filter_status = st.selectbox(
                "Filtrar por estado",
                ["all", "pending", "in_progress", "completed"]
            )
            
            filtered_todos = st.session_state.todos
            if filter_status != "all":
                filtered_todos = [t for t in st.session_state.todos if t.get('status') == filter_status]
            
            for i, todo in enumerate(filtered_todos):
                if render_todo_item(todo, i):
                    # Eliminar tarea
                    st.session_state.todos.remove(todo)
                    st.rerun()
        else:
            render_info_box("No hay tareas pendientes", "Lista vacía")
    
    # ===========================================
    # PÁGINA: ESTADÍSTICAS
    # ===========================================
    elif selection == "📊 Estadísticas":
        st.subheader("📊 Estadísticas del Sistema")
        
        # Métricas generales
        metrics = {
            "Archivos Subidos": len(st.session_state.uploaded_files),
            "Mensajes en Chat": len(st.session_state.chat_history),
            "Tareas Pendientes": len([t for t in st.session_state.todos if t.get('status') == 'pending']),
            "Tareas Completadas": len([t for t in st.session_state.todos if t.get('status') == 'completed'])
        }
        
        render_metrics_grid(metrics)
        
        st.divider()
        
        # Estadísticas de documentos
        uploads_dir = Path("uploads")
        if uploads_dir.exists():
            pdf_files = list(uploads_dir.glob("*.pdf"))
            
            stats = {
                'total_documents': len(pdf_files),
                'pdfs_processed': len(pdf_files),
                'total_size': f"{sum(f.stat().st_size for f in pdf_files) / 1024 / 1024:.2f} MB",
                'last_update': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            render_document_stats(stats)
    
    # ===========================================
    # PÁGINA: CONFIGURACIÓN
    # ===========================================
    elif selection == "⚙️ Configuración":
        st.subheader("⚙️ Configuración del Agente")
        
        # Configuración del modelo
        st.section("Configuración del Modelo")
        
        model_path = st.text_input(
            "Ruta del Modelo",
            value="models/llama-2-7b-chat.Q4_K_M.gguf",
            help="Ruta al archivo del modelo GGUF"
        )
        
        max_tokens = st.slider(
            "Máximo de Tokens",
            min_value=256,
            max_value=4096,
            value=2048,
            step=256
        )
        
        temperature = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Controla la creatividad del modelo"
        )
        
        st.divider()
        
        # Configuración del sistema
        st.section("Configuración del Sistema")
        
        upload_dir = st.text_input(
            "Directorio de Uploads",
            value="uploads"
        )
        
        log_level = st.selectbox(
            "Nivel de Log",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1
        )
        
        # Guardar configuración
        if st.button("💾 Guardar Configuración"):
            render_success_box("Configuración guardada (simulado)", "Éxito")
        
        st.divider()
        
        # Información del sistema
        st.section("Información del Sistema")
        
        import sys
        st.info(f"""
        - **Python**: {sys.version.split()[0]}
        - **Streamlit**: {st.__version__}
        - **Estado del Agente**: {'Activo' if st.session_state.agent else 'Inactivo'}
        """)


if __name__ == "__main__":
    main()
