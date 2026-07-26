"""
Agente principal para gestión de documentos PDF
Conecta con llama.cpp y proporciona herramientas para análisis de PDFs
"""
import json
import os
import re
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from colorama import Fore, Style, init
import pdfplumber
from pypdf import PdfReader

# Importar configuración - ruta relativa ajustada
try:
    from ...config.settings import (
        LLAMA_SERVER_URL, 
        LLAMA_API_KEY, 
        MODEL_NAME,
        MAX_TOKENS,
        MAX_CONTEXT_CHARS,
        MAX_ITERATIONS,
        COMMAND_TIMEOUT_SECONDS,
        DANGEROUS_COMMANDS,
        OUTPUT_DIR
    )
except ImportError:
    # Fallback para cuando se ejecuta como script principal
    LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://localhost:8081/v1")
    LLAMA_API_KEY = os.getenv("LLAMA_API_KEY", "sk-no-key-required")
    MODEL_NAME = os.getenv("MODEL_NAME", "InternScience/Agents-A1-4B-Q4_K_M-GGUF")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
    MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "8000"))
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))
    COMMAND_TIMEOUT_SECONDS = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "10"))
    DANGEROUS_COMMANDS = ["rm", "sudo", "dd", "chmod", ">", ">>"]
    OUTPUT_DIR = Path("./output")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from .todo_manager import TodoManager
from .reasoning import ReasoningEngine


init(autoreset=True)


class AgentState:
    """Estado actual del agente"""
    def __init__(self):
        self.current_task: Optional[str] = None
        self.iteration_count: int = 0
        self.tools_used: List[str] = []
        self.reasoning_steps: List[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_task": self.current_task,
            "iteration_count": self.iteration_count,
            "tools_used": self.tools_used,
            "reasoning_steps": self.reasoning_steps,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None
        }


