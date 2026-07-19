# Sistema RAG Local con LLM

Sistema completo de **Retrieval-Augmented Generation (RAG)** que funciona 100% local, sin dependencias de APIs externas. Usa modelos de lenguaje grandes (LLMs) cuantizados con llama.cpp y embeddings locales con sentence-transformers.

## 📋 Características

- **100% Local**: Sin llamadas a APIs externas, todos los modelos se ejecutan en tu máquina
- **Soporte múltiple de formatos**: PDF, TXT, Markdown
- **Embeddings cacheados**: Evita reprocesar documentos ya indexados
- **Vector DB persistente**: ChromaDB con persistencia en disco
- **LLM flexible**: Soporta Mistral-7B, Llama-3, Phi-3 y otros modelos GGUF
- **CLI y API**: Interfaz de línea de comandos y API REST con FastAPI
- **Optimizable**: Configuración de GPU layers, threads CPU, y parámetros de generación

## 🏗️ Estructura del Proyecto

```
rag_system/
├── config/
│   ├── .env.example          # Plantilla de configuración
│   └── settings.py           # Módulo de configuración
├── src/
│   ├── document_loader.py    # Carga de PDF, TXT, MD
│   ├── chunker.py            # División inteligente de texto
│   ├── embeddings.py         # Generación de embeddings
│   ├── vector_store.py       # ChromaDB para vectores
│   ├── llm.py                # LLM local con llama.cpp
│   └── pipeline.py           # Pipeline RAG completo
├── docs/                      # Directorio para documentos
├── models/                    # Directorio para modelos GGUF
├── vector_store/              # Persistencia de ChromaDB
├── cache/                     # Caché de embeddings
├── cli.py                     # Interfaz de línea de comandos
├── api.py                     # API FastAPI
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

## 🚀 Instalación

### 1. Crear entorno virtual

```bash
cd rag_system
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Descargar modelo LLM

Descarga un modelo en formato GGUF desde Hugging Face:

**Opción recomendada (Mistral-7B-Instruct):**
```bash
# Usando huggingface-cli
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir ./models \
  --local-dir-use-symlinks False
```

