# Sistema de Agentes IA para Gestión Documental

Sistema multi-agente especializado para analizar, clasificar, buscar y gestionar documentos locales usando LLMs locales con llama.cpp.

## 🎯 Características Principales

### Agentes Especializados

1. **🔍 FileFinderAgent** - Búsqueda inteligente de archivos
   - Búsqueda recursiva en directorios
   - Filtrado por extensión, nombre, fecha y tamaño
   - Estadísticas y metadatos completos

2. **📖 DocumentReaderAgent** - Lectura multipropósito
   - PDF (con extracción por páginas)
   - OpenDocument (ODT, ODS, ODP, ODG)
   - Microsoft Office (DOCX, XLSX, PPTX)
   - Texto plano (TXT, MD, CSV)

3. **🏷️ DocumentClassifierAgent** - Clasificación automática
   - Detección de categoría (financiero, legal, técnico, etc.)
   - Identificación de idioma
   - Estimación de complejidad
   - Generación de tags automáticos
   - Opción de clasificación con LLM para mayor precisión

4. **🧐 DocumentAnalyzerAgent** - Análisis profundo
   - Resúmenes ejecutivos
   - Extracción de puntos clave
   - Detección de entidades nombradas
   - Identificación de acciones requeridas
   - Comparación entre documentos

5. **📝 DocumentManagerAgent** - Gestión documental
   - Crear nuevos documentos
   - Mover/copiar/renombrar archivos
   - Organizar por tipo
   - Consolidar múltiples documentos
   - Archivar en ZIP

6. **🎼 AgentOrchestrator** - Coordinador central
   - Procesa instrucciones en lenguaje natural
   - Coordina múltiples agentes
   - Retornar respuestas coherentes

## 🚀 Instalación

### Requisitos Previos

```bash
# Python 3.10+
pip install openai  # Para el cliente OpenAI-compatible

# Dependencias adicionales para lectura de documentos
pip install odfpy python-docx openpyxl python-pptx pypdf
```

### Configurar llama.cpp Server

1. Descarga un modelo GGUF:
```bash
# Ejemplo con Mistral-7B-Instruct
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

2. Inicia el servidor:
```bash
# Solo texto
./server -m mistral-7b-instruct-v0.2.Q4_K_M.gguf --port 8081

# Con soporte de visión (imágenes)
./server -m llava-v1.6-34b-q4_k_m.gguf --port 8081 --mmproj llava-mmproj-Q4_K_M.gguf
```

## 💡 Uso Básico

### Configuración del Cliente LLM

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8081/v1",
    api_key="sk-no-key-required",  # No requerida para local
)
```

### Usar el Orquestador

```python
from agents.orchestrator import AgentOrchestrator

# Inicializar
orchestrator = AgentOrchestrator(
    llm_client=client,
    base_directory="/ruta/a/documentos"
)

# Instrucciones en lenguaje natural
result = orchestrator.process_instruction(
    "Busca todos los archivos PDF del directorio"
)

result = orchestrator.process_instruction(
    "Analiza el documento informe_2024.pdf y dame un resumen"
)

result = orchestrator.process_instruction(
    "Clasifica este documento y dime su categoría"
)

result = orchestrator.process_instruction(
    "Crea un reporte con las conclusiones del análisis"
)
```

### Usar Agentes Individualmente

```python
from agents.file_finder import FileFinderAgent
from agents.document_reader import DocumentReaderAgent
from agents.document_classifier import DocumentClassifierAgent

# Buscar archivos
finder = FileFinderAgent("/workspace")
pdf_files = finder.find_by_type('pdf')
stats = finder.get_statistics(pdf_files)

# Leer documento
reader = DocumentReaderAgent()
content = reader.read_document("documento.pdf")
print(content.content)
print(content.metadata)

# Clasificar sin LLM
classifier = DocumentClassifierAgent(llm_client=None)
classification = classifier.classify(content.content, "documento.pdf")
print(f"Categoría: {classification.category}")
print(f"Tags: {classification.tags}")
```

## 📋 Formatos Soportados

| Formato | Extensión | Agente |
|---------|-----------|--------|
| PDF | .pdf | DocumentReaderAgent |
| OpenDocument Text | .odt | DocumentReaderAgent |
| OpenDocument Spreadsheet | .ods | DocumentReaderAgent |
| OpenDocument Presentation | .odp | DocumentReaderAgent |
| OpenDocument Graphics | .odg | DocumentReaderAgent |
| Microsoft Word | .docx | DocumentReaderAgent |
| Microsoft Excel | .xlsx | DocumentReaderAgent |
| Microsoft PowerPoint | .pptx | DocumentReaderAgent |
| Markdown | .md, .markdown | Todos |
| Texto Plano | .txt | Todos |
| CSV | .csv | DocumentReaderAgent |

## 🔧 Ejemplos Detallados

### Búsqueda Avanzada

