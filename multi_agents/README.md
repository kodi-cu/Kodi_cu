# Sistema Multi-Agente de Gestión Documental

Sistema multi-agente especializado en análisis, clasificación, búsqueda y gestión de documentos con IA local.

## 🚀 Características Principales

### Agentes Especializados
- **🔍 FileFinderAgent**: Búsqueda inteligente de archivos con cache de intenciones
- **📖 DocumentReaderAgent**: Lectura de PDF, ODT, ODS, ODP, ODG, DOCX, XLSX, PPTX e imágenes
- **🏷️ DocumentClassifierAgent**: Clasificación automática con heurística + LLM (umbral 70%)
- **🧐 DocumentAnalyzerAgent**: Análisis profundo (resúmenes, entidades, Q&A)
- **📝 DocumentManagerAgent**: Crear, modificar, organizar y gestionar documentos
- **🎼 AgentOrchestrator**: Coordinador central con detección de intenciones sin LLM

### Optimizaciones Implementadas
1. **Cache de Intenciones**: Evita llamadas al LLM para consultas comunes (~70-80% menos llamadas)
2. **Clasificación Híbrida**: Heurística por defecto, LLM solo cuando confianza < 70%
3. **Patrones Regex**: Detección de intenciones sin LLM para operaciones comunes

## 📋 Requisitos

- Python 3.8+
- Servidor llama.cpp corriendo localmente (puerto 8081)
- Modelo base: Mistral-7B-Instruct, Phi-3-mini o similar (formato GGUF)
- Modelo de visión: LLaVA o similar (opcional, para análisis de imágenes)

## 🛠️ Instalación

```bash
# Crear entorno virtual
cd /workspace/multi_agents
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 🔧 Configuración del Servidor LLM

### Iniciar llama.cpp server:
```bash
# Descargar modelo (ejemplo: Mistral-7B-Instruct)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Iniciar servidor
./llama-server -m mistral-7b-instruct-v0.2.Q4_K_M.gguf --port 8081 --host 0.0.0.0
```

### Para visión (LLaVA):
```bash
./llama-server -m llava-v1.5-7b.Q4_K_M.gguf --port 8081 --host 0.0.0.0
```

## 💻 Uso

### Modo Interactivo (CLI)

```bash
python cli.py [directorios_de_búsqueda]
```

**Ejemplos:**
```bash
# Búsqueda predeterminada en ./documents y ./
python cli.py

# Búsqueda en directorios específicos
python cli.py /home/user/docs /tmp/archivos
```

**Comandos disponibles en el CLI:**
```
/help              - Muestra ayuda
/search <query>    - Busca archivos (ej: /search pdf contrato)
/read <archivo>    - Lee un documento
/classify <arch>   - Clasifica un documento
/summarize <arch>  - Resume un documento
/analyze <arch>    - Analiza profundamente
/extract <preg>    - Extrae información específica
/create <nombre>   - Crea nuevo documento
/organize [dir]    - Organiza archivos por tipo
/stats             - Muestra estadísticas
/clear             - Limpia el cache
/exit              - Sale del programa
```

### Uso Programático

```python
from openai import OpenAI
from agents.orchestrator import AgentOrchestrator

# Configurar cliente local
client = OpenAI(
    base_url="http://localhost:8081/v1",
    api_key="sk-no-key-required"
)

# Inicializar orquestador
orchestrator = AgentOrchestrator(
    llm_client=client,
    vision_client=client,
    search_paths=["./documents", "./"],
    output_dir="./output"
)

# Ejecutar consultas
result = orchestrator.execute("Busca todos los PDFs de contratos")
print(result)

# Clasificar documento
result = orchestrator.execute("clasifica este documento", file_path="./docs/info.pdf")
print(f"Categoría: {result['category']}, Confianza: {result['confidence']}")

