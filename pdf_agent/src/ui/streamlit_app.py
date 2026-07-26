"""
Interfaz web para PDF Agent usando Streamlit
"""
import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Añadir el path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent import PDFAgent
from src.config.settings import UI_HOST, UI_PORT, PDF_UPLOAD_DIR, OUTPUT_DIR


def init_session_state():
    """Inicializa el estado de la sesión"""
    if 'agent' not in st.session_state:
        st.session_state.agent = PDFAgent()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "chat"


def render_sidebar():
    """Renderiza la barra lateral"""
    with st.sidebar:
        st.title("🤖 PDF Agent")
        st.markdown("---")
        
        # Navegación
        view = st.radio(
            "Navegación",
            ["💬 Chat", "📄 Documentos", "✅ Tareas", "⚙️ Configuración"],
            index=["💬 Chat", "📄 Documentos", "✅ Tareas", "⚙️ Configuración"].index(st.session_state.current_view)
        )
        st.session_state.current_view = view
        
        st.markdown("---")
        
        # Estado del agente
        if hasattr(st.session_state.agent, 'state'):
            state = st.session_state.agent.state
            if state.start_time:
                st.metric("Iteraciones", state.iteration_count)
                if state.end_time and state.start_time:
                    duration = (state.end_time - state.start_time).total_seconds()
                    st.metric("Duración última tarea", f"{duration:.2f}s")
        
        # Estadísticas TODO
        todo_stats = st.session_state.agent.todo_manager.get_stats()
        st.subheader("📊 Progreso")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", todo_stats['total'])
        with col2:
            st.metric("Completadas", todo_stats['completed'])
        with col3:
            st.metric("Pendientes", todo_stats['pending'])
        
        if todo_stats['total'] > 0:
            progress = todo_stats['progress_percentage'] / 100
            st.progress(progress)
            st.caption(f"{todo_stats['progress_percentage']}% completado")
        
        st.markdown("---")
        
        # Botones de acción
        if st.button("🗑️ Limpiar chat"):
            st.session_state.agent.reset()
            st.session_state.chat_history = []
            st.rerun()
        
        if st.button("💾 Guardar sesión"):
            filepath = OUTPUT_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if st.session_state.agent.save_session(str(filepath)):
                st.success(f"Sesión guardada en {filepath}")
            else:
                st.error("Error al guardar sesión")


def render_chat():
    """Renderiza la vista de chat"""
    st.title("💬 Chat con PDF Agent")
    
    # Mostrar historial
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
            if "metadata" in msg and msg["metadata"]:
                metadata = msg["metadata"]
                if 'state' in metadata:
                    with st.expander("🧠 Estado del agente"):
                        state = metadata['state']
                        if state.get('reasoning_steps'):
                            st.subheader("Razonamiento")
                            for step in state['reasoning_steps']:
                                st.info(step)
                        if state.get('tools_used'):
                            st.subheader("Herramientas usadas")
                            st.json(state['tools_used'])
                
                if 'todo_stats' in metadata:
                    with st.expander("✅ Estado de tareas"):
                        st.json(metadata['todo_stats'])
    
    # Input del usuario
    if prompt := st.chat_input("Escribe tu pregunta sobre los PDFs..."):
        # Añadir mensaje del usuario
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Procesar con el agente
        with st.chat_message("assistant"):
            with st.spinner("🤔 Pensando..."):
                result = st.session_state.agent.procesar_pregunta(prompt)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                    respuesta = "Lo siento, ha ocurrido un error."
                else:
                    respuesta = result.get('respuesta', 'No pude generar una respuesta.')
                    st.write(respuesta)
                    
                    # Mostrar metadatos
                    metadata = {
                        'state': result.get('state', {}),
                        'todo_stats': result.get('todo_stats', {})
                    }
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": respuesta,
                        "metadata": metadata
                    })
                    
                    # Mostrar herramientas usadas
                    if result.get('state', {}).get('tools_used'):
                        st.caption(f"🔧 Herramientas usadas: {', '.join(result['state']['tools_used'])}")


def render_documents():
    """Renderiza la vista de documentos"""
    st.title("📄 Gestión de Documentos")
    
    # Subida de archivos
    uploaded_files = st.file_uploader(
        "Subir archivos PDF",
        type=['pdf'],
        accept_multiple_files=True,
        help="Sube los PDFs que quieres analizar"
    )
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        
        # Guardar archivos
        PDF_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        cols = st.columns(2)
        for i, file in enumerate(uploaded_files):
            filepath = PDF_UPLOAD_DIR / file.name
            with open(filepath, "wb") as f:
                f.write(file.getvalue())
            
            with cols[i % 2]:
                st.success(f"✅ {file.name}")
                st.caption(f"{round(file.size / 1024, 2)} KB")
        
        # Acciones disponibles
        st.subheader("🔧 Acciones disponibles")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Analizar todos los PDFs", use_container_width=True):
                directorio = str(PDF_UPLOAD_DIR)
                result = st.session_state.agent.resumen_ejecutivo_pdfs(directorio)
                st.text_area("Resumen", value=result, height=300)
        
        with col2:
            if st.button("📋 Clasificar por fecha", use_container_width=True):
                directorio = str(PDF_UPLOAD_DIR)
                result = st.session_state.agent.clasificar_pdfs(directorio, criterio="fecha")
                st.text_area("Clasificación", value=result, height=300)
        
        # Búsqueda
        st.subheader("🔍 Búsqueda en PDFs")
        search_term = st.text_input("Palabra clave a buscar")
        if search_term and st.button("Buscar"):
            directorio = str(PDF_UPLOAD_DIR)
            result = st.session_state.agent.buscar_en_pdfs(directorio, search_term)
            st.text_area("Resultados", value=result, height=300)


