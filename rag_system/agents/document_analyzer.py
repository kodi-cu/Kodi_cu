"""
Agente especializado en análisis profundo de documentos.

Realiza:
- Resumen automático
- Extracción de puntos clave
- Detección de entidades
- Análisis de sentimiento (si aplica)
- Identificación de acciones requeridas
- Comparación entre documentos
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DocumentAnalysis:
    """Resultado del análisis de un documento."""
    summary: str
    key_points: List[str]
    entities: Dict[str, List[str]]  # tipo -> lista de entidades
    action_items: List[str]
    questions_answered: List[Dict[str, str]]  # pregunta -> respuesta
    sentiment: Optional[str]  # positivo, negativo, neutral
    confidence: float
    metadata: Dict[str, Any]


class DocumentAnalyzerAgent:
    """
    Agente para análisis profundo de documentos usando LLM.
    
    Realiza análisis semántico y estructural para extraer:
    - Resúmenes ejecutivos
    - Puntos clave
    - Entidades nombradas
    - Acciones requeridas
    - Relaciones entre conceptos
    """
    
    def __init__(self, llm_client):
        """
        Inicializa el analizador.
        
        Args:
            llm_client: Cliente OpenAI-compatible
        """
        self.llm_client = llm_client
    
    def analyze(self, content: str, file_path: str = "", 
                analysis_type: str = "complete") -> DocumentAnalysis:
        """
        Analiza un documento completo.
        
        Args:
            content: Contenido del documento
            file_path: Ruta al archivo
            analysis_type: 'summary', 'keypoints', 'entities', 'complete'
            
        Returns:
            DocumentAnalysis con resultados
        """
        if analysis_type == "summary":
            return self._analyze_summary(content, file_path)
        elif analysis_type == "keypoints":
            return self._analyze_keypoints(content, file_path)
        elif analysis_type == "entities":
            return self._analyze_entities(content, file_path)
        else:
            return self._analyze_complete(content, file_path)
    
    def _analyze_complete(self, content: str, file_path: str) -> DocumentAnalysis:
        """Análisis completo del documento."""
        prompt = f"""Analiza exhaustivamente el siguiente documento:

=== DOCUMENTO ===
{content[:4000]}  # Limitar para no exceder contexto

Proporciona un análisis estructurado con:

1. RESUMEN EJECUTIVO (2-3 párrafos)
2. PUNTOS CLAVE (lista de 5-10 puntos más importantes)
3. ENTIDADES MENCIONADAS (personas, organizaciones, lugares, fechas, cantidades)
4. ACCIONES REQUERIDAS (tareas, deadlines, responsables si se mencionan)
5. TEMA PRINCIPAL y TEMAS SECUNDARIOS
6. NIVEL DE URGENCIA (si aplica): bajo, medio, alto

