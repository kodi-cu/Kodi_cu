# Guía Rápida de Inicio - Sistema RAG Local

## 📦 Instalación en 5 pasos

### Paso 1: Crear entorno virtual
```bash
cd /workspace/rag_system
python3 -m venv venv
source venv/bin/activate
```

### Paso 2: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Descargar modelo (opcional para pruebas)
```bash
# Si no tienes huggingface-cli, instálala primero:
pip install huggingface_hub

# Descargar Mistral-7B-Instruct Q4_K_M (~4GB)
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir ./models \
  --local-dir-use-symlinks False
```

**Alternativa ligera para CPU (Phi-3, ~2GB):**
```bash
huggingface-cli download TheBloke/Phi-3-mini-4k-instruct-GGUF \
  phi-3-mini-4k-instruct.Q4_K_M.gguf \
  --local-dir ./models \
  --local-dir-use-symlinks False
```

### Paso 4: Configurar
```bash
cp config/.env.example config/.env
```

Editar `config/.env`:
```env
MODEL_PATH=./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
N_GPU_LAYERS=0  # Cambiar a 35 si tienes GPU NVIDIA
N_THREADS=4     # Ajustar a núcleos de tu CPU
```

### Paso 5: Probar con documento de ejemplo
```bash
# Ya hay un documento de ejemplo en docs/python_intro.md
python example_usage.py
```

## 🚀 Comandos principales

### Indexar documentos
```bash
# Indexar todo el directorio docs/
python cli.py index ./docs

# Indexar solo PDFs y TXTs
python cli.py index ./docs --types pdf,txt

# Reindexar desde cero
python cli.py index ./docs --clear
```

### Hacer consultas
```bash
# Consulta única
python cli.py query -q "¿Qué es Python?"

# Modo interactivo (REPL)
python cli.py query --interactive

# Con parámetros personalizados
python cli.py query -q "Explica OOP" --temperature 0.5 --max-tokens 256
```

### Ver estadísticas
```bash
python cli.py stats
```

## 🔌 API REST

### Iniciar servidor
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints

#### Health check
```bash
curl http://localhost:8000/health
```

#### Indexar
```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"directory": "./docs", "clear_existing": false}'
```

#### Consultar
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es Python?", "temperature": 0.7}'
```

#### Estadísticas
```bash
curl http://localhost:8000/stats
```

## 💻 Uso programático

```python
from src.pipeline import RAGPipeline

# Inicializar
pipeline = RAGPipeline()

# Indexar
stats = pipeline.index_documents("./docs", clear_existing=True)

# Consultar
result = pipeline.query("¿Qué es machine learning?")
print(result["answer"])

# Ver fuentes
for source, score in zip(result["sources"], result["scores"]):
    print(f"  - {source}: {score:.2f}")
```

## ⚙️ Optimización por hardware

### Solo CPU (sin GPU)
```env
N_GPU_LAYERS=0
N_THREADS=8              # Igual a núcleos físicos
CHUNK_SIZE=400           # Chunks más pequeños
```

**Compilar llama-cpp-python optimizado:**
```bash
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
  pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Con GPU NVIDIA
```env
N_GPU_LAYERS=35          # Ajustar según VRAM (ej: 6GB=25, 12GB=40)
N_THREADS=4
```

**Verificar CUDA disponible:**
```bash
nvidia-smi
```

## 📊 Parámetros recomendados

| Escenario | CHUNK_SIZE | TOP_K | TEMPERATURE |
|-----------|------------|-------|-------------|
| Documentos técnicos | 600 | 5 | 0.5 |
| Documentos generales | 500 | 4 | 0.7 |
| Preguntas específicas | 400 | 3 | 0.3 |
| Resumen/creativo | 500 | 4 | 0.8 |

## 🔍 Troubleshooting común

### "Model not found"
```bash
# Verificar ruta del modelo
ls -la ./models/*.gguf

# Actualizar .env con ruta correcta
```

### "CUDA out of memory"
```env
# Reducir capas en GPU
N_GPU_LAYERS=20  # o menos
```

### Consultas muy lentas
```env
# Usar modelo más pequeño o reducir tokens
MAX_TOKENS=256
```

### Error al instalar llama-cpp-python
```bash
# Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install build-essential cmake

# Reintentar instalación
pip install llama-cpp-python --no-cache-dir
```

## 📈 Flujo de trabajo recomendado

1. **Preparación**: Colocar documentos en `./docs/`
2. **Indexación**: `python cli.py index ./docs --clear`
3. **Prueba**: `python cli.py query --interactive`
4. **Ajuste**: Modificar parámetros en `.env` según resultados
5. **Producción**: Iniciar API con `uvicorn api:app`

## 🎯 Ejemplo completo paso a paso

```bash
# 1. Entorno
cd /workspace/rag_system
python3 -m venv venv && source venv/bin/activate

# 2. Instalar
pip install -r requirements.txt

# 3. Configurar (usando Phi-3 que es más ligero)
huggingface-cli download TheBloke/Phi-3-mini-4k-instruct-GGUF \
  phi-3-mini-4k-instruct.Q4_K_M.gguf \
  --local-dir ./models --local-dir-use-symlinks False

echo "MODEL_PATH=./models/phi-3-mini-4k-instruct.Q4_K_M.gguf" > config/.env
echo "N_GPU_LAYERS=0" >> config/.env
echo "N_THREADS=4" >> config/.env

# 4. Indexar documento de ejemplo
python cli.py index ./docs

# 5. Consultar
python cli.py query -q "¿Qué es Python?"
```

## 📚 Recursos adicionales

- **Documentación completa**: Ver README.md
- **Código fuente**: Archivos en `src/` con comentarios detallados
- **Configuración avanzada**: Editar `config/settings.py`

---

**Soporte**: Para problemas específicos, revisar logs de error y verificar:
1. Python 3.10+ instalado
2. Espacio en disco suficiente (~10GB mínimo)
3. Modelo GGUF descargado correctamente
4. Dependencias instaladas sin errores
