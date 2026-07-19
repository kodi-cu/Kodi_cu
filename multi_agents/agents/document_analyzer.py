"""Agente DocumentAnalyzer - Análisis profundo de documentos con LLM"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union


class DocumentAnalyzerAgent:
    """
    Agente especializado en análisis profundo de documentos usando LLM.
    Realiza resúmenes, extracción de entidades, preguntas y respuestas, etc.
    """
    
    def __init__(self, llm_client, model_name: str = "local-model", vision_client=None, vision_model: str = "local-vision-model"):
        """
        Inicializa el analizador.
        
        Args:
            llm_client: Cliente LLM para análisis
            model_name: Nombre del modelo base
            vision_client: Cliente para modelos de visión (opcional)
            vision_model: Nombre del modelo de visión
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.vision_client = vision_client
        self.vision_model = vision_model
    
    def summarize(
        self,
        content: str,
        max_length: str = "medium"  # short, medium, long
    ) -> Dict[str, Any]:
        """
        Genera un resumen del documento.
        
        Args:
            content: Contenido del documento
            max_length: Longitud del resumen (short, medium, long)
        
        Returns:
            Diccionario con resumen y metadatos
        """
        length_map = {
            'short': '2-3 frases',
            'medium': '1 párrafo (5-7 frases)',
            'long': '3-4 párrafos detallados'
        }
        
        prompt = f"""Resume el siguiente texto en {length_map.get(max_length, '1 párrafo')}.
Incluye los puntos clave más importantes.

Texto:
{content[:8000]}  # Limitar para no exceder tokens

Resumen:"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.5
            )
            
            return {
                'summary': response.choices[0].message.content,
                'original_length': len(content),
                'summary_length': len(response.choices[0].message.content),
                'compression_ratio': len(content) / max(len(response.choices[0].message.content), 1),
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def extract_entities(self, content: str) -> Dict[str, Any]:
        """
        Extrae entidades nombradas del documento.
        
        Args:
            content: Contenido del documento
        
        Returns:
            Diccionario con entidades extraídas
        """
        prompt = f"""Extrae las siguientes entidades del texto:
- Personas
- Organizaciones/Empresas
- Fechas
- Lugares
- Cantidades monetarias
- Términos técnicos importantes

Texto:
{content[:8000]}

Responde ÚNICAMENTE con JSON en este formato:
{{
    "personas": [],
    "organizaciones": [],
    "fechas": [],
    "lugares": [],
    "cantidades": [],
    "terminos_tecnicos": []
}}"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            import json
            entities = json.loads(response.choices[0].message.content.strip())
            
            return {
                'entities': entities,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def answer_question(self, content: str, question: str) -> Dict[str, Any]:
        """
        Responde una pregunta específica sobre el documento.
        
        Args:
            content: Contenido del documento
            question: Pregunta a responder
        
        Returns:
            Diccionario con respuesta y contexto
        """
        prompt = f"""Basándote en el siguiente texto, responde la pregunta.
Si la respuesta no está en el texto, indícalo claramente.

Texto:
{content[:10000]}

Pregunta: {question}

Respuesta:"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.5
            )
            
            return {
                'question': question,
                'answer': response.choices[0].message.content,
                'success': True
            }
        except Exception as e:
            return {
                'question': question,
                'error': str(e),
                'success': False
            }
    
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """
        Analiza el sentimiento del documento.
        
        Args:
            content: Contenido del documento
        
        Returns:
            Diccionario con análisis de sentimiento
        """
        prompt = f"""Analiza el sentimiento de este texto.
Clasifícalo como: positivo, negativo, neutral, o mixto.
Proporciona una puntuación del 0 al 1 donde 0 es muy negativo y 1 es muy positivo.
Explica brevemente el razonamiento.

Texto:
{content[:6000]}

Formato de respuesta JSON:
{{
    "sentiment": "positivo/negativo/neutral/mixto",
    "score": 0.XX,
    "reasoning": "explicación breve"
}}"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            
            return {
                'sentiment': result.get('sentiment', 'unknown'),
                'score': float(result.get('score', 0.5)),
                'reasoning': result.get('reasoning', ''),
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def extract_key_points(self, content: str, num_points: int = 5) -> Dict[str, Any]:
        """
        Extrae los puntos clave del documento.
        
        Args:
            content: Contenido del documento
            num_points: Número de puntos clave a extraer
        
        Returns:
            Lista de puntos clave
        """
        prompt = f"""Extrae los {num_points} puntos clave más importantes de este texto.
Presenta cada punto como una frase concisa.

Texto:
{content[:8000]}

Puntos clave (formato lista numerada):"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.5
            )
            
            points_text = response.choices[0].message.content.strip()
            points = [line.strip() for line in points_text.split('\n') if line.strip()]
            
            return {
                'key_points': points[:num_points],
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def compare_documents(
        self,
        content1: str,
        content2: str,
        comparison_type: str = "similarities_differences"
    ) -> Dict[str, Any]:
        """
        Compara dos documentos.
        
        Args:
            content1: Contenido del primer documento
            content2: Contenido del segundo documento
            comparison_type: Tipo de comparación (similarities_differences, contradictions, evolution)
        
        Returns:
            Análisis comparativo
        """
        comparison_prompts = {
            'similarities_differences': 'Identifica similitudes y diferencias clave entre estos dos documentos.',
            'contradictions': 'Identifica cualquier contradicción o inconsistencia entre estos documentos.',
            'evolution': 'Analiza cómo ha evolucionado la información del primer al segundo documento.'
        }
        
        prompt = f"""{comparison_prompts.get(comparison_type, 'Compara estos documentos.')}

Documento 1:
{content1[:5000]}

Documento 2:
{content2[:5000]}

Análisis comparativo:"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.5
            )
            
            return {
                'comparison': response.choices[0].message.content,
                'type': comparison_type,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def analyze_image_content(
        self,
        image_path: Union[str, Path],
        analysis_type: str = "description"
    ) -> Dict[str, Any]:
        """
        Analiza el contenido de una imagen.
        
        Args:
            image_path: Ruta a la imagen
            analysis_type: Tipo de análisis (description, ocr, chart_analysis)
        
        Returns:
            Análisis de la imagen
        """
        if not self.vision_client:
            return {
                'error': 'No vision client available',
                'success': False
            }
        
        from tools.vision_utils import analyze_image_with_llm, extract_text_from_image, describe_chart_or_graph
        
        analysis_prompts = {
            'description': 'Describe detalladamente esta imagen.',
            'ocr': 'Extrae todo el texto visible en esta imagen.',
            'chart_analysis': 'Analiza este gráfico: tipo, datos, tendencias y conclusiones.'
        }
        
        try:
            if analysis_type == 'ocr':
                result = extract_text_from_image(self.vision_client, image_path, self.vision_model)
            elif analysis_type == 'chart_analysis':
                result = describe_chart_or_graph(self.vision_client, image_path, self.vision_model)
            else:
                result = analyze_image_with_llm(
                    self.vision_client,
                    image_path,
                    analysis_prompts.get(analysis_type, 'Describe esta imagen.'),
                    self.vision_model
                )
            
            return {
                'analysis': result,
                'type': analysis_type,
                'image_path': str(image_path),
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