class PDFAgent:
    """Agente especializado en gestión de documentos PDF"""
    
    def __init__(self, model_name: str = None):
        self.client = OpenAI(
            base_url=LLAMA_SERVER_URL,
            api_key=LLAMA_API_KEY,
        )
        self.model_name = model_name or MODEL_NAME
        self.todo_manager = TodoManager()
        self.reasoning_engine = ReasoningEngine()
        self.state = AgentState()
        self.historial = []
        self.herramientas_disponibles = self._registrar_herramientas()
        self.herramientas_modelo = self._definir_herramientas_modelo()
        self._inicializar_sistema()
    
    def _inicializar_sistema(self):
        self.historial = [{
            "role": "system",
            "content": (
                "Eres un asistente experto en análisis de documentos PDF. "
                "Tienes herramientas para analizar PDFs individuales o procesar lotes completos. "
                "También tienes herramientas para gestionar listas TODO. "
                "Usa estas herramientas para organizar tareas complejas. "
                "Responde en español. Usa <reasoning> para tu razonamiento interno."
            )
        }]
    
    def _registrar_herramientas(self) -> Dict[str, Callable]:
        return {
            "leer_archivo": self.leer_archivo,
            "listar_archivos": self.listar_archivos,
            "ejecutar_comando_seguro": self.ejecutar_comando_seguro,
            "analizar_pdf": self.analizar_pdf_smart,
            "clasificar_pdfs": self.clasificar_pdfs,
            "buscar_en_pdfs": self.buscar_en_pdfs,
            "resumen_ejecutivo_pdfs": self.resumen_ejecutivo_pdfs,
            "todo_write": self.todo_manager.todo_write,
            "todo_add": self.todo_manager.todo_add,
            "todo_update": self.todo_manager.todo_update,
            "todo_delete": self.todo_manager.todo_delete,
            "todo_list": self.todo_manager.todo_list,
        }
    
    def _definir_herramientas_modelo(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {"name": "leer_archivo", "description": "Lee contenido de archivo.", "parameters": {"type": "object", "properties": {"ruta_archivo": {"type": "string"}}, "required": ["ruta_archivo"]}}},
            {"type": "function", "function": {"name": "listar_archivos", "description": "Lista archivos en directorio.", "parameters": {"type": "object", "properties": {"ruta_directorio": {"type": "string", "default": "."}}}}},
            {"type": "function", "function": {"name": "ejecutar_comando_seguro", "description": "Ejecuta comando seguro.", "parameters": {"type": "object", "properties": {"comando": {"type": "string"}}, "required": ["comando"]}}},
            {"type": "function", "function": {"name": "analizar_pdf", "description": "Analiza PDF extrayendo texto y metadatos.", "parameters": {"type": "object", "properties": {"ruta_pdf": {"type": "string"}, "paginas": {"type": "string", "default": "todas"}, "max_caracteres": {"type": "integer", "default": 8000}}, "required": ["ruta_pdf"]}}},
            {"type": "function", "function": {"name": "clasificar_pdfs", "description": "Clasifica PDFs en directorio.", "parameters": {"type": "object", "properties": {"directorio": {"type": "string"}, "criterio": {"type": "string", "enum": ["tema", "fecha", "tamano", "todos"], "default": "tema"}}, "required": ["directorio"]}}},
            {"type": "function", "function": {"name": "buscar_en_pdfs", "description": "Busca palabra en PDFs.", "parameters": {"type": "object", "properties": {"directorio": {"type": "string"}, "palabra_clave": {"type": "string"}}, "required": ["directorio", "palabra_clave"]}}},
            {"type": "function", "function": {"name": "resumen_ejecutivo_pdfs", "description": "Genera resumen de PDFs.", "parameters": {"type": "object", "properties": {"directorio": {"type": "string"}, "max_pdfs": {"type": "integer", "default": 10}}, "required": ["directorio"]}}},
            {"type": "function", "function": {"name": "todo_write", "description": "Gestiona lista TODO.", "parameters": {"type": "object", "properties": {"todos": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "integer"}, "content": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}}, "required": ["id", "content", "status"]}}}, "required": ["todos"]}}},
            {"type": "function", "function": {"name": "todo_add", "description": "Añade tarea TODO.", "parameters": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "default": "pending"}}, "required": ["content"]}}},
            {"type": "function", "function": {"name": "todo_update", "description": "Actualiza tarea TODO.", "parameters": {"type": "object", "properties": {"todo_id": {"type": "integer"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}}, "required": ["todo_id", "status"]}}},
            {"type": "function", "function": {"name": "todo_list", "description": "Lista tareas TODO.", "parameters": {"type": "object", "properties": {"status_filter": {"type": "string", "enum": ["pending", "in_progress", "completed"]}}}}},
        ]
    
    def leer_archivo(self, ruta_archivo: str) -> str:
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"❌ Error: {e}"
    
    def listar_archivos(self, ruta_directorio: str = ".") -> str:
        try:
            return "\n".join(sorted(os.listdir(ruta_directorio)))
        except Exception as e:
            return f"❌ Error: {e}"
    
    def ejecutar_comando_seguro(self, comando: str) -> str:
        if any(p in comando for p in DANGEROUS_COMMANDS):
            return "⛔ Comando denegado."
        try:
            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECONDS)
            return resultado.stdout or resultado.stderr or "Comando ejecutado."
        except subprocess.TimeoutExpired:
            return "⏰ Timeout."
        except Exception as e:
            return f"❌ Error: {e}"
    
    def obtener_fecha_creacion_pdf(self, ruta_pdf: str) -> str:
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                if pdf.metadata and 'CreationDate' in pdf.metadata:
                    match = re.search(r'D:(\d{4})(\d{2})(\d{2})', pdf.metadata['CreationDate'])
                    if match:
                        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            return datetime.fromtimestamp(os.stat(ruta_pdf).st_ctime).strftime("%Y-%m-%d")
        except:
            return "Fecha desconocida"
    
    def analizar_pdf_avanzado(self, ruta_pdf: str, paginas: str = "todas", max_caracteres: int = 8000) -> str:
        if not os.path.exists(ruta_pdf):
            return f"❌ Error: No existe '{ruta_pdf}'"
        
        texto_extraido = []
        metadatos_info = []
        
        with pdfplumber.open(ruta_pdf) as pdf:
            num_paginas = len(pdf.pages)
            if pdf.metadata:
                metadatos_info.append("📋 METADATOS:")
                for k, v in pdf.metadata.items():
                    metadatos_info.append(f"  {k}: {v}")
            
            rango = range(num_paginas) if paginas == "todas" else self._parse_paginas(paginas, num_paginas)
            
            for i in rango:
                pagina = pdf.pages[i]
                contenido = []
                texto = pagina.extract_text()
                if texto and texto.strip():
                    contenido.append(f"📄 PÁGINA {i+1}:\n{texto.strip()}")
                tablas = pagina.extract_tables()
                if tablas:
                    contenido.append(f"\n📊 TABLAS:")
                    for t in tablas:
                        if t:
                            contenido.append(str(t))
                if contenido:
                    texto_extraido.append("\n".join(contenido))
        
        texto = "\n\n".join(texto_extraido)[:max_caracteres]
        return f"📄 {os.path.basename(ruta_pdf)} | {num_paginas} páginas\n\n{texto}"
    
    def _parse_paginas(self, paginas: str, total: int) -> list:
        result = []
        for parte in paginas.split(','):
            if '-' in parte:
                inicio, fin = map(int, parte.split('-'))
                result.extend(range(max(0, inicio-1), min(total, fin)))
            else:
                idx = int(parte) - 1
                if 0 <= idx < total:
                    result.append(idx)
        return result
    
    def analizar_pdf_basico(self, ruta_pdf: str, paginas: str = "todas", max_caracteres: int = 8000) -> str:
        try:
            lector = PdfReader(ruta_pdf)
            num_paginas = len(lector.pages)
            rango = range(num_paginas) if paginas == "todas" else self._parse_paginas(paginas, num_paginas)
            texto = "\n".join([lector.pages[i].extract_text() or "" for i in rango])[:max_caracteres]
            return f"📄 {os.path.basename(ruta_pdf)} | {num_paginas} páginas\n\n{texto}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def analizar_pdf_smart(self, ruta_pdf: str, paginas: str = "todas", max_caracteres: int = 8000) -> str:
        print(f"{Fore.YELLOW}📄 Analizando PDF...{Style.RESET_ALL}")
        try:
            resultado = self.analizar_pdf_avanzado(ruta_pdf, paginas, max_caracteres)
            print(f"{Fore.GREEN}✅ OK{Style.RESET_ALL}")
            return resultado
        except:
            return self.analizar_pdf_basico(ruta_pdf, paginas, max_caracteres)
    
    def clasificar_pdfs(self, directorio: str, criterio: str = "tema") -> str:
        if not os.path.exists(directorio):
            return f"❌ Error: Directorio no existe"
        
        pdfs = list(Path(directorio).glob("*.pdf"))
        if not pdfs:
            return "📂 No hay PDFs"
        
        docs = []
        for pdf_path in pdfs:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    docs.append({
                        "archivo": pdf_path.name,
                        "paginas": len(pdf.pages),
                        "tamano_kb": round(os.path.getsize(pdf_path) / 1024, 2),
                        "fecha": self.obtener_fecha_creacion_pdf(str(pdf_path)),
                        "titulo": pdf.metadata.get('title', '') if pdf.metadata else '',
                    })
            except:
                continue
        
        if criterio == "fecha":
            docs.sort(key=lambda x: x.get("fecha", ""))
        elif criterio == "tamano":
            docs.sort(key=lambda x: x.get("tamano_kb", 0), reverse=True)
        
        return "\n".join([f"📄 {d['archivo']} | {d['paginas']} págs | {d['tamano_kb']} KB | {d['fecha']}" for d in docs])
    
    def buscar_en_pdfs(self, directorio: str, palabra_clave: str) -> str:
        if not os.path.exists(directorio):
            return "❌ Directorio no existe"
        
        pdfs = list(Path(directorio).glob("*.pdf"))
        resultados = []
        
        for pdf_path in pdfs:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    texto = "\n".join([p.extract_text() or "" for p in pdf.pages])
                    if palabra_clave.lower() in texto.lower():
                        idx = texto.lower().find(palabra_clave.lower())
                        ctx = texto[max(0, idx-100):min(len(texto), idx+200)]
                        resultados.append(f"📄 {pdf_path.name}: ...{ctx}...")
            except:
                continue
        
        return f"✅ Encontrado en {len(resultados)} PDFs\n" + "\n".join(resultados) if resultados else "❌ No encontrado"
    
    def resumen_ejecutivo_pdfs(self, directorio: str, max_pdfs: int = 10) -> str:
        if not os.path.exists(directorio):
            return "❌ Directorio no existe"
        
        pdfs = list(Path(directorio).glob("*.pdf"))[:max_pdfs]
        if not pdfs:
            return "📂 No hay PDFs"
        
        lines = ["📊 RESUMEN EJECUTIVO", "=" * 40]
        total_paginas, total_size = 0, 0
        
        for p in pdfs:
            try:
                with pdfplumber.open(p) as pdf:
                    n = len(pdf.pages)
                    size = round(os.path.getsize(p) / 1024, 2)
                    total_paginas += n
                    total_size += size
                    titulo = pdf.metadata.get('title', p.name) if pdf.metadata else p.name
                    lines.append(f"📄 {titulo} | {n} págs | {size} KB")
            except:
                continue
        
        lines.extend(["=" * 40, f"Total: {len(pdfs)} docs | {total_paginas} págs | {round(total_size/1024, 2)} MB"])
        return "\n".join(lines)
    
    def mostrar_razonamiento(self, texto: str) -> str:
        patrones = [
            (r'<reasoning>(.*?)</reasoning>', Fore.CYAN, "💭 [RAZONAMIENTO]"),
            (r'<thinking>(.*?)</thinking>', Fore.CYAN, "💭 [PENSAMIENTO]"),
        ]
        resultado = ""
        for patron, color, etiqueta in patrones:
            for match in re.findall(patron, texto, re.DOTALL):
                if match.strip():
                    print(f"{color}{etiqueta}\n{match.strip()}\n{Style.RESET_ALL}")
                    self.state.reasoning_steps.append(match.strip())
        return resultado
    
    def procesar_pregunta(self, pregunta: str, max_iteraciones: int = 5) -> Dict[str, Any]:
        self.state = AgentState()
        self.state.start_time = datetime.now()
        self.state.current_task = pregunta
        self.historial.append({"role": "user", "content": pregunta})
        
        respuesta_final = ""
        
        for iteracion in range(max_iteraciones):
            self.state.iteration_count = iteracion + 1
            
            try:
                respuesta = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.historial,
                    tools=self.herramientas_modelo,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=MAX_TOKENS,
                )
            except Exception as e:
                return {"error": str(e), "state": self.state.to_dict()}
            
            mensaje = respuesta.choices[0].message
            contenido = mensaje.content or ""
            
            if contenido:
                self.mostrar_razonamiento(contenido)
                partes = re.split(r'</?(?:reasoning|thinking)>', contenido)
                respuesta_final = "\n".join([p.strip() for p in partes if p.strip() and not re.match(r'^\s*$', p)])
            
            mensaje_dict = mensaje.model_dump()
            if mensaje_dict.get('content'):
                mensaje_dict['content'] = re.sub(r'<[^>]+>', '', mensaje_dict['content'])
            self.historial.append(mensaje_dict)
            
            if not mensaje.tool_calls:
                self.state.end_time = datetime.now()
                return {"respuesta": respuesta_final, "state": self.state.to_dict(), "todo_stats": self.todo_manager.get_stats()}
            
            for tc in mensaje.tool_calls:
                nombre = tc.function.name
                args = json.loads(tc.function.arguments)
                
                print(f"{Fore.YELLOW}🔧 {nombre}({json.dumps(args)}){Style.RESET_ALL}")
                self.state.tools_used.append(nombre)
                
                func = self.herramientas_disponibles.get(nombre)
                resultado = func(**args) if func else f"❌ Herramienta no encontrada"
                
                print(f"{Fore.BLUE}📋 Resultado: {resultado[:200]}{'...' if len(resultado) > 200 else ''}{Style.RESET_ALL}")
                
                self.historial.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": nombre,
                    "content": str(resultado),
                })
        
        self.state.end_time = datetime.now()
        return {"respuesta": respuesta_final, "state": self.state.to_dict(), "todo_stats": self.todo_manager.get_stats()}
    
    def reset(self):
        self._inicializar_sistema()
        self.state = AgentState()
        self.todo_manager = TodoManager()
    
    def get_todo_state(self) -> Dict[str, Any]:
        return self.todo_manager.to_dict()
    
    def save_session(self, filepath: str) -> bool:
        try:
            data = {
                "historial": self.historial,
                "todo_state": self.todo_manager.to_dict(),
                "state": self.state.to_dict(),
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    def load_session(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.historial = data.get("historial", [])
            self.todo_manager.load_from_file(filepath + ".todo.json")
            return True
        except:
            return False
