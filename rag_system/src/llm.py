"""
Módulo para generación de respuestas con LLM local.
Usa llama-cpp-python con modelos GGUF cuantizados.

Soporta:
- Modelos Mistral-7B-Instruct y Llama-3-8B-Instruct
- Offload parcial a GPU si está disponible
- Templates de prompt específicos por modelo
- Control de temperatura y otros parámetros
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Generator
import sys

sys.path.insert(0, str(Path(__file__).parent))

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("Advertencia: llama-cpp-python no está instalado.")


class LocalLLM:
    """
    Wrapper para modelos LLM locales usando llama.cpp.
    
    Soporta modelos en formato GGUF cuantizados:
    - Mistral-7B-Instruct-v0.2.Q4_K_M.gguf (recomendado)
    - Llama-3-8B-Instruct.Q4_K_M.gguf
    - Phi-3-mini-4k-instruct.Q4_K_M.gguf (más ligero)
    """
    
    # Templates de prompt por tipo de modelo
    PROMPT_TEMPLATES = {
        "mistral": """[INST] Eres un asistente útil que responde preguntas basándose en el contexto proporcionado.

<contexto>
{context}
</contexto>

Usa ÚNICAMENTE la información del contexto anterior para responder. Si la respuesta no se puede encontrar en el contexto, di "No tengo suficiente información en el contexto proporcionado para responder esta pregunta."

Pregunta: {question}

Respuesta: [/INST]""",
        
        "llama3": """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Eres un asistente útil que responde preguntas basándose en el contexto proporcionado. Usa ÚNICAMENTE la información del contexto. Si no puedes responder con el contexto dado, indícalo claramente.<|eot_id|><|start_header_id|>user<|end_header_id|>

Contexto:
{context}

