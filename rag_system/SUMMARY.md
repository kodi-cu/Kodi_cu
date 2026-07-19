# Sistema RAG Local - Resumen Ejecutivo

## 📁 Estructura del Proyecto Entregado

```
/workspace/rag_system/
├── README.md                    # Documentación completa
├── QUICKSTART.md                # Guía rápida de inicio
├── requirements.txt             # Dependencias Python
├── example_usage.py             # Script de ejemplo completo
├── cli.py                       # Interfaz de línea de comandos
├── api.py                       # API REST con FastAPI
│
├── config/
│   ├── __init__.py
│   ├── .env.example             # Plantilla de configuración
│   └── settings.py              # Módulo de configuración
│
├── src/
│   ├── __init__.py
│   ├── document_loader.py       # Carga de PDF, TXT, Markdown
│   ├── chunker.py               # Chunking inteligente recursivo
│   ├── embeddings.py            # Generación con sentence-transformers
│   ├── vector_store.py          # ChromaDB para almacenamiento vectorial
│   ├── llm.py                   # LLM local con llama-cpp-python
│   └── pipeline.py              # Pipeline RAG completo
│
├── docs/
│   └── python_intro.md          # Documento de ejemplo
│
├── models/                      # (vacío - descargar modelo GGUF)
├── vector_store/                # (se llena al indexar)
└── cache/                       # (se llena con embeddings cacheados)
```

## 🎯 Componentes Principales

### 1. `document_loader.py` - Carga de Documentos
**Funciones:**
- `load_pdf()` - Extrae texto de PDFs página por página
- `load_txt()` - Carga archivos de texto plano
- `load_markdown()` - Carga archivos Markdown preservando estructura
- `load_documents()` - Carga masiva desde directorio

**Manejo de tablas/listas:**
- Mantiene saltos de línea y separadores
- Preserva estructura de listas Markdown
- Para tablas complejas en PDF, recomienda chunk más grande

### 2. `chunker.py` - División Inteligente
**Estrategia recursiva:**
1. Intenta dividir por párrafos (doble salto de línea)
2. Si no, divide por oraciones
3. Como último recurso, divide por palabras

**Funciones clave:**
- `create_chunks()` - Función principal con solapamiento
- `create_chunks_recursive()` - Algoritmo semántico
- `merge_small_chunks()` - Fusiona chunks muy pequeños

**Parámetros recomendados:**
- `CHUNK_SIZE=500` tokens
- `CHUNK_OVERLAP=50` tokens (10%)

### 3. `embeddings.py` - Generación de Embeddings
**Características:**
- Usa `sentence-transformers` (all-MiniLM-L6-v2)
- Caché persistente para evitar reprocesamiento
- Soporte para procesamiento por lotes

**Clases:**
- `EmbeddingCache` - Sistema de caché en disco
- `EmbeddingGenerator` - Wrapper de sentence-transformers

### 4. `vector_store.py` - Base de Datos Vectorial
**Por qué ChromaDB:**
- Persistencia nativa en disco
- API simple Python-first
- Búsqueda por similitud coseno eficiente
- Filtrado por metadatos

**Funciones principales:**
- `add_documents()` - Agrega embeddings y documentos
- `retrieve()` - Búsqueda por similitud
- `retrieve_with_scores()` - Con umbral de calidad
- `delete_by_metadata()` - Eliminación selectiva

### 5. `llm.py` - Modelo de Lenguaje Local
**Soporta:**
- Mistral-7B-Instruct (template automático)
- Llama-3-8B-Instruct (template automático)
- Phi-3-mini (template automático)
- Cualquier modelo GGUF

**Características:**
- Templates de prompt específicos por modelo
- Offload parcial a GPU configurable
- Modo streaming disponible
- Control de temperatura, top_p, repeat_penalty

**Prompt engineering para contexto:**
```
[INST] Eres un asistente útil que responde basándose en el contexto.

<contexto>
{chunks con fuentes y scores}
</contexto>

Usa ÚNICAMENTE la información del contexto...
Pregunta: {question}
Respuesta: [/INST]
```

### 6. `pipeline.py` - Orquestador RAG
**Clase `RAGPipeline`:**
- Inicialización lazy de componentes
- Configuración flexible vía .env o parámetros
- Métodos principales:
  - `index_documents()` - Indexa directorio completo
  - `query()` - Realiza consulta con retrieval
  - `rag_pipeline()` - Función simplificada
  - `add_new_documents()` - Actualización incremental

## 🔧 Flujo Completo del Sistema

### Indexación:
```
Documentos → Load → Chunks → Embeddings → Vector DB
                        ↓
                    Caché (disco)
```

### Consulta:
```
Pregunta → Embedding → Retrieve (top-k) → Contexto → LLM → Respuesta
                         ↓
                    ChromaDB
```

