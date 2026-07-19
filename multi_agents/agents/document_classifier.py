"""Agente DocumentClassifier - Clasificación de documentos"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import re


class DocumentClassifierAgent:
    """
    Agente especializado en clasificar documentos por categoría.
    OPTIMIZACIÓN: Usa heurística por defecto y solo llama al LLM cuando
    la confianza heurística es baja (< 70%).
    """
    
    # Palabras clave por categoría para clasificación heurística
    CATEGORY_KEYWORDS = {
        'legal': [
            'contrato', 'ley', 'legislación', 'jurídico', 'demanda', 'tribunal',
            'abogado', 'normativa', 'reglamento', 'cláusula', 'fianza', 'garantía',
            'litigio', 'sentencia', 'derecho', 'legal', 'judicial'
        ],
        'financiero': [
            'balance', 'contabilidad', 'presupuesto', 'factura', 'impuesto',
            'hacienda', 'banco', 'inversión', 'crédito', 'débito', 'dividendo',
            'estado financiero', 'audit', 'cash flow', 'ebitda', 'roi'
        ],
        'tecnico': [
            'especificación', 'manual técnico', 'arquitectura', 'código',
            'algoritmo', 'base de datos', 'api', 'servidor', 'red', 'software',
            'hardware', 'desarrollo', 'programación', 'sistema', 'técnico'
        ],
        'administrativo': [
            'oficio', 'memorando', 'circuito', 'procedimiento', 'política',
            'directriz', 'organigrama', 'recurso humano', 'nomina', 'empleado',
            'administración', 'gestión', 'trámite', 'expediente'
        ],
        'comercial': [
            'venta', 'cliente', 'producto', 'mercado', 'marketing', 'precio',
            'cotización', 'pedido', 'facturación', 'comercial', 'negocio',
            'estrategia comercial', 'portfolio', 'catálogo'
        ],
        'rrhh': [
            'recurso humano', 'empleo', 'currículum', 'entrevista', 'contratación',
            'formación', 'capacitación', 'evaluación', 'desempeño', 'salario',
            'beneficio', 'vacaciones', 'ausencia', 'personal'
        ],
        'marketing': [
            'campaña', 'publicidad', 'branding', 'redes sociales', 'seo',
            'contenido', 'audiencia', 'engagement', 'conversion', 'promoción',
            'evento', 'lanzamiento', 'comunicación', 'prensa'
        ],
        'investigacion': [
            'investigación', 'estudio', 'análisis', 'datos', 'metodología',
            'resultados', 'conclusión', 'hipótesis', 'experimento', 'muestra',
            'estadística', 'paper', 'artículo científico', 'tesis'
        ]
    }
    
    # Umbrales de confianza
    HIGH_CONFIDENCE_THRESHOLD = 0.7  # Si heurística >= 70%, no usar LLM
    LOW_CONFIDENCE_THRESHOLD = 0.3   # Si heurística < 30%, definitivamente usar LLM
    
    def __init__(self, llm_client=None, model_name: str = "local-model"):
        """
        Inicializa el clasificador.
        
        Args:
            llm_client: Cliente LLM para clasificación cuando sea necesario
            model_name: Nombre del modelo a usar
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.categories = list(self.CATEGORY_KEYWORDS.keys())
    
    def classify(
        self,
        content: str,
        file_path: Optional[Union[str, Path]] = None,
        force_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Clasifica un documento por categoría.
        
        Args:
            content: Contenido del documento
            file_path: Ruta al archivo (opcional, para contexto adicional)
            force_llm: Si True, usa LLM siempre (ignora heurística)
        
        Returns:
            Diccionario con categoría, confianza y método usado
        """
        if force_llm or not content:
            return self._classify_with_llm(content, file_path)
        
        # Intentar clasificación heurística primero
        heuristic_result = self._classify_heuristic(content, file_path)
        
        # Si la confianza es alta, devolver resultado sin usar LLM
        if heuristic_result['confidence'] >= self.HIGH_CONFIDENCE_THRESHOLD:
            heuristic_result['method'] = 'heuristic'
            heuristic_result['llm_used'] = False
            return heuristic_result
        
        # Si la confianza es baja, mejorar con LLM
        if heuristic_result['confidence'] < self.LOW_CONFIDENCE_THRESHOLD:
            llm_result = self._classify_with_llm(content, file_path)
            llm_result['method'] = 'llm'
            llm_result['heuristic_confidence'] = heuristic_result['confidence']
            llm_result['llm_used'] = True
            return llm_result
        
        # Confianza media: promediar heurística y LLM si está disponible
        if self.llm_client:
            llm_result = self._classify_with_llm(content, file_path)
            
            # Promediar confianzas
            avg_confidence = (heuristic_result['confidence'] + llm_result['confidence']) / 2
            
            # Usar la categoría con mayor confianza combinada
            if llm_result['confidence'] > heuristic_result['confidence']:
                result = llm_result.copy()
                result['confidence'] = avg_confidence
            else:
                result = heuristic_result.copy()
                result['confidence'] = avg_confidence
            
            result['method'] = 'hybrid'
            result['llm_used'] = True
            return result
        
        # No hay LLM disponible, devolver heurística
        heuristic_result['method'] = 'heuristic_fallback'
        heuristic_result['llm_used'] = False
        return heuristic_result
    
    def _classify_heuristic(
        self,
        content: str,
        file_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Clasificación basada en palabras clave (heurística).
        
        Args:
            content: Contenido del documento
            file_path: Ruta al archivo para contexto adicional
        
        Returns:
            Resultado de clasificación con confianza
        """
        content_lower = content.lower()[:10000]  # Limitar para performance
        
        # Añadir nombre del archivo al contenido para análisis
        if file_path:
            file_name = Path(file_path).name.lower()
            content_lower = f"{file_name} {content_lower}"
        
        scores = {}
        total_words = len(content_lower.split())
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            match_count = 0
            for keyword in keywords:
                # Contar ocurrencias de cada palabra clave
                matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower))
                match_count += matches
            
            # Calcular score normalizado
            if total_words > 0:
                # Peso: frecuencia de keywords / total de palabras * factor de amplificación
                raw_score = (match_count / total_words) * 100
                # Aplicar log para evitar scores demasiado altos
                import math
                normalized_score = min(1.0, math.log(raw_score + 1) / math.log(50))
            else:
                normalized_score = 0.0
            
            scores[category] = normalized_score
        
        # Encontrar categoría con mayor score
        best_category = max(scores, key=scores.get)
        best_confidence = scores[best_category]
        
        # Calcular distribución de probabilidades
        total_score = sum(scores.values())
        if total_score > 0:
            probabilities = {k: v / total_score for k, v in scores.items()}
        else:
            probabilities = {k: 1.0 / len(scores) for k in scores}
        
        return {
            'category': best_category,
            'confidence': best_confidence,
            'all_scores': scores,
            'probabilities': probabilities,
            'keywords_matched': self._get_matched_keywords(content_lower, best_category)
        }
    
    def _get_matched_keywords(self, content: str, category: str) -> List[str]:
        """Obtiene las palabras clave que matchearon en el contenido"""
        matched = []
        for keyword in self.CATEGORY_KEYWORDS.get(category, []):
            if re.search(r'\b' + re.escape(keyword) + r'\b', content):
                matched.append(keyword)
        return matched[:10]  # Limitar a 10 keywords
    
    def _classify_with_llm(
        self,
        content: str,
        file_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Clasificación usando LLM.
        
        Args:
            content: Contenido del documento
            file_path: Ruta al archivo
        
        Returns:
            Resultado de clasificación con confianza
        """
        if not self.llm_client:
            return {
                'category': 'otros',
                'confidence': 0.5,
                'error': 'No LLM client available',
                'llm_used': False
            }
        
        # Preparar prompt
        file_context = f"Archivo: {Path(file_path).name}\n" if file_path else ""
        
        prompt = f"""{file_context}
Clasifica el siguiente documento en UNA de estas categorías:
{', '.join(self.categories)}

Contenido:
{content[:5000]}  # Limitar contenido para no exceder tokens

Responde ÚNICAMENTE con el formato JSON:
{{
    "category": "nombre_categoria",
    "confidence": 0.XX,
    "reasoning": "breve explicación"
}}"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parsear respuesta JSON
            import json
            result = json.loads(result_text)
            
            return {
                'category': result.get('category', 'otros'),
                'confidence': float(result.get('confidence', 0.5)),
                'reasoning': result.get('reasoning', ''),
                'llm_used': True
            }
        except Exception as e:
            return {
                'category': 'otros',
                'confidence': 0.5,
                'error': str(e),
                'llm_used': True
            }
    
    def classify_batch(
        self,
        documents: List[Dict[str, Any]],
        max_llm_calls: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Clasifica múltiples documentos optimizando llamadas al LLM.
        
        Args:
            documents: Lista de diccionarios con 'content' y opcionalmente 'path'
            max_llm_calls: Máximo de llamadas al LLM permitidas
        
        Returns:
            Lista de resultados de clasificación
        """
        results = []
        llm_calls_count = 0
        
        for doc in documents:
            content = doc.get('content', '')
            path = doc.get('path')
            
            # Solo usar LLM si es necesario y tenemos cuota
            use_llm = llm_calls_count < max_llm_calls
            
            result = self.classify(
                content,
                path,
                force_llm=False and use_llm
            )
            
            if result.get('llm_used'):
                llm_calls_count += 1
            
            results.append(result)
        
        return results