**Alternativas:**
- [Llama-3-8B-Instruct-GGUF](https://huggingface.co/TheBloke/Llama-3-8B-Instruct-GGUF)
- [Phi-3-mini-4k-instruct-GGUF](https://huggingface.co/TheBloke/Phi-3-mini-4k-instruct-GGUF)

### 4. Configurar el sistema

```bash
cp config/.env.example config/.env
```

Edita `config/.env` y ajusta:
- `MODEL_PATH`: Ruta a tu modelo GGUF
- `N_GPU_LAYERS`: Número de capas en GPU (0 = solo CPU)
- `CHUNK_SIZE`: Tamaño de chunks (default: 500 tokens)
- `TOP_K`: Chunks a recuperar (default: 4)

## 📖 Uso

### Modo CLI

#### Indexar documentos

```bash
# Indexar todos los documentos en ./docs
python cli.py index ./docs

# Indexar solo archivos específicos
python cli.py index ./docs --types pdf,txt

# Limpiar DB existente antes de indexar
python cli.py index ./docs --clear
```

#### Hacer consultas

```bash
# Consulta única
python cli.py query -q "¿Qué es Python?"

# Modo interactivo
python cli.py query --interactive

# Ajustar temperatura
python cli.py query -q "Explica la relatividad" --temperature 0.5
```

#### Ver estadísticas

```bash
python cli.py stats
```

### Modo API

Iniciar servidor:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints disponibles:

- `GET /` - Información de la API
- `GET /health` - Estado del sistema
- `POST /index` - Indexar documentos
- `POST /query` - Realizar consulta
- `GET /stats` - Estadísticas

Ejemplo con curl:

```bash
# Consultar
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es machine learning?", "temperature": 0.7}'
```

### Uso programático

```python
from src.pipeline import RAGPipeline

# Inicializar
pipeline = RAGPipeline()

# Indexar documentos
stats = pipeline.index_documents("./docs", clear_existing=True)
print(f"Indexados {stats['chunks_created']} chunks")

# Hacer consulta
result = pipeline.query("¿Qué es Python?")
print(result["answer"])
print(f"Fuentes: {result['sources']}")
```

## ⚙️ Configuración

### Parámetros principales (.env)

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `MODEL_PATH` | Ruta al modelo GGUF | `./models/mistral-7b...gguf` |
| `EMBEDDING_MODEL` | Modelo sentence-transformers | `all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | Tokens por chunk | `500` |
| `CHUNK_OVERLAP` | Solapamiento entre chunks | `50` |
| `TOP_K` | Chunks a recuperar | `4` |
| `TEMPERATURE` | Creatividad del LLM | `0.7` |
| `N_GPU_LAYERS` | Capas en GPU | `0` |
| `N_THREADS` | Hilos CPU | `4` |

### Optimización de hardware

**Solo CPU:**
```env
N_GPU_LAYERS=0
N_THREADS=8  # Ajustar a núcleos disponibles
```

**Con GPU (NVIDIA):**
```env
N_GPU_LAYERS=35  # Ajustar según VRAM disponible
N_THREADS=4
```

## 📚 Respuestas a preguntas específicas

### 1. ¿Cuál es la mejor estrategia de chunking para documentos largos?

El sistema usa **chunking recursivo semántico**:

1. Intenta dividir por párrafos (doble salto de línea)
2. Si los párrafos son muy grandes, divide por oraciones
3. Como último recurso, divide por palabras

**Recomendaciones:**
- `CHUNK_SIZE=500`: Balance entre contexto y precisión
- `CHUNK_OVERLAP=50`: Mantiene continuidad entre chunks
- Para documentos técnicos: aumentar a 600-700 tokens
- Para documentos generales: 400-500 tokens es suficiente

### 2. ¿Cómo manejar documentos con tablas o listas?

**Tablas:**
- En PDFs: Se extraen como texto plano con separadores
- En Markdown: Se preserva la estructura con `|`
- Recomendación: Para tablas complejas, usar chunk más grande (700+ tokens)

**Listas:**
- Se mantienen dentro del mismo chunk cuando es posible
- El chunking por párrafos preserva la estructura de listas
- Las listas numeradas mantienen su coherencia semántica

### 3. ¿Cómo asegurar que el LLM use correctamente el contexto recuperado?

El sistema usa **prompt engineering específico**:

```
[INST] Eres un asistente útil que responde basándose en el contexto.

<contexto>
{chunks recuperados con fuentes y scores}
</contexto>

Usa ÚNICAMENTE la información del contexto. Si no puedes responder, dilo claramente.

Pregunta: {question}
Respuesta: [/INST]
```

**Técnicas aplicadas:**
- Delimitadores claros (`<contexto>`, `[/INST]`)
- Instrucción explícita de usar solo el contexto
- Inclusión de fuentes y scores de relevancia
- Templates específicos por tipo de modelo (Mistral, Llama-3, Phi-3)

### 4. ¿Cómo optimizar el rendimiento en CPU (sin GPU)?

**Configuración recomendada:**

```env
N_THREADS=8              # Igual a núcleos físicos
N_GPU_LAYERS=0
CHUNK_SIZE=400           # Chunks más pequeños = menos memoria
```

**Otras optimizaciones:**
1. Usar modelo Q4_K_M (balance calidad/velocidad)
2. Para máxima velocidad: Q3_K_M o Q2_K
3. Reducir `CONTEXT_WINDOW` si no se necesita contexto largo
4. Usar `llama-cpp-python` compilado con BLAS/OpenBLAS

```bash
# Compilar con optimizaciones
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
  pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 5. ¿Cómo actualizar la vector DB cuando se agregan nuevos documentos?

**Opción 1: Adición incremental (recomendada)**

```python
pipeline = RAGPipeline()
pipeline.add_new_documents("./nuevos_docs")
```

**Opción 2: CLI**
```bash
python cli.py index ./nuevos_docs  # Sin --clear
```

**Opción 3: Eliminar documentos específicos**

```python
# Eliminar por fuente
db.delete_by_metadata(key="source", value="documento_viejo.pdf")

# Luego agregar versión actualizada
pipeline.add_new_documents("./docs_actualizados")
```

El **caché de embeddings** evita reprocesar contenido ya indexado.

## 🔧 Troubleshooting

### Error: "Model not found"
Verifica que `MODEL_PATH` en `.env` apunte al archivo correcto.

### Error: "CUDA out of memory"
Reduce `N_GPU_LAYERS` o usa un modelo más pequeño (Q3, Q2).

### Consultas lentas en CPU
- Verificar que `N_THREADS` esté configurado correctamente
- Considerar usar modelo más pequeño (Phi-3, TinyLlama)
- Reducir `MAX_TOKENS` en consultas

### Embeddings tardan mucho la primera vez
Es normal. Los embeddings se cachean y las siguientes veces será instantáneo.

## 📊 Métricas de rendimiento

| Tarea | CPU (i7) | GPU (RTX 3060) |
|-------|----------|----------------|
| Embedding (1 chunk) | ~50ms | ~10ms |
| Indexar 100 páginas | ~2 min | ~1 min |
| Consulta (retrieval) | ~100ms | ~50ms |
| Generación (512 tokens) | ~30s | ~5s |

## 📝 Licencia

MIT License

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor abrir un issue o PR.