```python
from agents.file_finder import FileFinderAgent
from datetime import datetime, timedelta

finder = FileFinderAgent("/documents")

# Buscar por patrón
files = finder.search_by_name("informe_*")

# Buscar por tipo y fecha
last_week = datetime.now() - timedelta(days=7)
files = finder.find_files(
    extensions=['pdf', 'odt'],
    modified_after=last_week,
    min_size=1024,  # > 1KB
)

# Obtener estructura del directorio
structure = finder.get_directory_structure(max_depth=2)
```

### Análisis Completo

```python
from agents.document_analyzer import DocumentAnalyzerAgent

analyzer = DocumentAnalyzerAgent(llm_client=client)

# Análisis completo
analysis = analyzer.analyze(content, "archivo.pdf", analysis_type="complete")
print(f"Resumen: {analysis.summary}")
print(f"Puntos clave: {analysis.key_points}")
print(f"Entidades: {analysis.entities}")
print(f"Acciones: {analysis.action_items}")

# Solo resumen
summary = analyzer.analyze(content, analysis_type="summary")

# Responder preguntas
questions = ["¿Cuál es el tema principal?", "¿Hay fechas límite?"]
answers = analyzer.answer_questions(content, questions)
```

### Gestión de Documentos

```python
from agents.document_manager import DocumentManagerAgent

manager = DocumentManagerAgent(base_directory="./output")

# Crear documento
path = manager.create_document(
    content="Contenido del documento...",
    filename="reporte.md",
    directory="reports",
    metadata={'category': 'financiero'}
)

# Organizar archivos
organized = manager.organize_by_type("./downloads")

# Consolidar textos
consolidated = manager.consolidate_texts(
    file_paths=["doc1.txt", "doc2.txt", "doc3.txt"],
    output_filename="consolidado.md"
)

# Archivar
archive = manager.archive_documents(
    file_paths=["doc1.pdf", "doc2.pdf"],
    archive_name="backup.zip"
)
```

## 🎨 Flujo de Trabajo Típico

```python
from openai import OpenAI
from agents.orchestrator import AgentOrchestrator

# 1. Configurar LLM local
client = OpenAI(
    base_url="http://localhost:8081/v1",
    api_key="sk-no-key-required"
)

# 2. Inicializar orquestador
orchestrator = AgentOrchestrator(client, base_directory="/docs")

# 3. Buscar documentos relevantes
result = orchestrator.process_instruction(
    "Encuentra todos los informes técnicos del último mes"
)

# 4. Analizar cada documento
for file_info in result.get('files', []):
    analysis = orchestrator.process_instruction(
        f"Analiza {file_info['path']} y extrae puntos clave"
    )
    print(analysis.get('key_points'))

# 5. Crear reporte consolidado
report = orchestrator.process_instruction(
    "Crea un reporte ejecutivo resumiendo todos los documentos analizados"
)
```

## ⚙️ Configuración con Modelos de Visión

Para documentos con imágenes, gráficos o diagramas:

```python
from openai import OpenAI

# Configurar con modelo multimodal
client = OpenAI(
    base_url="http://localhost:8081/v1",
    api_key="sk-no-key-required"
)

# El DocumentReaderAgent puede extraer información de imágenes
from agents.document_reader import DocumentReaderAgent

reader = DocumentReaderAgent()
content = reader.read_document("documento_con_graficos.pdf")

if content.images_info:
    for img in content.images_info:
        # Usar modelo de visión para analizar imagen
        response = client.chat.completions.create(
            model="llava-model",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe esta imagen"},
                    {"type": "image_url", "image_url": {"url": f"file://{img['name']}"}}
                ]
            }]
        )
```

## 📊 Categorías de Clasificación

El sistema reconoce automáticamente estas categorías:

- **Financiero**: balances, presupuestos, facturas
- **Legal**: contratos, normativas, cláusulas
- **Técnico**: especificaciones, manuales, código
- **Administrativo**: procedimientos, políticas, normas
- **Comercial**: propuestas, ofertas, marketing
- **Recursos Humanos**: empleados, nómina, capacitación
- **Investigación**: estudios, análisis, datos
- **Educativo**: cursos, lecciones, material didáctico

## 🛠️ Solución de Problemas

### Error: "Connection error" al conectar al LLM

```bash
# Verificar que el servidor está corriendo
curl http://localhost:8081/v1/models

# Si no responde, iniciar llama.cpp server
./server -m modelo.gguf --port 8081
```

### Error: "odfpy no está instalado"

```bash
pip install odfpy
```

### Documentos muy grandes

El sistema limita automáticamente el contenido enviado al LLM (3000-4000 caracteres). Para documentos extensos:

```python
# Dividir en chunks
from src.chunker import create_chunks

chunks = create_chunks([document], chunk_size=2000)
for chunk in chunks:
    analysis = analyzer.analyze(chunk.content)
```

## 📝 Licencia

Este sistema es parte del proyecto RAG System y está disponible bajo la misma licencia.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Envía un Pull Request
