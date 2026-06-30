# Chat con API de Jan

Script en Python para interactuar mediante chat con modelos de lenguaje locales usando la API de Jan.

## Descripción

Este script permite mantener una conversación continua con un modelo de IA local (por defecto `qwen2.5-coder-7b-instruct`) a través de la API de Jan running en `localhost:1337`.

## Requisitos

- Python 3.x
- Librería `requests`
- Jan App corriendo localmente con un modelo cargado

## Instalación

1. Instalar la dependencia requerida:

```bash
pip install requests
```

2. Asegurarse de tener Jan instalado y ejecutándose localmente en el puerto 1337.

3. Cargar un modelo en Jan (el script usa por defecto `qwen2.5-coder-7b-instruct`).

## Uso

Ejecutar el script:

```bash
python requets_janOK.py
```

Una vez iniciado, podrás:
- Escribir mensajes para chatear con el modelo
- El historial de conversación se mantiene durante la sesión
- Escribir `salir` o `exit` para terminar la conversación

## Configuración

Puedes modificar los siguientes parámetros en el script:

- `api_url`: URL de la API de Jan (por defecto: `http://localhost:1337/v1/chat/completions`)
- `model`: Nombre del modelo a usar (por defecto: `qwen2.5-coder-7b-instruct`)
- `system message`: Mensaje inicial del sistema para configurar el comportamiento del asistente

## Ejemplo

```
¡Bienvenido al chat con el modelo! Escribe 'salir' para terminar.
Tú: Hola, ¿cómo estás?
Asistente: ¡Hola! Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?
Tú: salir
¡Hasta luego!
```

## Notas

- Asegúrate de que Jan esté ejecutándose antes de usar este script
- La API debe estar habilitada en la configuración de Jan
- El puerto por defecto es 1337
