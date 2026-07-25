import json
import os
import subprocess
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from colorama import init, Fore, Style
from pypdf import PdfReader
import pdfplumber

# Inicializar colorama
init(autoreset=True)

# --- 1. CONFIGURACIÓN ---
client = OpenAI(
    base_url="http://localhost:8081/v1",
    api_key="sk-no-key-required",
)

# --- 1.5. ESTADO DE TODOS ---
todos_state = {
    "todos": [],
    "next_id": 1
}

# --- 2. FUNCIONES BÁSICAS (Siempre disponibles) ---
def leer_archivo(ruta_archivo: str) -> str:
    """Lee el contenido de un archivo de texto."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error al leer el archivo: {e}"

def listar_archivos(ruta_directorio: str = ".") -> str:
    """Lista los archivos y carpetas en un directorio."""
    try:
        return "\n".join(os.listdir(ruta_directorio))
    except Exception as e:
        return f"Error al listar el directorio: {e}"

def ejecutar_comando_seguro(comando: str) -> str:
    """Ejecuta un comando en la terminal de forma segura."""
    comandos_peligrosos = ["rm", "sudo", "dd", "chmod", ">", ">>"]
    if any(peligroso in comando for peligroso in comandos_peligrosos):
        return "⛔ Comando denegado por razones de seguridad."
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=10)
        return resultado.stdout or resultado.stderr or "Comando ejecutado sin salida."
    except subprocess.TimeoutExpired:
        return "⏰ El comando tardó demasiado en ejecutarse."

# --- 2.5. FUNCIONES DE TODO ---
def todo_write(todos: List[Dict[str, Any]]) -> str:
    """
    Crea o actualiza la lista completa de tareas TODO.

    Args:
        todos: Lista de tareas con formato [{"id": 1, "content": "tarea", "status": "pending"}]

    Returns:
        Resumen del estado de la lista TODO
    """
    try:
        # Validar formato
        if not todos or not isinstance(todos, list):
            return "❌ Error: 'todos' debe ser una lista de tareas"

        # Validar cada tarea
        for todo in todos:
            if not all(k in todo for k in ["id", "content", "status"]):
                return "❌ Error: Cada tarea debe tener 'id', 'content' y 'status'"
            if todo["status"] not in ["pending", "in_progress", "completed"]:
                return f"❌ Error: Estado inválido '{todo['status']}'. Usa pending, in_progress o completed"

        # Actualizar estado global
        global todos_state
        todos_state["todos"] = todos
        todos_state["next_id"] = max([t["id"] for t in todos]) + 1 if todos else 1

        # Generar resumen
        resumen = f"""
📋 LISTA TODO ACTUALIZADA
━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total de tareas: {len(todos)}
✅ Completadas: {sum(1 for t in todos if t['status'] == 'completed')}
🔄 En progreso: {sum(1 for t in todos if t['status'] == 'in_progress')}
⏳ Pendientes: {sum(1 for t in todos if t['status'] == 'pending')}

📝 TAREAS:
"""
        for todo in todos:
            icon = "✅" if todo["status"] == "completed" else "🔄" if todo["status"] == "in_progress" else "⏳"
            resumen += f"  {icon} [{todo['id']}] {todo['content']} ({todo['status']})\n"

        return resumen.strip()

    except Exception as e:
        return f"❌ Error al gestionar TODOs: {str(e)}"

def todo_add(content: str, status: str = "pending") -> str:
    """Añade una nueva tarea a la lista TODO."""
    global todos_state

    nuevo_todo = {
        "id": todos_state["next_id"],
        "content": content,
        "status": status
    }

    todos_state["todos"].append(nuevo_todo)
    todos_state["next_id"] += 1

    return f"""✅ Tarea añadida:
📌 [{nuevo_todo['id']}] {content} ({status})

📋 Lista actualizada: {len(todos_state['todos'])} tareas totales"""

def todo_update(todo_id: int, status: str) -> str:
    """Actualiza el estado de una tarea existente."""
    global todos_state

    for todo in todos_state["todos"]:
        if todo["id"] == todo_id:
            if status not in ["pending", "in_progress", "completed"]:
                return f"❌ Error: Estado inválido '{status}'"

            old_status = todo["status"]
            todo["status"] = status

            return f"""✅ Tarea actualizada:
📌 [{todo_id}] {todo['content']}
🔄 Estado: {old_status} → {status}"""

    return f"❌ Error: No se encontró tarea con ID {todo_id}"

def todo_list(status_filter: str = None) -> str:
    """Muestra la lista de tareas, opcionalmente filtradas por estado."""
    global todos_state

    if not todos_state["todos"]:
        return "📋 No hay tareas en la lista TODO"

    filtradas = todos_state["todos"]
    if status_filter:
        filtradas = [t for t in filtradas if t["status"] == status_filter]

    if not filtradas:
        return f"📋 No hay tareas con estado '{status_filter}'"

    resumen = f"""
📋 LISTA TODO {'(' + status_filter + ')' if status_filter else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    for todo in filtradas:
        icon = "✅" if todo["status"] == "completed" else "🔄" if todo["status"] == "in_progress" else "⏳"
        resumen += f"  {icon} [{todo['id']}] {todo['content']}\n"

    return resumen.strip()

# --- 3. FUNCIONES DE PDF (Versión SMART) ---
def obtener_fecha_creacion_pdf(ruta_pdf):
    """Obtiene la fecha de creación del PDF desde múltiples fuentes."""
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            if pdf.metadata and 'CreationDate' in pdf.metadata:
                fecha_str = pdf.metadata['CreationDate']
                match = re.search(r'D:(\d{4})(\d{2})(\d{2})', fecha_str)
                if match:
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        stats = os.stat(ruta_pdf)
        return datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d")
    except:
        return "Fecha desconocida"

def analizar_pdf_avanzado(ruta_pdf: str, paginas: str = "todas", max_caracteres: int = 8000) -> str:
    """Versión avanzada con pdfplumber."""
    try:
        if not os.path.exists(ruta_pdf):
            return f"❌ Error: No se encontró el archivo '{ruta_pdf}'"

        texto_extraido = []
        metadatos_info = []

        with pdfplumber.open(ruta_pdf) as pdf:
            num_paginas = len(pdf.pages)

            # Metadatos
            if pdf.metadata:
                metadatos_info.append("📋 METADATOS:")
                for clave, valor in pdf.metadata.items():
                    metadatos_info.append(f"  {clave}: {valor}")
                metadatos_info.append("")

            # Determinar páginas
            if paginas == "todas":
                rango_paginas = range(num_paginas)
            else:
                paginas_seleccionadas = []
                for parte in paginas.split(','):
                    if '-' in parte:
                        inicio, fin = map(int, parte.split('-'))
                        paginas_seleccionadas.extend(range(max(0, inicio-1), min(num_paginas, fin)))
                    else:
                        idx = int(parte) - 1
                        if 0 <= idx < num_paginas:
                            paginas_seleccionadas.append(idx)
                rango_paginas = paginas_seleccionadas

            # Extraer contenido
            for i in rango_paginas:
                pagina = pdf.pages[i]
                contenido_pagina = []

                texto = pagina.extract_text()
                if texto and texto.strip():
                    contenido_pagina.append(f"📄 PÁGINA {i+1} - TEXTO:")
                    contenido_pagina.append(texto.strip())

                tablas = pagina.extract_tables()
                if tablas:
                    contenido_pagina.append(f"\n📊 TABLAS EN PÁGINA {i+1}:")
                    for num_tabla, tabla in enumerate(tablas, 1):
                        if tabla and len(tabla) > 0:
                            contenido_pagina.append(f"  Tabla {num_tabla}:")
                            for fila in tabla:
                                if fila and any(cell for cell in fila if cell):
                                    fila_limpia = [str(cell) if cell else "" for cell in fila]
                                    contenido_pagina.append(f"    {' | '.join(fila_limpia)}")

                if pagina.images:
                    contenido_pagina.append(f"\n🖼️ PÁGINA {i+1} contiene {len(pagina.images)} imágenes")

                texto_extraido.append("\n".join(contenido_pagina))

        texto_completo = "\n\n".join(texto_extraido)
        if len(texto_completo) > max_caracteres:
            texto_completo = texto_completo[:max_caracteres] + "\n... [TRUNCADO]"

        respuesta = f"""
📄 ANÁLISIS DEL PDF: {os.path.basename(ruta_pdf)}
📊 Total de páginas: {num_paginas}
📖 Páginas extraídas: {len(rango_paginas)}
📝 Caracteres extraídos: {len(texto_completo)}

{chr(10).join(metadatos_info) if metadatos_info else ''}
--- CONTENIDO ---
{texto_completo}
"""
        return respuesta.strip()
    except Exception as e:
        raise e

def analizar_pdf_basico(ruta_pdf: str, paginas: str = "todas", max_caracteres: int = 8000) -> str:
    """Versión básica con pypdf (fallback)."""
    try:
        if not os.path.exists(ruta_pdf):
            return f"❌ Error: No se encontró el archivo '{ruta_pdf}'"

        lector = PdfReader(ruta_pdf)
        num_paginas = len(lector.pages)

        if paginas == "todas":
            rango_paginas = range(num_paginas)
        else:
            paginas_seleccionadas = []
            for parte in paginas.split(','):
                if '-' in parte:
                    inicio, fin = map(int, parte.split('-'))
                    paginas_seleccionadas.extend(range(inicio-1, fin))
                else:
                    paginas_seleccionadas.append(int(parte)-1)
            rango_paginas = paginas_seleccionadas

        texto_extraido = []
        for i in rango_paginas:
            if i < num_paginas:
                pagina = lector.pages[i]
                texto = pagina.extract_text()
                if texto.strip():
                    texto_extraido.append(f"--- Página {i+1} ---\n{texto}")

        texto_completo = "\n\n".join(texto_extraido)
        if len(texto_completo) > max_caracteres:
            texto_completo = texto_completo[:max_caracteres] + "\n... [TRUNCADO]"

        return f"""
📄 ANÁLISIS BÁSICO DEL PDF: {os.path.basename(ruta_pdf)}
📊 Total de páginas: {num_paginas}
📖 Páginas extraídas: {len(rango_paginas)}

--- CONTENIDO ---
{texto_completo}
""".strip()
    except Exception as e:
        return f"❌ Error en análisis básico: {str(e)}"

def analizar_pdf_smart(ruta_pdf: str, paginas: str = "todas", max_caracteres: int = 8000) -> str:
    """Función SMART que usa pdfplumber y fallback a pypdf."""
    print(f"{Fore.YELLOW}📄 Intentando analizar PDF con pdfplumber...{Style.RESET_ALL}")
    try:
        resultado = analizar_pdf_avanzado(ruta_pdf, paginas, max_caracteres)
        print(f"{Fore.GREEN}✅ PDF analizado con pdfplumber{Style.RESET_ALL}")
        return resultado
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ Falló pdfplumber: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔄 Usando pypdf como fallback...{Style.RESET_ALL}")
        resultado = analizar_pdf_basico(ruta_pdf, paginas, max_caracteres)
        if "❌ Error" not in resultado:
            print(f"{Fore.GREEN}✅ PDF analizado con pypdf (fallback){Style.RESET_ALL}")
        return resultado

# --- 4. FUNCIONES PARA MÚLTIPLES PDFS (CLASIFICACIÓN) ---
def clasificar_pdfs(directorio: str, criterio: str = "tema") -> str:
    """Escanea y clasifica todos los PDFs en un directorio."""
    if not os.path.exists(directorio):
        return f"❌ Error: El directorio '{directorio}' no existe"

    pdfs = list(Path(directorio).glob("*.pdf"))
    if not pdfs:
        return f"📂 No se encontraron archivos PDF en '{directorio}'"

    print(f"{Fore.YELLOW}📊 Escaneando {len(pdfs)} PDFs...{Style.RESET_ALL}")

    documentos = []
    for i, pdf_path in enumerate(pdfs, 1):
        print(f"{Fore.YELLOW}  Procesando {i}/{len(pdfs)}: {pdf_path.name}{Style.RESET_ALL}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadatos = {
                    "archivo": pdf_path.name,
                    "paginas": len(pdf.pages),
                    "tamano_kb": round(os.path.getsize(pdf_path) / 1024, 2),
                    "fecha_creacion": obtener_fecha_creacion_pdf(str(pdf_path)),
                }

                if pdf.metadata:
                    for key, value in pdf.metadata.items():
                        if key not in ['CreationDate', 'ModDate']:
                            metadatos[key.lower()] = value

                # Extraer muestra de texto para clasificación
                texto_inicial = ""
                for pagina in pdf.pages[:2]:
                    texto = pagina.extract_text()
                    if texto:
                        texto_inicial += texto[:300] + "\n"
                metadatos["muestra_texto"] = texto_inicial[:500]

                documentos.append(metadatos)
        except:
            continue

    # Clasificar según criterio
    if criterio == "fecha":
        clasificados = sorted(documentos, key=lambda x: x.get("fecha_creacion", "0000-00-00"))
        resumen = "📅 CLASIFICACIÓN POR FECHA DE CREACIÓN:\n\n"
        for doc in clasificados:
            resumen += f"  📄 {doc['archivo']} -> {doc.get('fecha_creacion', 'Desconocida')}\n"
            if 'title' in doc:
                resumen += f"     Título: {doc['title']}\n"

    elif criterio == "tamano":
        clasificados = sorted(documentos, key=lambda x: x.get("tamano_kb", 0), reverse=True)
        resumen = "📊 CLASIFICACIÓN POR TAMAÑO:\n\n"
        for doc in clasificados:
            resumen += f"  📄 {doc['archivo']} -> {doc.get('tamano_kb', 0):.1f} KB\n"

    else:  # "tema" o "todos"
        resumen = f"🔍 CLASIFICACIÓN DE {len(documentos)} PDFs:\n\n"
        for doc in documentos:
            resumen += f"--- {doc['archivo']} ---\n"
            resumen += f"  📅 Fecha: {doc.get('fecha_creacion', 'Desconocida')}\n"
            resumen += f"  📄 Páginas: {doc.get('paginas', '?')}\n"
            resumen += f"  📏 Tamaño: {doc.get('tamano_kb', 0):.1f} KB\n"
            if 'title' in doc:
                resumen += f"  📌 Título: {doc['title']}\n"
            if 'author' in doc:
                resumen += f"  ✍️ Autor: {doc['author']}\n"
            resumen += f"  📝 Muestra: {doc.get('muestra_texto', '')[:150]}...\n\n"

    return resumen

def buscar_en_pdfs(directorio: str, palabra_clave: str) -> str:
    """Busca una palabra clave en todos los PDFs de un directorio."""
    if not os.path.exists(directorio):
        return f"❌ Error: El directorio '{directorio}' no existe"

    pdfs = list(Path(directorio).glob("*.pdf"))
    if not pdfs:
        return f"📂 No se encontraron archivos PDF en '{directorio}'"

    print(f"{Fore.YELLOW}🔍 Buscando '{palabra_clave}' en {len(pdfs)} PDFs...{Style.RESET_ALL}")

    resultados = []
    for pdf_path in pdfs:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                texto_completo = ""
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo += texto

                if palabra_clave.lower() in texto_completo.lower():
                    idx = texto_completo.lower().find(palabra_clave.lower())
                    inicio = max(0, idx - 150)
                    fin = min(len(texto_completo), idx + 250)
                    contexto = texto_completo[inicio:fin]

                    resultados.append({
                        "archivo": pdf_path.name,
                        "contexto": contexto,
                        "fecha": obtener_fecha_creacion_pdf(str(pdf_path))
                    })
        except:
            continue

    if resultados:
        resumen = f"🔎 RESULTADOS PARA '{palabra_clave}' ({len(resultados)} coincidencias):\n\n"
        for r in resultados:
            resumen += f"📄 {r['archivo']} (Fecha: {r['fecha']})\n"
            resumen += f"  ...{r['contexto']}...\n\n"
        return resumen
    else:
        return f"🔎 No se encontraron coincidencias para '{palabra_clave}'"

def resumen_ejecutivo_pdfs(directorio: str, max_pdfs: int = 10) -> str:
    """Genera un resumen rápido de los PDFs en un directorio."""
    if not os.path.exists(directorio):
        return f"❌ Error: El directorio '{directorio}' no existe"

    pdfs = list(Path(directorio).glob("*.pdf"))[:max_pdfs]
    if not pdfs:
        return f"📂 No se encontraron archivos PDF en '{directorio}'"

    resumen = f"📊 RESUMEN EJECUTIVO DE {len(pdfs)} PDFs:\n\n"

    for pdf_path in pdfs:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                resumen += f"--- {pdf_path.name} ---\n"
                resumen += f"  📅 Fecha: {obtener_fecha_creacion_pdf(str(pdf_path))}\n"
                resumen += f"  📄 Páginas: {len(pdf.pages)}\n"
                resumen += f"  📏 Tamaño: {round(os.path.getsize(pdf_path) / 1024, 2)} KB\n"

                if pdf.metadata and 'title' in pdf.metadata:
                    resumen += f"  📌 Título: {pdf.metadata['title']}\n"

                if len(pdf.pages) > 0:
                    texto = pdf.pages[0].extract_text()
                    if texto:
                        lines = texto.split('\n')[:2]
                        resumen += f"  📝 Inicio: {' '.join(lines)[:100]}...\n"
                resumen += "\n"
        except:
            resumen += f"--- {pdf_path.name} ---\n"
            resumen += "  ❌ No se pudo procesar este PDF\n\n"

    return resumen

# --- 5. DICCIONARIO DE HERRAMIENTAS UNIFICADO ---
herramientas_disponibles = {
    # Herramientas básicas
    "leer_archivo": leer_archivo,
    "listar_archivos": listar_archivos,
    "ejecutar_comando_seguro": ejecutar_comando_seguro,

    # Herramientas de PDF individual
    "analizar_pdf": analizar_pdf_smart,

    # Herramientas para múltiples PDFs
    "clasificar_pdfs": clasificar_pdfs,
    "buscar_en_pdfs": buscar_en_pdfs,
    "resumen_ejecutivo_pdfs": resumen_ejecutivo_pdfs,

    # Herramientas TODO
    "todo_write": todo_write,
    "todo_add": todo_add,
    "todo_update": todo_update,
    "todo_list": todo_list,
}

# --- 6. ESQUEMA DE HERRAMIENTAS PARA EL MODELO ---
herramientas_modelo = [
    # Herramientas básicas
    {
        "type": "function",
        "function": {
            "name": "leer_archivo",
            "description": "Lee el contenido de un archivo de texto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta_archivo": {"type": "string", "description": "Ruta al archivo"}
                },
                "required": ["ruta_archivo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_archivos",
            "description": "Lista los archivos en un directorio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta_directorio": {"type": "string", "description": "Ruta al directorio", "default": "."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_comando_seguro",
            "description": "Ejecuta un comando en terminal (comandos peligrosos bloqueados).",
            "parameters": {
                "type": "object",
                "properties": {
                    "comando": {"type": "string", "description": "Comando a ejecutar"}
                },
                "required": ["comando"]
            }
        }
    },
    # Herramienta PDF individual
    {
        "type": "function",
        "function": {
            "name": "analizar_pdf",
            "description": "Analiza un PDF individual extrayendo texto, tablas y metadatos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta_pdf": {"type": "string", "description": "Ruta al archivo PDF"},
                    "paginas": {"type": "string", "description": "Páginas a extraer: 'todas', '1-5', o '1,3,5'", "default": "todas"},
                    "max_caracteres": {"type": "integer", "description": "Máximo de caracteres", "default": 8000}
                },
                "required": ["ruta_pdf"]
            }
        }
    },
    # Herramientas para múltiples PDFs
    {
        "type": "function",
        "function": {
            "name": "clasificar_pdfs",
            "description": "Escanea un directorio y clasifica todos los PDFs por tema, fecha o tamaño.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directorio": {"type": "string", "description": "Directorio con los PDFs"},
                    "criterio": {"type": "string", "description": "'tema', 'fecha', 'tamano' o 'todos'", "enum": ["tema", "fecha", "tamano", "todos"], "default": "tema"}
                },
                "required": ["directorio"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_en_pdfs",
            "description": "Busca una palabra clave en todos los PDFs de un directorio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directorio": {"type": "string", "description": "Directorio con los PDFs"},
                    "palabra_clave": {"type": "string", "description": "Palabra o frase a buscar"}
                },
                "required": ["directorio", "palabra_clave"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_ejecutivo_pdfs",
            "description": "Genera un resumen rápido con información clave de los PDFs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directorio": {"type": "string", "description": "Directorio con los PDFs"},
                    "max_pdfs": {"type": "integer", "description": "Máximo de PDFs a procesar", "default": 10}
                },
                "required": ["directorio"]
            }
        }
    },
    # Herramientas TODO
    {
        "type": "function",
        "function": {
            "name": "todo_write",
            "description": "Crea o actualiza la lista completa de tareas TODO. Útil para organizar trabajo complejo y hacer seguimiento de progreso.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "description": "Lista de tareas",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "description": "ID único de la tarea"},
                                "content": {"type": "string", "description": "Descripción de la tarea"},
                                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Estado de la tarea"}
                            },
                            "required": ["id", "content", "status"]
                        }
                    }
                },
                "required": ["todos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "todo_add",
            "description": "Añade una nueva tarea a la lista TODO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Descripción de la tarea"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Estado inicial de la tarea", "default": "pending"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "todo_update",
            "description": "Actualiza el estado de una tarea existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "ID de la tarea a actualizar"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Nuevo estado de la tarea"}
                },
                "required": ["todo_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "todo_list",
            "description": "Muestra la lista de tareas, opcionalmente filtradas por estado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Filtro por estado (opcional)"}
                }
            }
        }
    }
]

