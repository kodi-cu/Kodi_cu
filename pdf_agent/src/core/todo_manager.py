"""
Sistema de gestión de tareas TODO para el agente
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class TodoItem:
    """Representa una tarea individual en la lista TODO"""
    id: int
    content: str
    status: str  # pending, in_progress, completed
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoItem':
        return cls(
            id=data["id"],
            content=data["content"],
            status=data["status"],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


class TodoManager:
    """Gestiona la lista de tareas TODO del agente"""
    
    VALID_STATUSES = ["pending", "in_progress", "completed"]
    
    def __init__(self):
        self.todos: List[TodoItem] = []
        self.next_id: int = 1
    
    def todo_write(self, todos: List[Dict[str, Any]]) -> str:
        """
        Crea o actualiza la lista completa de tareas TODO.
        
        Args:
            todos: Lista de tareas con formato [{"id": 1, "content": "tarea", "status": "pending"}]
        
        Returns:
            Resumen del estado de la lista TODO
        """
        try:
            if not todos or not isinstance(todos, list):
                return "❌ Error: 'todos' debe ser una lista de tareas"
            
            for todo_data in todos:
                if not all(k in todo_data for k in ["id", "content", "status"]):
                    return "❌ Error: Cada tarea debe tener 'id', 'content' y 'status'"
                if todo_data["status"] not in self.VALID_STATUSES:
                    return f"❌ Error: Estado inválido '{todo_data['status']}'. Usa pending, in_progress o completed"
            
            # Convertir a TodoItem
            self.todos = [TodoItem.from_dict(t) for t in todos]
            self.next_id = max([t.id for t in self.todos]) + 1 if self.todos else 1
            
            return self._generate_summary()
        
        except Exception as e:
            return f"❌ Error al gestionar TODOs: {str(e)}"
    
    def todo_add(self, content: str, status: str = "pending") -> str:
        """Añade una nueva tarea a la lista TODO."""
        if status not in self.VALID_STATUSES:
            return f"❌ Error: Estado inválido '{status}'"
        
        nuevo_todo = TodoItem(
            id=self.next_id,
            content=content,
            status=status
        )
        
        self.todos.append(nuevo_todo)
        self.next_id += 1
        
        return f"""✅ Tarea añadida:
📌 [{nuevo_todo.id}] {content} ({status})

📋 Lista actualizada: {len(self.todos)} tareas totales"""
    
    def todo_update(self, todo_id: int, status: str) -> str:
        """Actualiza el estado de una tarea existente."""
        if status not in self.VALID_STATUSES:
            return f"❌ Error: Estado inválido '{status}'"
        
        for todo in self.todos:
            if todo.id == todo_id:
                old_status = todo.status
                todo.status = status
                todo.updated_at = datetime.now()
                
                return f"""✅ Tarea actualizada:
📌 [{todo_id}] {todo.content}
🔄 Estado: {old_status} → {status}"""
        
        return f"❌ Error: No se encontró tarea con ID {todo_id}"
    
    def todo_delete(self, todo_id: int) -> str:
        """Elimina una tarea de la lista TODO."""
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id:
                deleted = self.todos.pop(i)
                return f"✅ Tarea eliminada: [{todo_id}] {deleted.content}"
        
        return f"❌ Error: No se encontró tarea con ID {todo_id}"
    
    def todo_list(self, status_filter: Optional[str] = None) -> str:
        """Muestra la lista de tareas, opcionalmente filtradas por estado."""
        if not self.todos:
            return "📋 No hay tareas en la lista TODO"
        
        filtradas = self.todos
        if status_filter:
            filtradas = [t for t in filtradas if t.status == status_filter]
        
        if not filtradas:
            return f"📋 No hay tareas con estado '{status_filter}'"
        
        resumen = f"\n📋 LISTA TODO {'(' + status_filter + ')' if status_filter else ''}\n"
        resumen += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for todo in filtradas:
            icon = "✅" if todo.status == "completed" else "🔄" if todo.status == "in_progress" else "⏳"
            resumen += f"  {icon} [{todo.id}] {todo.content}\n"
        
        return resumen.strip()
    
    def _generate_summary(self) -> str:
        """Genera un resumen formateado de la lista TODO."""
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t.status == 'completed')
        in_progress = sum(1 for t in self.todos if t.status == 'in_progress')
        pending = sum(1 for t in self.todos if t.status == 'pending')
        
        resumen = f"""
📋 LISTA TODO ACTUALIZADA
━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total de tareas: {total}
✅ Completadas: {completed}
🔄 En progreso: {in_progress}
⏳ Pendientes: {pending}

📝 TAREAS:
"""
        for todo in self.todos:
            icon = "✅" if todo.status == "completed" else "🔄" if todo.status == "in_progress" else "⏳"
            resumen += f"  {icon} [{todo.id}] {todo.content} ({todo.status})\n"
        
        return resumen.strip()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de las tareas."""
        return {
            "total": len(self.todos),
            "completed": sum(1 for t in self.todos if t.status == 'completed'),
            "in_progress": sum(1 for t in self.todos if t.status == 'in_progress'),
            "pending": sum(1 for t in self.todos if t.status == 'pending'),
            "progress_percentage": round(sum(1 for t in self.todos if t.status == 'completed') / len(self.todos) * 100, 2) if self.todos else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Exporta el estado actual como diccionario."""
        return {
            "todos": [t.to_dict() for t in self.todos],
            "next_id": self.next_id,
            "stats": self.get_stats()
        }
    
    def save_to_file(self, filepath: str) -> bool:
        """Guarda el estado TODO en un archivo JSON."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """Carga el estado TODO desde un archivo JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.todos = [TodoItem.from_dict(t) for t in data.get("todos", [])]
            self.next_id = data.get("next_id", 1)
            return True
        except Exception:
            return False
