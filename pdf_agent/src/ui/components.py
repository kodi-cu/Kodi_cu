"""
Componentes UI reutilizables para la interfaz del agente PDF.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime


def render_header(title: str, subtitle: str = ""):
    """Renderiza el encabezado de la aplicación."""
    st.markdown(f"""
    <div style='background-color: #1f2937; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>{title}</h1>
        {f'<p style="color: #9ca3af; margin: 0.5rem 0 0 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def render_card(title: str, content: str, icon: str = "📄", bg_color: str = "#f3f4f6"):
    """Renderiza una tarjeta con contenido."""
    st.markdown(f"""
    <div style='background-color: {bg_color}; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3b82f6;'>
        <h3 style='margin: 0 0 0.5rem 0; color: #1f2937;'>{icon} {title}</h3>
        <p style='margin: 0; color: #4b5563;'>{content}</p>
    </div>
    """, unsafe_allow_html=True)


def render_status_indicator(status: str, label: str = ""):
    """Renderiza un indicador de estado."""
    colors = {
        "success": "#10b981",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "info": "#3b82f6",
        "pending": "#6b7280"
    }
    
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "pending": "⏳"
    }
    
    color = colors.get(status, "#6b7280")
    icon = icons.get(status, "•")
    
    st.markdown(f"""
    <span style='background-color: {color}; color: white; padding: 0.25rem 0.75rem; 
                border-radius: 9999px; font-size: 0.875rem; display: inline-block;'>
        {icon} {label if label else status.capitalize()}
    </span>
    """, unsafe_allow_html=True)


def render_file_info(file_data: Dict[str, Any]):
    """Renderiza información detallada de un archivo."""
    with st.expander(f"📁 {file_data.get('name', 'Archivo')}", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Tamaño", file_data.get('size_human', 'N/A'))
            st.metric("Extensión", file_data.get('extension', 'N/A'))
        
        with col2:
            st.metric("Creado", file_data.get('created', 'N/A')[:10] if file_data.get('created') else 'N/A')
            st.metric("Modificado", file_data.get('modified', 'N/A')[:10] if file_data.get('modified') else 'N/A')
        
        if 'path' in file_data:
            st.code(file_data['path'], language=None)


def render_todo_item(todo, index: int):
    """Renderiza un elemento de la lista TODO."""
    # Validar que todo sea un diccionario
    if not isinstance(todo, dict):
        st.warning(f"Elemento de tarea inválido en índice {index}")
        return False
    
    status_colors = {
        "pending": "#fbbf24",
        "in_progress": "#3b82f6",
        "completed": "#10b981",
        "cancelled": "#ef4444"
    }
    
    status_icons = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "cancelled": "❌"
    }
    
    status = todo.get('status', 'pending')
    color = status_colors.get(status, "#6b7280")
    icon = status_icons.get(status, "•")
    
    with st.container():
        cols = st.columns([0.5, 4, 1, 0.5])
        
        with cols[0]:
            st.markdown(f"<span style='font-size: 1.2rem;'>{icon}</span>", unsafe_allow_html=True)
        
        with cols[1]:
            priority_badge = ""
            if todo.get('priority') == 'high':
                priority_badge = "🔴 Alta"
            elif todo.get('priority') == 'medium':
                priority_badge = "🟡 Media"
            elif todo.get('priority') == 'low':
                priority_badge = "🟢 Baja"
            
            st.markdown(f"**{todo.get('task', 'Tarea sin título')}** {priority_badge}")
            
            if todo.get('description'):
                st.caption(todo['description'])
        
        with cols[2]:
            if todo.get('due_date'):
                st.caption(f"📅 {todo['due_date'][:10]}")
        
        with cols[3]:
            if st.button("🗑️", key=f"delete_todo_{index}", help="Eliminar tarea"):
                return True
    
    return False


def render_reasoning_step(step: Dict[str, Any], index: int):
    """Renderiza un paso del razonamiento del agente."""
    step_types = {
        "analysis": "🔍",
        "planning": "📋",
        "execution": "⚙️",
        "evaluation": "✅",
        "conclusion": "🎯"
    }
    
    icon = step_types.get(step.get('type', ''), "💭")
    
    with st.expander(f"{icon} Paso {index + 1}: {step.get('type', 'Paso').capitalize()}", expanded=True):
        st.write(step.get('content', ''))
        
        if step.get('timestamp'):
            st.caption(f"Timestamp: {step['timestamp']}")


def render_chat_message(message: Dict[str, Any], is_user: bool = False):
    """Renderiza un mensaje de chat."""
    # Validar que message sea un diccionario
    if not isinstance(message, dict):
        st.write(str(message))
        return
    
    if is_user:
        with st.chat_message("user"):
            st.write(message.get('content', ''))
    else:
        with st.chat_message("assistant"):
            st.write(message.get('content', ''))
            
            if message.get('reasoning'):
                with st.expander("🧠 Ver razonamiento"):
                    for i, step in enumerate(message.get('reasoning', [])):
                        if isinstance(step, dict):
                            render_reasoning_step(step, i)
            
            if message.get('tools_used'):
                with st.expander("🛠️ Herramientas utilizadas"):
                    for tool in message.get('tools_used', []):
                        if isinstance(tool, dict):
                            st.code(f"{tool.get('name', 'Herramienta')}: {tool.get('result', 'Sin resultado')}", language=None)
                        else:
                            st.code(str(tool), language=None)


def render_metrics_grid(metrics: Dict[str, Any]):
    """Renderiza una cuadrícula de métricas."""
    cols = st.columns(len(metrics))
    
    for i, (key, value) in enumerate(metrics.items()):
        with cols[i]:
            st.metric(label=key.replace('_', ' ').title(), value=value)


def render_progress_bar(progress: float, label: str = "Progreso"):
    """Renderiza una barra de progreso."""
    st.progress(progress)
    st.caption(f"{label}: {progress * 100:.1f}%")


def render_error_box(message: str, title: str = "Error"):
    """Renderiza una caja de error."""
    st.error(f"**{title}**: {message}")


def render_success_box(message: str, title: str = "Éxito"):
    """Renderiza una caja de éxito."""
    st.success(f"**{title}**: {message}")


def render_warning_box(message: str, title: str = "Advertencia"):
    """Renderiza una caja de advertencia."""
    st.warning(f"**{title}**: {message}")


def render_info_box(message: str, title: str = "Información"):
    """Renderiza una caja de información."""
    st.info(f"**{title}**: {message}")


def create_sidebar_menu():
    """Crea un menú en la barra lateral."""
    st.sidebar.title("📑 Menú")
    
    options = [
        "💬 Chat con Agente",
        "📁 Gestión de Documentos",
        "✅ Lista de Tareas",
        "📊 Estadísticas",
        "⚙️ Configuración"
    ]
    
    selection = st.sidebar.radio("Navegación", options)
    
    return selection


def render_document_stats(stats: Dict[str, Any]):
    """Renderiza estadísticas de documentos."""
    st.subheader("📊 Estadísticas de Documentos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documentos", stats.get('total_documents', 0))
    
    with col2:
        st.metric("PDFs Procesados", stats.get('pdfs_processed', 0))
    
    with col3:
        st.metric("Tamaño Total", stats.get('total_size', '0 MB'))
    
    with col4:
        st.metric("Última Actualización", stats.get('last_update', 'N/A'))