# --- 7. FUNCIONES DE VISUALIZACIÓN ---
def mostrar_razonamiento(texto: str) -> str:
    """Procesa y muestra el razonamiento del modelo."""
    patrones = [
        (r'<reasoning>(.*?)</reasoning>', Fore.CYAN, "💭 [RAZONAMIENTO]"),
        (r'<thinking>(.*?)</thinking>', Fore.CYAN, "💭 [PENSAMIENTO]"),
        (r'<analysis>(.*?)</analysis>', Fore.CYAN, "📊 [ANÁLISIS]"),
        (r'<tool_call>(.*?)</tool_call>', Fore.YELLOW, "🔧 [LLAMADA A HERRAMIENTA]"),
        (r'<action>(.*?)</action>', Fore.YELLOW, "⚡ [ACCIÓN]"),
        (r'(?s)(.*?)(?=<tool_call>|<reasoning>|<thinking>|<analysis>|<action>|$)', Fore.GREEN, "💬 [RESPUESTA]"),
    ]

    texto_procesado = texto
    resultado_final = ""

    for patron, color, etiqueta in patrones:
        coincidencias = re.findall(patron, texto_procesado, re.DOTALL)
        if coincidencias:
            for contenido in coincidencias:
                contenido_limpio = contenido.strip()
                if contenido_limpio:
                    if "RESPUESTA" in etiqueta:
                        if contenido_limpio and not re.match(r'^\s*$', contenido_limpio):
                            print(f"{color}{etiqueta}\n{contenido_limpio}\n{Style.RESET_ALL}")
                            resultado_final = contenido_limpio
                    else:
                        print(f"{color}{etiqueta}\n{contenido_limpio}\n{Style.RESET_ALL}")
                texto_procesado = texto_procesado.replace(contenido, '')

    return resultado_final

