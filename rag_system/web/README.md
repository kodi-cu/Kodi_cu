# RAG System - Guía de la Interfaz Web

## 🌐 Descripción

La interfaz web permite interactuar con el sistema RAG directamente desde el navegador, proporcionando:

- **Panel de estadísticas**: Visualiza el estado del sistema y documentos indexados
- **Indexación de documentos**: Carga documentos desde tu sistema de archivos
- **Consultas interactivas**: Realiza preguntas y obtén respuestas con fuentes
- **Gestión de base de datos**: Limpia la base de datos vectorial cuando sea necesario

## 📁 Estructura de Archivos

```
web/
├── app.py                 # Servidor web FastAPI
├── templates/
│   └── index.html        # Página principal HTML
└── static/
    ├── css/
    │   └── style.css     # Estilos de la interfaz
    └── js/
        └── app.js        # Lógica JavaScript del frontend
```

## 🚀 Cómo Iniciar el Servidor Web

### Opción 1: Desde el directorio web

```bash
cd /workspace/rag_system/web
python app.py
```

### Opción 2: Usando uvicorn directamente

```bash
cd /workspace/rag_system/web
uvicorn app:web_app --host 0.0.0.0 --port 8080
```

### Opción 3: En segundo plano

```bash
cd /workspace/rag_system/web
nohup python app.py > web_server.log 2>&1 &
```

## 🔗 Accesos

Una vez iniciado el servidor:

- **Interfaz Web**: http://localhost:8080
- **Documentación API**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

## 📋 Requisitos Adicionales

El servidor web requiere las siguientes dependencias adicionales (además de las ya instaladas):

```bash
pip install jinja2>=3.1.0
```

## 💡 Uso de la Interfaz

### 1. Indexar Documentos

1. Ingresa la ruta al directorio con tus documentos
2. (Opcional) Especifica tipos de archivo: `pdf, txt, md`
3. (Opcional) Marca "Limpiar base de datos existente" si quieres empezar de cero
4. Haz clic en "Indexar Documentos"

### 2. Realizar Consultas

1. Escribe tu pregunta en el área de texto
2. Ajusta la temperatura (0 = más preciso, 1 = más creativo)
3. Define el máximo de tokens para la respuesta
4. Marca "Incluir fuentes" si quieres ver el contexto utilizado
5. Haz clic en "Consultar"

### 3. Ver Estadísticas

- Haz clic en "Actualizar" para refrescar las estadísticas del sistema
- Verás: número de documentos, modelo cargado, embeddings y chunk size

### 4. Limpiar Base de Datos

- Haz clic en "Limpiar Base de Datos" para borrar todos los documentos indexados
- ⚠️ Esta acción no se puede deshacer

## 🎨 Características de la Interfaz

- **Diseño responsivo**: Funciona en desktop y móviles
- **Indicadores de carga**: Spinners durante operaciones largas
- **Mensajes de estado**: Notificaciones visuales de éxito/error
- **Temperatura ajustable**: Slider interactivo para controlar la creatividad del LLM
- **Fuentes con scores**: Visualización de documentos fuente con sus puntuaciones de relevancia

## 🔧 Configuración Avanzada

### Cambiar el Puerto

Edita `app.py` y modifica la línea:
```python
uvicorn.run(web_app, host="0.0.0.0", port=8080)
```

### Personalizar Estilos

Edita `static/css/style.css` para cambiar:
- Colores (variables CSS en `:root`)
- Fuentes
- Espaciado y layout

### Modificar Comportamiento

Edita `static/js/app.js` para:
- Cambiar la URL base de la API
- Agregar validaciones personalizadas
- Modificar el formato de visualización de respuestas

## 🐛 Solución de Problemas

### Error de CORS

Si hay problemas de CORS, verifica que el middleware esté configurado correctamente en `api.py`.

### No se cargan las estadísticas

Verifica que:
1. El servidor API esté funcionando
2. Los permisos de lectura del directorio sean correctos
3. La ruta a los documentos exista

### Error al indexar

Asegúrate de que:
1. El directorio especificado existe
2. Hay documentos válidos (PDF, TXT, MD) en el directorio
3. El sistema tiene permisos de lectura

## 📝 Notas

- La interfaz web se conecta a la API localmente
- Todas las operaciones se ejecutan en tu máquina (no hay envío de datos a servidores externos)
- El modelo LLM y los embeddings se ejecutan localmente usando llama.cpp y sentence-transformers

## 🔄 Actualizaciones Futuras

Posibles mejoras:
- Historial de consultas
- Exportar respuestas a PDF/TXT
- Subida de archivos directa desde el navegador
- Autenticación de usuarios
- Modo oscuro/claro

---

**RAG System v1.0.0** | Powered by FastAPI & Local LLM
