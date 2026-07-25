# PDF Agent - Agente Profesional de IA para Gestión de Documentos PDF

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Descripción

**PDF Agent** es un sistema profesional de agente de IA especializado en el análisis y gestión de documentos PDF. Utiliza modelos locales a través de llama.cpp para proporcionar capacidades avanzadas de procesamiento de documentos con una interfaz web moderna e intuitiva.

### ✨ Características Principales

- **🤖 Agente de IA Local**: Conectado a modelos locales mediante llama.cpp
- **📄 Análisis Inteligente de PDFs**: Extracción de texto, tablas, metadatos e imágenes
- **🔍 Búsqueda Semántica**: Búsqueda de contenido en múltiples documentos
- **📊 Clasificación Automática**: Organización de PDFs por tema, fecha o tamaño
- **✅ Sistema TODO Integrado**: Razonamiento y seguimiento de tareas del agente
- **🖥️ Interfaz Web Moderna**: Dashboard interactivo para visualización de resultados
- **🧠 Razonamiento Visible**: Muestra el proceso de pensamiento del agente
- **🛠️ Herramientas Extensibles**: Arquitectura modular para añadir nuevas capacidades

## 🚀 Instalación

### Requisitos Previos

1. **Python 3.9+** instalado
2. **llama.cpp** corriendo con un modelo cargado (por defecto en `http://localhost:8081`)

### Pasos de Instalación

```bash
# Clonar o navegar al directorio del proyecto
cd pdf_agent

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python -m src.main
```

## 📁 Estructura del Proyecto

```
pdf_agent/
├── config/
│   └── settings.py          # Configuración del sistema
├── src/
│   ├── core/
│   │   ├── agent.py         # Lógica principal del agente
│   │   ├── reasoning.py     # Sistema de razonamiento
│   │   └── todo_manager.py  # Gestor de lista TODO
│   ├── tools/
│   │   ├── pdf_tools.py     # Herramientas de análisis PDF
│   │   ├── file_tools.py    # Herramientas de archivo
│   │   └── search_tools.py  # Herramientas de búsqueda
│   ├── ui/
│   │   ├── dashboard.py     # Interfaz web principal
│   │   └── components.py    # Componentes UI reutilizables
│   ├── utils/
│   │   ├── logger.py        # Sistema de logging
│   │   └── helpers.py       # Funciones utilitarias
│   └── main.py              # Punto de entrada principal
├── tests/                   # Tests unitarios
├── docs/                    # Documentación adicional
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## 🛠️ Herramientas Disponibles

### Herramientas Básicas
- `leer_archivo`: Lee archivos de texto
- `listar_archivos`: Lista contenido de directorios
- `ejecutar_comando_seguro`: Ejecuta comandos seguros en terminal

### Herramientas PDF
- `analizar_pdf`: Analiza PDFs individuales (texto, tablas, metadatos)
- `clasificar_pdfs`: Clasifica múltiples PDFs por criterio
- `buscar_en_pdfs`: Busca palabras clave en colección de PDFs
- `resumen_ejecutivo_pdfs`: Genera resúmenes ejecutivos

### Herramientas TODO
- `todo_write`: Crea/actualiza lista completa de tareas
- `todo_add`: Añade nueva tarea
- `todo_update`: Actualiza estado de tarea
- `todo_list`: Muestra lista de tareas filtrada

## 💻 Uso

### Desde Línea de Comandos

```bash
python -m src.main
```

### Desde Interfaz Web

```bash
python -m src.ui.dashboard
```

Luego abre tu navegador en `http://localhost:8501`

### Ejemplos de Comandos

```
"Analiza el documento 'contrato.pdf' y extrae las cláusulas importantes"
"Busca todos los PDFs que mencionen 'inteligencia artificial'"
"Clasifica los documentos del directorio /docs por fecha"
"Genera un resumen ejecutivo de todos los PDFs en /informes"
"Muestra mi lista de tareas pendientes"
```

## 🔧 Configuración

Edita `config/settings.py` para personalizar:

```python
# Configuración del servidor llama.cpp
LLAMA_SERVER_URL = "http://localhost:8081/v1"
MODEL_NAME = "InternScience/Agents-A1-4B-Q4_K_M-GGUF"

# Configuración de la interfaz
UI_PORT = 8501
UI_THEME = "light"

# Límites de procesamiento
MAX_PDF_SIZE_MB = 50
MAX_TOKENS = 4096
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/

# Con cobertura
pytest --cov=src tests/
```

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📞 Soporte

Para issues o preguntas, por favor abre un issue en el repositorio.

---

**Desarrollado con ❤️ usando Python, Streamlit y llama.cpp**