# --- 8. FUNCIÓN PRINCIPAL ---
def procesar_pregunta(mensajes, max_iteraciones=5):
    """Procesa una pregunta mostrando razonamiento y ejecutando herramientas."""
    for iteracion in range(max_iteraciones):
        print(f"{Fore.MAGENTA}━━━ Iteración {iteracion+1} ━━━{Style.RESET_ALL}")

        try:
            respuesta = client.chat.completions.create(
                model="InternScience/Agents-A1-4B-Q4_K_M-GGUF",
                messages=mensajes,
                tools=herramientas_modelo,
                tool_choice="auto",
                temperature=0.85,
                top_p=0.95,
                presence_penalty=1.1,
            )
        except Exception as e:
            print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Asegúrate de que llama-server esté corriendo en http://localhost:8081{Style.RESET_ALL}")
            return

        mensaje_respuesta = respuesta.choices[0].message
        contenido_respuesta = mensaje_respuesta.content or ""

        if contenido_respuesta:
            print(f"{Fore.CYAN}🧠 [PENSAMIENTO DEL MODELO]{Style.RESET_ALL}")
            respuesta_final = mostrar_razonamiento(contenido_respuesta)

        mensaje_limpio = mensaje_respuesta.model_dump()
        if mensaje_limpio.get('content'):
            contenido_limpio = re.sub(r'<[^>]+>', '', mensaje_limpio['content'])
            mensaje_limpio['content'] = contenido_limpio.strip()

        mensajes.append(mensaje_limpio)

        if not mensaje_respuesta.tool_calls:
            print(f"\n{Fore.GREEN}✅ [RESPUESTA FINAL]{Style.RESET_ALL}")
            if not respuesta_final and contenido_respuesta:
                print(contenido_respuesta)
            return

        for tool_call in mensaje_respuesta.tool_calls:
            nombre = tool_call.function.name
            argumentos = json.loads(tool_call.function.arguments)

            print(f"{Fore.YELLOW}🔧 [EJECUTANDO HERRAMIENTA]\n{nombre}({json.dumps(argumentos, indent=2)}){Style.RESET_ALL}")

            funcion = herramientas_disponibles.get(nombre)
            if funcion:
                try:
                    print(f"{Fore.YELLOW}⏳ Ejecutando...{Style.RESET_ALL}")
                    inicio = time.time()
                    resultado = funcion(**argumentos)
                    fin = time.time()
                    print(f"{Fore.GREEN}✅ Completado en {fin - inicio:.2f}s{Style.RESET_ALL}")
                except Exception as e:
                    resultado = f"❌ Error: {e}"
                    print(f"{Fore.RED}{resultado}{Style.RESET_ALL}")
            else:
                resultado = f"❌ Herramienta '{nombre}' no encontrada"
                print(f"{Fore.RED}{resultado}{Style.RESET_ALL}")

            resultado_mostrar = resultado[:500] + ('...' if len(resultado) > 500 else '')
            print(f"{Fore.BLUE}📋 [RESULTADO]\n{resultado_mostrar}{Style.RESET_ALL}")

            mensajes.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": nombre,
                "content": str(resultado),
            })

        print(f"{Fore.MAGENTA}{'━' * 50}{Style.RESET_ALL}")

