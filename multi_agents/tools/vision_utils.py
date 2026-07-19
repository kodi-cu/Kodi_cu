"""Utilidades para análisis de imágenes con modelos de visión"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import base64


def encode_image_to_base64(image_path: Path) -> str:
    """
    Codifica una imagen a base64 para enviar al modelo de visión.
    
    Args:
        image_path: Ruta a la imagen
    
    Returns:
        String en base64 de la imagen
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error codificando imagen: {str(e)}")


def create_vision_message(
    image_path: Union[Path, str],
    prompt: str = "Describe esta imagen en detalle."
) -> Dict[str, Any]:
    """
    Crea un mensaje para el modelo de visión.
    
    Args:
        image_path: Ruta a la imagen
        prompt: Prompt para el modelo
    
    Returns:
        Diccionario con el formato de mensaje para la API
    """
    image_path = Path(image_path)
    base64_image = encode_image_to_base64(image_path)
    
    # Detectar tipo de MIME
    mime_type = f"image/{image_path.suffix.lower().replace('.', '')}"
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
    elif mime_type == "image/odg":
        mime_type = "image/svg+xml"
    
    return {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            }
        ]
    }


def analyze_image_with_llm(
    client,
    image_path: Union[Path, str],
    prompt: str = "Describe esta imagen en detalle.",
    model_name: str = "local-vision-model",
    max_tokens: int = 1024
) -> str:
    """
    Analiza una imagen usando un modelo de visión local.
    
    Args:
        client: Cliente OpenAI compatible
        image_path: Ruta a la imagen
        prompt: Prompt para el análisis
        model_name: Nombre del modelo de visión
        max_tokens: Máximo de tokens en la respuesta
    
    Returns:
        Descripción/analisi de la imagen
    """
    try:
        message = create_vision_message(image_path, prompt)
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[message],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analizando imagen: {str(e)}"


def extract_text_from_image(
    client,
    image_path: Union[Path, str],
    model_name: str = "local-vision-model"
) -> str:
    """
    Extrae texto de una imagen (OCR con modelo de visión).
    
    Args:
        client: Cliente OpenAI compatible
        image_path: Ruta a la imagen
        model_name: Nombre del modelo de visión
    
    Returns:
        Texto extraído de la imagen
    """
    prompt = "Extrae todo el texto visible en esta imagen. Si no hay texto, responde 'No hay texto visible'."
    return analyze_image_with_llm(client, image_path, prompt, model_name)


def describe_chart_or_graph(
    client,
    image_path: Union[Path, str],
    model_name: str = "local-vision-model"
) -> str:
    """
    Describe gráficos o diagramas en una imagen.
    
    Args:
        client: Cliente OpenAI compatible
        image_path: Ruta a la imagen
        model_name: Nombre del modelo de visión
    
    Returns:
        Descripción del gráfico
    """
    prompt = """Analiza este gráfico o diagrama y proporciona:
1. Tipo de gráfico (barras, líneas, circular, etc.)
2. Título si existe
3. Ejes y sus etiquetas
4. Datos principales o tendencias
5. Conclusiones clave"""
    
    return analyze_image_with_llm(client, image_path, prompt, model_name)


def is_image_file(file_path: Path) -> bool:
    """Verifica si un archivo es una imagen soportada"""
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff']
    return file_path.suffix.lower() in image_extensions