def render_todos():
    """Renderiza la vista de tareas TODO"""
    st.title("✅ Gestión de Tareas")
    
    # Añadir nueva tarea
    st.subheader("➕ Nueva tarea")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_task = st.text_input("Descripción de la tarea", key="new_task_input")
    with col2:
        task_status = st.selectbox("Estado", ["pending", "in_progress", "completed"], key="new_task_status")
    
    if st.button("Añadir tarea"):
        if new_task:
            result = st.session_state.agent.todo_manager.todo_add(new_task, task_status)
            st.success(result)
            st.rerun()
    
    # Mostrar tareas
    st.subheader("📋 Lista de tareas")
    
    todo_state = st.session_state.agent.get_todo_state()
    todos = todo_state.get('todos', [])
    
    if not todos:
        st.info("No hay tareas pendientes. ¡Añade una arriba!")
    else:
        # Filtros
        filter_status = st.selectbox(
            "Filtrar por estado",
            ["all", "pending", "in_progress", "completed"],
            key="todo_filter"
        )
        
        # Agrupar por estado
        status_groups = {
            "pending": [],
            "in_progress": [],
            "completed": []
        }
        
        for todo in todos:
            if filter_status == "all" or todo['status'] == filter_status:
                status_groups[todo['status']].append(todo)
        
        # Mostrar tareas pendientes
        if status_groups["pending"]:
            st.markdown("### ⏳ Pendientes")
            for todo in status_groups["pending"]:
                col1, col2, col3 = st.columns([6, 2, 1])
                with col1:
                    st.write(f"**[{todo['id']}]** {todo['content']}")
                with col2:
                    if st.button("▶️ Iniciar", key=f"start_{todo['id']}"):
                        st.session_state.agent.todo_manager.todo_update(todo['id'], "in_progress")
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{todo['id']}"):
                        st.session_state.agent.todo_manager.todo_delete(todo['id'])
                        st.rerun()
        
        # Mostrar tareas en progreso
        if status_groups["in_progress"]:
            st.markdown("### 🔄 En progreso")
            for todo in status_groups["in_progress"]:
                col1, col2, col3 = st.columns([6, 2, 1])
                with col1:
                    st.write(f"**[{todo['id']}]** {todo['content']}")
                with col2:
                    if st.button("✅ Completar", key=f"complete_{todo['id']}"):
                        st.session_state.agent.todo_manager.todo_update(todo['id'], "completed")
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{todo['id']}"):
                        st.session_state.agent.todo_manager.todo_delete(todo['id'])
                        st.rerun()
        
        # Mostrar tareas completadas
        if status_groups["completed"]:
            with st.expander(f"✅ Completadas ({len(status_groups['completed'])})"):
                for todo in status_groups["completed"]:
                    st.write(f"~~**[{todo['id']}]** {todo['content']}~~")
        
        # Estadísticas
        stats = st.session_state.agent.todo_manager.get_stats()
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", stats['total'])
        with col2:
            st.metric("Completadas", stats['completed'])
        with col3:
            st.metric("En progreso", stats['in_progress'])
        with col4:
            st.metric("Pendientes", stats['pending'])
        
        if stats['total'] > 0:
            progress = stats['progress_percentage'] / 100
            st.progress(progress)
            st.caption(f"{stats['progress_percentage']}% completado")


def render_settings():
    """Renderiza la vista de configuración"""
    st.title("⚙️ Configuración")
    
    st.subheader("🤖 Modelo")
    st.write(f"Modelo actual: `{st.session_state.agent.model_name}`")
    st.write(f"Server: `{st.session_state.agent.client.base_url}`")
    
    st.subheader("📁 Directorios")
    st.write(f"Upload: `{PDF_UPLOAD_DIR}`")
    st.write(f"Output: `{OUTPUT_DIR}`")
    
    st.subheader("💾 Exportar/Importar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Exportar configuración", use_container_width=True):
            filepath = OUTPUT_DIR / f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            config = {
                "model_name": st.session_state.agent.model_name,
                "server_url": str(st.session_state.agent.client.base_url),
                "todo_state": st.session_state.agent.get_todo_state(),
            }
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            st.success(f"Configuración exportada a {filepath}")
    
    with col2:
        uploaded_config = st.file_uploader("Importar configuración", type=['json'])
        if uploaded_config:
            try:
                config = json.load(uploaded_config)
                if 'todo_state' in config:
                    st.session_state.agent.todo_manager.todo_write([
                        {"id": t['id'], "content": t['content'], "status": t['status']}
                        for t in config['todo_state'].get('todos', [])
                    ])
                st.success("Configuración importada correctamente")
            except Exception as e:
                st.error(f"Error al importar: {e}")
    
    st.subheader("ℹ️ Acerca de")
    st.markdown("""
    **PDF Agent** es un asistente de IA especializado en análisis de documentos PDF.
    
    Características:
    - 📄 Análisis de PDFs individuales o lotes completos
    - 🔍 Búsqueda de palabras clave en múltiples documentos
    - ✅ Gestión de tareas con lista TODO
    - 🧠 Razonamiento visible del agente
    - 🔌 Conectado a modelo local vía llama.cpp
    
    Versión: 1.0.0
    """)


def main():
    """Función principal"""
    st.set_page_config(
        page_title="PDF Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    render_sidebar()
    
    view = st.session_state.current_view
    
    if view == "💬 Chat":
        render_chat()
    elif view == "📄 Documentos":
        render_documents()
    elif view == "✅ Tareas":
        render_todos()
    elif view == "⚙️ Configuración":
        render_settings()


if __name__ == "__main__":
    main()
