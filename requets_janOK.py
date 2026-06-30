import requests

# URL de la API local de Jan
api_url = "http://localhost:1337/v1/chat/completions"

# Configurar los headers y el cuerpo de la solicitud
headers = {
    "Content-Type": "application/json",
}

# Mensaje inicial del sistema
messages = [
    {"role": "system", "content": "Eres un asistente útil."}
]

# Función para enviar mensajes al modelo
def enviar_mensaje(mensaje):
    messages.append({"role": "user", "content": mensaje})  # Agregar el mensaje del usuario
    data = {
        "model": "qwen2.5-coder-7b-instruct",  # Reemplaza con el nombre del modelo que estás usando en Jan
        "messages": messages
    }

    try:
        # Hacer la solicitud POST a la API
        response = requests.post(api_url, json=data, headers=headers)

        # Verificar la respuesta
        if response.status_code == 200:
            respuesta_modelo = response.json()["choices"][0]["message"]["content"]
            print("Asistente:", respuesta_modelo)
            messages.append({"role": "assistant", "content": respuesta_modelo})  # Agregar la respuesta del asistente
        else:
            print("Error en la solicitud:")
            print("Código de estado:", response.status_code)
            print("Mensaje de error:", response.text)

    except requests.exceptions.RequestException as e:
        print("Error de conexión:", e)

# Bucle principal para chatear
print("¡Bienvenido al chat con el modelo! Escribe 'salir' para terminar.")
while True:
    # Solicitar entrada del usuario
    user_input = input("Tú: ")

    # Salir del bucle si el usuario escribe "salir" o "exit"
    if user_input.lower() in ["salir", "exit"]:
        print("¡Hasta luego!")
        break

    # Enviar el mensaje al modelo
    enviar_mensaje(user_input)