Pregunta: {question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

""",
        
        "phi3": """<|system|>
Eres un asistente útil. Responde basándote únicamente en el contexto proporcionado.<|end|>
<|user|>
Contexto: {context}

Pregunta: {question}<|end|>
<|assistant|>
""",
        
        # Template genérico
        "default": """Instrucción: Responde la siguiente pregunta usando el contexto proporcionado.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""
    }
    
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = 0,
        verbose: bool = False
    ):
        """
        Inicializa el modelo LLM.
        
        Args:
            model_path: Ruta al archivo .gguf del modelo
            n_ctx: Tamaño de ventana de contexto
            n_threads: Número de hilos CPU (None para auto)
            n_gpu_layers: Capas a offload a GPU (0 = solo CPU)
            verbose: Mostrar logs detallados
        """
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError(
                "llama-cpp-python no está instalado. "
                "Ejecuta: pip install llama-cpp-python"
            )
        
        self.model_path = model_path
        
        # Detectar tipo de modelo para template
        model_name = Path(model_path).name.lower()
        if "mistral" in model_name:
            self.template_type = "mistral"
        elif "llama-3" in model_name or "llama3" in model_name:
            self.template_type = "llama3"
        elif "phi" in model_name:
            self.template_type = "phi3"
        else:
            self.template_type = "default"
        
        print(f"Cargando modelo: {model_path}")
        print(f"Tipo de template: {self.template_type}")
        
        # Configurar carga del modelo
        kwargs = {
            "model_path": model_path,
            "n_ctx": n_ctx,
            "verbose": verbose,
        }
        
        if n_threads is not None:
            kwargs["n_threads"] = n_threads
        
        if n_gpu_layers > 0:
            kwargs["n_gpu_layers"] = n_gpu_layers
            print(f"Offload a GPU: {n_gpu_layers} capas")
        else:
            print("Ejecutando en CPU")
        
        # Cargar modelo
        self.model = Llama(**kwargs)
        print("Modelo cargado exitosamente")
    
    def format_prompt(self, context: str, question: str) -> str:
        """
        Formatea el prompt con contexto y pregunta.
        
        El prompt engineering es crucial para que el LLM:
        1. Use correctamente el contexto recuperado
        2. No invente información (alucinaciones)
        3. Reconozca cuando no tiene suficiente información
        
        Args:
            context: Texto del contexto recuperado
            question: Pregunta del usuario
            
        Returns:
            Prompt formateado
        """
        template = self.PROMPT_TEMPLATES.get(
            self.template_type, 
            self.PROMPT_TEMPLATES["default"]
        )
        
        return template.format(context=context, question=question)
    
    def generate_response(
        self,
        context: str,
        question: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Genera una respuesta basada en contexto y pregunta.
        
        Parámetros clave para calidad:
        - temperature: Controla creatividad (0.7 = balance)
        - top_p: Muestreo nuclear (0.9 = diverso pero coherente)
        - repeat_penalty: Reduce repeticiones
        
        Args:
            context: Contexto recuperado
            question: Pregunta del usuario
            temperature: Temperatura de muestreo
            max_tokens: Máximo de tokens a generar
            top_p: Probabilidad acumulada para muestreo
            repeat_penalty: Penalización por repetición
            stop_sequences: Secuencias para detener generación
            
        Returns:
            Respuesta generada
        """
        prompt = self.format_prompt(context, question)
        
        # Configurar secuencias de parada por template
        if stop_sequences is None:
            stop_sequences = []
            if self.template_type == "mistral":
                stop_sequences = ["[/INST]", "[INST]", "</s>"]
            elif self.template_type == "llama3":
                stop_sequences = ["<|eot_id|>", "<|end_of_text|>"]
            elif self.template_type == "phi3":
                stop_sequences = ["<|end|>", "<|assistant|>"]
        
        response = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
            stop=stop_sequences,
            echo=False
        )
        
        return response["choices"][0]["text"].strip()
    
    def generate_streaming(
        self,
        context: str,
        question: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Genera respuesta en modo streaming (token por token).
        
        Útil para interfaces interactivas donde se quiere mostrar
        progreso de generación.
        
        Args:
            context: Contexto recuperado
            question: Pregunta del usuario
            temperature: Temperatura de muestreo
            max_tokens: Máximo de tokens
            
        Yields:
            Tokens generados uno por uno
        """
        prompt = self.format_prompt(context, question)
        
        stop_sequences = kwargs.get('stop_sequences', None)
        if stop_sequences is None:
            stop_sequences = []
            if self.template_type == "mistral":
                stop_sequences = ["[/INST]", "[INST]"]
            elif self.template_type == "llama3":
                stop_sequences = ["<|eot_id|>"]
        
        for token in self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences,
            stream=True
        ):
            yield token["choices"][0]["text"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información del modelo."""
        return {
            "model_path": self.model_path,
            "template_type": self.template_type,
            "context_window": self.model.n_ctx(),
        }


def generate_response(
    llm: LocalLLM,
    context: str,
    question: str,
    temperature: float = 0.7,
    max_tokens: int = 512
) -> str:
    """
    Función principal para generar respuesta.
    
    Args:
        llm: Instancia de LocalLLM
        context: Contexto recuperado
        question: Pregunta del usuario
        temperature: Temperatura de muestreo
        max_tokens: Máximo de tokens a generar
        
    Returns:
        Respuesta generada
    """
    return llm.generate_response(
        context=context,
        question=question,
        temperature=temperature,
        max_tokens=max_tokens
    )


def create_context_string(
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    scores: List[float]
) -> str:
    """
    Crea string de contexto formateado para el prompt.
    
    Incluye:
    - Cada chunk numerado
    - Fuente del chunk (archivo, página)
    - Score de relevancia
    
    Esto ayuda al LLM a entender la procedencia y relevancia
    de cada fragmento.
    
    Args:
        documents: Lista de chunks recuperados
        metadatas: Metadatos de cada chunk
        scores: Scores de similitud
        
    Returns:
        String de contexto formateado
    """
    context_parts = []
    
    for i, (doc, meta, score) in enumerate(zip(documents, metadatas, scores), 1):
        source = meta.get('source', 'Desconocido')
        page = meta.get('page', '')
        page_info = f" (página {page})" if page else ""
        
        context_part = f"""[Fragmento {i}] - Fuente: {source}{page_info} - Relevancia: {score:.2f}
{doc}
"""
        context_parts.append(context_part)
    
    return "\n".join(context_parts)