# Analizar documento
result = orchestrator.execute("analiza ./docs/proyecto.pdf")
print(f"Resumen: {result['summary']}")
print(f"Puntos clave: {result['key_points']}")
```

## 📁 Estructura del Proyecto

```
multi_agents/
├── agents/
│   ├── __init__.py
│   ├── file_finder.py       # Búsqueda con cache
│   ├── document_reader.py   # Lectura multi-formato
│   ├── document_classifier.py # Clasificación híbrida
│   ├── document_analyzer.py # Análisis con LLM
│   ├── document_manager.py  # Gestión de archivos
│   └── orchestrator.py      # Coordinador central
├── tools/
│   ├── __init__.py
│   ├── file_utils.py        # Utilidades de archivo
│   ├── pdf_utils.py         # Procesamiento PDF
│   ├── odt_utils.py         # Procesamiento OpenDocument
│   └── vision_utils.py      # Análisis de imágenes
├── config/
│   └── settings.py          # Configuración del sistema
├── cli.py                   # Interfaz de línea de comandos
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## 🎯 Formatos Soportados

| Formato | Lectura | Escritura | Notas |
|---------|---------|-----------|-------|
| PDF | ✅ | ❌ | Extracción de texto y metadatos |
| ODT | ✅ | ❌ | OpenDocument Text |
| ODS | ✅ | ❌ | OpenDocument Spreadsheet |
| ODP | ✅ | ❌ | OpenDocument Presentation |
| ODG | ✅* | ❌ | *Requiere modelo de visión |
| DOCX | ✅ | ❌ | Word moderno |
| XLSX | ✅ | ❌ | Excel moderno |
| PPTX | ✅ | ❌ | PowerPoint moderno |
| TXT/MD | ✅ | ✅ | Texto plano |
| Imágenes | ✅* | ❌ | *Con modelo de visión |

## ⚡ Optimizaciones de Rendimiento

### 1. Cache de Intenciones
- Almacena las últimas 100 consultas
- Detecta patrones comunes sin LLM
- Ahorro estimado: 70-80% menos llamadas al LLM

### 2. Clasificación Híbrida
```python
# Umbral de confianza
HIGH_CONFIDENCE_THRESHOLD = 0.7  # 70%

if heuristic_confidence >= 0.7:
    return heuristic_result  # Sin LLM ✓
elif heuristic_confidence < 0.3:
    return llm_result  # LLM necesario
else:
    return hybrid_result  # Combinación
```

### 3. Patrones Regex Predefinidos
```python
INTENTION_PATTERNS = {
    'search_pdf': [r'busc.*pdf', r'find.*pdf', ...],
    'classify': [r'clasific.*', r'categor.*', ...],
    'summarize': [r'resum.*', r'puntos.*clave', ...]
}
```

## 🔒 Consideraciones de Seguridad

- Todo se ejecuta localmente (sin envío de datos a la nube)
- Los archivos no se modifican sin autorización explícita
- El cache se limpia automáticamente al salir

## 🐛 Solución de Problemas

### Error: "No se pudo conectar al servidor LLM"
```bash
# Verificar que llama-server esté corriendo
ps aux | grep llama-server

# Reiniciar servidor
./llama-server -m tu-modelo.gguf --port 8081
```

### Error: "Formato no soportado"
- Verifica que el archivo tenga una extensión válida
- Algunos formatos antiguos (.doc, .xls) requieren conversión previa

### Error: "Memory error" con archivos grandes
- El sistema limita automáticamente el contenido a 8000-10000 caracteres
- Usa `/summarize` para obtener resúmenes de documentos extensos

## 📊 Métricas de Rendimiento

| Escenario | Sin Optimización | Con Optimización | Mejora |
|-----------|------------------|------------------|--------|
| Búsqueda simple | 1 llamada LLM | 0 llamadas LLM | 100% |
| Clasificación clara | 1 llamada LLM | 0 llamadas LLM | 100% |
| Clasificación ambigua | 1 llamada LLM | 1 llamada LLM | 0% |
| Promedio estimado | 1.0 llamadas | 0.2-0.3 llamadas | 70-80% |

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

## 🙏 Créditos

- **llama.cpp**: Inferencia local de modelos LLM
- **OpenAI API**: Compatibilidad con cliente estándar
- **Comunidad**: Contribuciones y feedback

---

**Hecho con ❤️ para gestión documental eficiente y privada**