# --- 9. BUCLE PRINCIPAL ---
if __name__ == "__main__":
    print(f"{Fore.CYAN}🚀 Agente Agents-A1-4B UNIFICADO con TODO List{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📂 Herramientas:{Style.RESET_ALL}")
    print(f"  • Básicas: leer_archivo, listar_archivos, ejecutar_comando_seguro")
    print(f"  • PDF individual: analizar_pdf")
    print(f"  • Múltiples PDFs: clasificar_pdfs, buscar_en_pdfs, resumen_ejecutivo_pdfs")
    print(f"  • Gestión TODO: todo_write, todo_add, todo_update, todo_list")
    print(f"{Fore.GREEN}💬 Escribe 'salir' para terminar{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'═' * 60}{Style.RESET_ALL}\n")

    historial = [
        {
            "role": "system",
            "content": (
                "Eres un asistente experto en análisis de documentos PDF. "
                "Tienes herramientas para analizar PDFs individuales o procesar lotes completos. "
                "También tienes herramientas para gestionar listas TODO (todo_write, todo_add, todo_update, todo_list). "
                "Usa estas herramientas para organizar tareas complejas, hacer seguimiento de progreso, "
                "y mantener al usuario informado de los pasos que estás siguiendo. "
                "Cuando tengas múltiples tareas que realizar, crea una lista TODO para organizarlas. "
                "Actualiza el estado de las tareas a medida que avanzas. "
                "Responde en español. Usa <reasoning> para tu razonamiento."
            )
        }
    ]

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

        historial.append({"role": "user", "content": pregunta})
        procesar_pregunta(historial)
        print(f"{Fore.MAGENTA}{'═' * 60}{Style.RESET_ALL}\n")