## 📊 Respuestas a Preguntas Específicas

### 1. Mejor estrategia de chunking para documentos largos
✅ **Chunking recursivo semántico** implementado:
- Prioriza límites naturales (párrafos, oraciones)
- Mantiene coherencia contextual
- Solapamiento del 10% evita pérdida en bordes

### 2. Manejo de documentos con tablas o listas
✅ **Estrategias implementadas:**
- Tablas en Markdown: se preserva estructura con `|`
- Listas: se mantienen dentro del mismo chunk
- PDFs con tablas: chunk más grande recomendado (700+ tokens)

### 3. Asegurar que LLM use correctamente el contexto
✅ **Técnicas aplicadas:**
- Delimitadores XML claros (`<contexto>`)
- Instrucciones explícitas en el prompt
- Inclusión de fuentes y scores de relevancia
- Templates específicos por familia de modelo
- Stop sequences apropiadas

### 4. Optimización de rendimiento en CPU
✅ **Recomendaciones implementadas:**
- Variable `N_THREADS` configurable
- Soporte para BLAS/OpenBLAS
- Chunks más pequeños reducen memoria
- Modelos Q4_K_M balancean velocidad/calidad

### 5. Actualizar vector DB con nuevos documentos
✅ **Métodos disponibles:**
- `add_new_documents()` - Adición incremental
- `delete_by_metadata()` - Eliminación selectiva
- Caché evita reprocesar contenido existente

## 🚀 Interfaces Disponibles

### CLI (cli.py)
```bash
python cli.py index ./docs           # Indexar
python cli.py query -q "pregunta"    # Consultar
python cli.py query --interactive    # REPL
python cli.py stats                  # Estadísticas
```

### API REST (api.py)
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```
Endpoints:
- `POST /index` - Indexar documentos
- `POST /query` - Realizar consulta
- `GET /stats` - Ver estadísticas
- `DELETE /vector-db/clear` - Limpiar DB

### Programático
```python
from src.pipeline import RAGPipeline
pipeline = RAGPipeline()
pipeline.index_documents("./docs")
result = pipeline.query("¿Qué es Python?")
```

## ⚙️ Configuración (.env)

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| MODEL_PATH | ./models/...gguf | Ruta al modelo LLM |
| EMBEDDING_MODEL | all-MiniLM-L6-v2 | Modelo de embeddings |
| CHUNK_SIZE | 500 | Tokens por chunk |
| CHUNK_OVERLAP | 50 | Solapamiento entre chunks |
| TOP_K | 4 | Chunks a recuperar |
| TEMPERATURE | 0.7 | Creatividad del LLM |
| MAX_TOKENS | 512 | Máximo tokens a generar |
| N_GPU_LAYERS | 0 | Capas en GPU (0=CPU) |
| N_THREADS | 4 | Hilos CPU |

## 📦 Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv && source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar modelo
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir ./models --local-dir-use-symlinks False

# 4. Configurar
cp config/.env.example config/.env

# 5. Probar
python example_usage.py
```

## 📈 Métricas Esperadas

| Operación | CPU (i7) | GPU (RTX 3060) |
|-----------|----------|----------------|
| Embedding (1 chunk) | ~50ms | ~10ms |
| Indexar 100 páginas | ~2 min | ~1 min |
| Retrieval | ~100ms | ~50ms |
| Generación (512 tokens) | ~30s | ~5s |

## 🎓 Características Destacables

1. **100% Local**: Sin APIs externas, privacidad total
2. **Modular**: Cada componente es independiente y reemplazable
3. **Persistente**: Vector DB y caché en disco
4. **Configurable**: Todos los parámetros ajustables
5. **Documentado**: Código con comentarios detallados
6. **Extensible**: Fácil agregar nuevos formatos o modelos

## 🔍 Archivos Clave para Extender

- `src/document_loader.py` - Agregar nuevo formato de archivo
- `src/llm.py` - Agregar template para nuevo modelo
- `src/chunker.py` - Modificar estrategia de división
- `config/settings.py` - Agregar nueva opción de configuración

## ✅ Verificación de Calidad

Todos los archivos han sido verificados:
- ✓ Sintaxis Python correcta
- ✓ Type hints donde corresponde
- ✓ Docstrings en todas las funciones
- ✓ Manejo de errores apropiado
- ✓ Comentarios explicativos

---

**Entregables completados:**
1. ✅ Estructura de carpetas del proyecto
2. ✅ Archivos de código Python completos y funcionales
3. ✅ Script de instalación (requirements.txt)
4. ✅ Ejemplo de uso con documento de prueba
5. ✅ Explicación paso a paso (README.md, QUICKSTART.md)
6. ✅ Respuestas a preguntas específicas (en README.md)