Responde ÚNICAMENTE en formato JSON:
{{
    "summary": "...",
    "key_points": ["...", "..."],
    "entities": {{
        "personas": ["..."],
        "organizaciones": ["..."],
        "fechas": ["..."],
        "cantidades": ["..."]
    }},
    "action_items": [
        {{"task": "...", "deadline": "...", "responsible": "..."}}
    ],
    "main_topic": "...",
    "secondary_topics": ["...", "..."],
    "urgency": "bajo|medio|alto|N/A",
    "confidence": 0.0-1.0
}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="local-model",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return DocumentAnalysis(
                summary=result.get('summary', ''),
                key_points=result.get('key_points', []),
                entities=result.get('entities', {}),
                action_items=[item.get('task', '') for item in result.get('action_items', [])],
                questions_answered=[],
                sentiment=None,
                confidence=result.get('confidence', 0.5),
                metadata={
                    'main_topic': result.get('main_topic', ''),
                    'secondary_topics': result.get('secondary_topics', []),
                    'urgency': result.get('urgency', 'N/A'),
                    'source': file_path,
                }
            )
        except Exception as e:
            print(f"Error en análisis: {e}")
            return DocumentAnalysis(
                summary=f"[Error en análisis: {str(e)}]",
                key_points=[],
                entities={},
                action_items=[],
                questions_answered=[],
                sentiment=None,
                confidence=0.0,
                metadata={'error': str(e)},
            )
    
    def _analyze_summary(self, content: str, file_path: str) -> DocumentAnalysis:
        """Genera solo resumen."""
        prompt = f"""Resume el siguiente documento en 2-3 párrafos claros y concisos:

{content[:3000]}

Responde SOLO con el resumen, sin introducciones ni conclusiones adicionales.
"""
        
        response = self.llm_client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        
        return DocumentAnalysis(
            summary=response.choices[0].message.content.strip(),
            key_points=[],
            entities={},
            action_items=[],
            questions_answered=[],
            sentiment=None,
            confidence=0.8,
            metadata={'source': file_path, 'analysis_type': 'summary'},
        )
    
    def _analyze_keypoints(self, content: str, file_path: str) -> DocumentAnalysis:
        """Extrae solo puntos clave."""
        prompt = f"""Extrae los 5-10 puntos más importantes del siguiente documento:

{content[:3000]}

Responde ÚNICAMENTE con una lista JSON de strings:
["punto 1", "punto 2", ...]
"""
        
        response = self.llm_client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        
        import json
        key_points = json.loads(response.choices[0].message.content)
        
        return DocumentAnalysis(
            summary="",
            key_points=key_points,
            entities={},
            action_items=[],
            questions_answered=[],
            sentiment=None,
            confidence=0.8,
            metadata={'source': file_path, 'analysis_type': 'keypoints'},
        )
    
    def _analyze_entities(self, content: str, file_path: str) -> DocumentAnalysis:
        """Extrae entidades nombradas."""
        prompt = f"""Extrae todas las entidades mencionadas en el siguiente documento:

{content[:3000]}

Clasifícalas en categorías y responde en JSON:
{{
    "personas": ["nombre1", "nombre2"],
    "organizaciones": ["org1", "org2"],
    "lugares": ["lugar1", "lugar2"],
    "fechas": ["fecha1", "fecha2"],
    "cantidades": ["cantidad1", "cantidad2"],
    "productos": ["prod1", "prod2"]
}}
"""
        
        response = self.llm_client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        
        import json
        entities = json.loads(response.choices[0].message.content)
        
        return DocumentAnalysis(
            summary="",
            key_points=[],
            entities=entities,
            action_items=[],
            questions_answered=[],
            sentiment=None,
            confidence=0.8,
            metadata={'source': file_path, 'analysis_type': 'entities'},
        )
    
    def answer_questions(self, content: str, questions: List[str]) -> List[Dict[str, str]]:
        """
        Responde preguntas específicas sobre el documento.
        
        Args:
            content: Contenido del documento
            questions: Lista de preguntas
            
        Returns:
            Lista de diccionarios {pregunta, respuesta}
        """
        results = []
        
        for question in questions:
            prompt = f"""Basándote ÚNICAMENTE en el siguiente documento, responde la pregunta:

DOCUMENTO:
{content[:3000]}

PREGUNTA: {question}

Si la respuesta no está en el documento, di "No se encuentra información en el documento".
Responde de forma concisa.
"""
            
            response = self.llm_client.chat.completions.create(
                model="local-model",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            
            results.append({
                'question': question,
                'answer': response.choices[0].message.content.strip(),
            })
        
        return results
    
    def compare_documents(self, content1: str, content2: str, 
                         comparison_aspect: str = "general") -> Dict[str, Any]:
        """
        Compara dos documentos.
        
        Args:
            content1: Contenido del primer documento
            content2: Contenido del segundo documento
            comparison_aspect: 'general', 'contradicciones', 'complemento', etc.
            
        Returns:
            Diccionario con comparación
        """
        prompt = f"""Compara los siguientes dos documentos enfocándote en: {comparison_aspect}

DOCUMENTO 1:
{content1[:2000]}

DOCUMENTO 2:
{content2[:2000]}

Proporciona un análisis comparativo en JSON:
{{
    "similarities": ["...", "..."],
    "differences": ["...", "..."],
    "contradictions": ["...", "..."],
    "complementary_info": ["...", "..."],
    "recommendation": "..."
}}
"""
        
        response = self.llm_client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def extract_structure(self, content: str) -> Dict[str, Any]:
        """
        Extrae la estructura del documento (secciones, subtítulos).
        
        Args:
            content: Contenido del documento
            
        Returns:
            Estructura jerárquica
        """
        lines = content.split('\n')
        structure = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Detectar posibles títulos
            if stripped.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = stripped.lstrip('#').strip()
                structure.append({
                    'type': 'heading',
                    'level': min(level, 6),
                    'content': title,
                })
            elif len(stripped) < 100 and stripped.endswith(':'):
                structure.append({
                    'type': 'subheading',
                    'content': stripped[:-1],
                })
        
        return {
            'headings': structure,
            'total_sections': len([s for s in structure if s['type'] == 'heading']),
        }
