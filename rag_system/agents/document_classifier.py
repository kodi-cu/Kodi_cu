"""
Agente especializado en clasificación de documentos.

Clasifica documentos por:
- Tipo de archivo (PDF, ODT, ODP, etc.)
- Contenido (texto, tablas, imágenes)
- Tema o categoría (usando LLM)
- Estructura (formal, informal, técnico, etc.)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentClassification:
    """Resultado de la clasificación de un documento."""
    path: str
    file_type: str
    content_type: List[str]  # ej: ['texto', 'tablas', 'imagenes']
    category: Optional[str]  # ej: 'financiero', 'legal', 'tecnico'
    subcategory: Optional[str]
    confidence: float  # 0.0 a 1.0
    tags: List[str]
    language: Optional[str]
    complexity: str  # 'bajo', 'medio', 'alto'


class DocumentClassifierAgent:
    """
    Agente para clasificar documentos automáticamente.
    
    Usa reglas heurísticas y opcionalmente LLM para:
    - Detectar tipo de contenido
    - Categorizar por tema
    - Asignar etiquetas
    - Estimar complejidad
    """
    
    # Categorías predefinidas basadas en palabras clave
    CATEGORY_KEYWORDS = {
        'financiero': [
            'balance', 'presupuesto', 'gasto', 'ingreso', 'factura',
            'impuesto', 'contabilidad', 'auditoría', 'financial', 'budget'
        ],
        'legal': [
            'contrato', 'ley', 'normativa', 'cláusula', 'demand',
            'tribunal', 'abogado', 'legal', 'regulation', 'compliance'
        ],
        'tecnico': [
            'especificación', 'implementación', 'código', 'api',
            'arquitectura', 'documento técnico', 'manual', 'specification'
        ],
        'administrativo': [
            'procedimiento', 'política', 'norma interna', 'memorándum',
            'circuito', 'organigrama', 'policy', 'procedure'
        ],
        'comercial': [
            'propuesta', 'oferta', 'cliente', 'venta', 'marketing',
            'producto', 'servicio', 'proposal', 'commercial'
        ],
        'recursos_humanos': [
            'empleado', 'nómina', 'contratación', 'evaluación',
            'capacitación', 'hr', 'personal', 'training'
        ],
        'investigacion': [
            'estudio', 'análisis', 'datos', 'resultados', 'metodología',
            'research', 'analysis', 'findings', 'conclusiones'
        ],
        'educativo': [
            'curso', 'lección', 'examen', 'material didáctico',
            'syllabus', 'educational', 'training material'
        ],
    }
    
    CONTENT_INDICATORS = {
        'tablas': ['|', '\t', 'columna', 'fila', 'tabla', 'table'],
        'listas': ['- ', '* ', '• ', '1.', '2.', '3.'],
        'codigo': ['```', 'def ', 'function', 'import ', 'class ', 'var '],
        'imagenes': ['[IMG', '[IMAGE', '<img', '!['],
        'ecuaciones': ['=', '∑', '∫', '√', '²', '³'],
    }
    
    def __init__(self, llm_client=None, heuristic_threshold: float = 0.7):
        """
        Inicializa el clasificador.
        
        Args:
            llm_client: Cliente OpenAI-compatible para clasificación con LLM
            heuristic_threshold: Umbral de confianza (0-1). Si la heurística 
                                 tiene confianza < threshold, usa LLM. Default: 0.7
        """
        self.llm_client = llm_client
        self.heuristic_threshold = heuristic_threshold
        
        # Estadísticas de clasificación
        self.stats = {
            'total_classifications': 0,
            'heuristic_classifications': 0,
            'llm_classifications': 0,
        }
    
    def classify(self, content: str, file_path: str = "", use_llm: bool = None) -> DocumentClassification:
        """
        Clasifica un documento basado en su contenido.
        
        Usa heurística por defecto. Solo usa LLM si:
        - La confianza heurística es menor al umbral configurado
        - Se fuerza explícitamente con use_llm=True
        
        Args:
            content: Contenido del documento
            file_path: Ruta al archivo (opcional)
            use_llm: Forzar uso de LLM (None = automático según umbral)
            
        Returns:
            DocumentClassification con los resultados
        """
        self.stats['total_classifications'] += 1
        
        # Primero siempre hacer clasificación heurística
        file_type = Path(file_path).suffix.lower().lstrip('.') if file_path else 'unknown'
        
        # Detectar tipo de contenido
        content_types = self._detect_content_types(content)
        
        # Detectar categoría heurística
        category, subcategory, confidence = self._detect_category(content)
        
        # Detectar idioma
        language = self._detect_language(content)
        
        # Estimar complejidad
        complexity = self._estimate_complexity(content)
        
        # Generar tags
        tags = self._generate_tags(content, category, content_types)
        
        # Decidir si usar LLM
        should_use_llm = use_llm if use_llm is not None else (confidence < self.heuristic_threshold)
        
        if should_use_llm and self.llm_client:
            # Usar LLM para mejorar clasificación
            self.stats['llm_classifications'] += 1
            llm_result = self._classify_with_llm_internal(content, file_path)
            
            # Combinar resultados: mantener lo que LLM hace mejor, usar heurística para lo demás
            return DocumentClassification(
                path=file_path,
                file_type=file_type,
                content_type=content_types,
                category=llm_result.get('category', category),
                subcategory=llm_result.get('subcategory', subcategory),
                confidence=llm_result.get('confidence', confidence),
                tags=llm_result.get('keywords', tags),
                language=llm_result.get('language', language),
                complexity=llm_result.get('complexity', complexity),
            )
        else:
            # Usar solo heurística
            self.stats['heuristic_classifications'] += 1
            return DocumentClassification(
                path=file_path,
                file_type=file_type,
                content_type=content_types,
                category=category,
                subcategory=subcategory,
                confidence=confidence,
                tags=tags,
                language=language,
                complexity=complexity,
            )
    
    def _detect_content_types(self, content: str) -> List[str]:
        """Detecta tipos de contenido presentes."""
        types = ['texto']  # Por defecto todo tiene texto
        
        for content_type, indicators in self.CONTENT_INDICATORS.items():
            count = sum(1 for ind in indicators if ind in content)
            if count >= 1:
                types.append(content_type)
        
        return types
    
    def _detect_category(self, content: str) -> tuple:
        """
        Detecta categoría principal basada en palabras clave.
        
        Returns:
            (categoria, subcategoria, confianza)
        """
        content_lower = content.lower()
        scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[category] = score
        
        if not scores:
            return ('general', None, 0.5)
        
        # Ordenar por score
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_category = sorted_categories[0][0]
        top_score = sorted_categories[0][1]
        
        # Calcular confianza normalizada
        max_possible = max(len(kw) for kw in self.CATEGORY_KEYWORDS.values())
        confidence = min(top_score / max_possible, 1.0)
        
        # Determinar subcategoría si hay empate cercano
        subcategory = None
        if len(sorted_categories) > 1 and sorted_categories[1][1] >= top_score * 0.7:
            subcategory = sorted_categories[1][0]
        
        return (top_category, subcategory, confidence)
    
    def _detect_language(self, content: str) -> str:
        """Detecta idioma del contenido (simple heuristic)."""
        content_lower = content.lower()
        
        # Palabras comunes por idioma
        spanish_markers = ['el', 'la', 'los', 'las', 'de', 'que', 'en', 'es', 'un', 'una']
        english_markers = ['the', 'and', 'of', 'to', 'in', 'is', 'a', 'an', 'for', 'on']
        
        spanish_count = sum(1 for word in spanish_markers if f' {word} ' in f' {content_lower} ')
        english_count = sum(1 for word in english_markers if f' {word} ' in f' {content_lower} ')
        
        if spanish_count > english_count * 1.5:
            return 'es'
        elif english_count > spanish_count * 1.5:
            return 'en'
        else:
            return 'mixed'
    
    def _estimate_complexity(self, content: str) -> str:
        """Estima complejidad del documento."""
        words = content.split()
        word_count = len(words)
        
        # Métricas simples
        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0
        
        # Contar párrafos
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Puntuación de complejidad
        complexity_score = 0
        
        if word_count > 2000:
            complexity_score += 2
        elif word_count > 500:
            complexity_score += 1
        
        if avg_word_length > 7:
            complexity_score += 1
        
        if paragraph_count > 20:
            complexity_score += 1
        
        # Verificar tecnicismos
        technical_terms = ['implementación', 'arquitectura', 'metodología', 'algoritmo', 
                          'framework', 'paradigma', 'infraestructura']
        tech_count = sum(1 for term in technical_terms if term in content.lower())
        if tech_count > 3:
            complexity_score += 1
        
        if complexity_score >= 4:
            return 'alto'
        elif complexity_score >= 2:
            return 'medio'
        else:
            return 'bajo'
    
    def _generate_tags(self, content: str, category: str, content_types: List[str]) -> List[str]:
        """Genera etiquetas descriptivas."""
        tags = []
        content_lower = content.lower()
        
        # Tags basados en categoría
        if category:
            tags.append(category)
        
        # Tags basados en tipo de contenido
        tags.extend(content_types)
        
        # Tags basados en patrones específicos
        if any(term in content_lower for term in ['resumen', 'abstract', 'summary']):
            tags.append('tiene_resumen')
        
        if any(term in content_lower for term in ['conclusión', 'conclusiones', 'conclusion']):
            tags.append('tiene_conclusiones')
        
        if any(term in content_lower for term in ['bibliografía', 'referencias', 'references']):
            tags.append('tiene_referencias')
        
        if 'índice' in content_lower or 'tabla de contenidos' in content_lower:
            tags.append('tiene_indice')
        
        # Tags temporales
        import re
        years = re.findall(r'\b(20\d{2}|19\d{2})\b', content)
        if years:
            tags.append(f'año_{max(years)}')
        
        return list(set(tags))  # Eliminar duplicados
    
    def _classify_with_llm_internal(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Método interno para clasificación con LLM.
        Retorna solo el diccionario del LLM sin crear DocumentClassification.
        
        Args:
            content: Contenido del documento
            file_path: Ruta al archivo
            
        Returns:
            Diccionario con resultados del LLM
        """
        if not self.llm_client:
            return {}
        
        prompt = f"""Analiza el siguiente documento y clasifícalo:

Instrucciones:
1. Identifica el tipo de documento (informe, contrato, manual, presentación, etc.)
2. Determina la categoría principal (financiero, legal, técnico, administrativo, etc.)
3. Extrae 5-10 palabras clave relevantes
4. Estima el nivel de complejidad (bajo, medio, alto)
5. Identifica el idioma principal

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
    "document_type": "...",
    "category": "...",
    "subcategory": "..." o null,
    "keywords": ["...", "..."],
    "complexity": "bajo|medio|alto",
    "language": "es|en|mixed",
    "confidence": 0.0-1.0,
    "summary": "Breve resumen de 1-2 líneas"
}}

Contenido del documento (primeros 3000 caracteres):
{content[:3000]}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="local-model",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            
            import json
            llm_result = json.loads(response.choices[0].message.content)
            return llm_result
        except Exception as e:
            print(f"Error en clasificación con LLM: {e}")
            return {}
    
    def classify_with_llm(self, content: str, file_path: str = "") -> DocumentClassification:
        """
        Clasifica usando LLM para mayor precisión (fuerza uso de LLM).
        
        Método público para cuando se quiere forzar explícitamente el uso de LLM.
        Para uso automático según umbral, usar classify().
        
        Args:
            content: Contenido del documento
            file_path: Ruta al archivo
            
        Returns:
            DocumentClassification
        """
        # Delegar al método classify con use_llm=True
        return self.classify(content, file_path, use_llm=True)
    
    def batch_classify(self, contents: List[tuple]) -> List[DocumentClassification]:
        """
        Clasifica múltiples documentos.
        
        Args:
            contents: Lista de tuplas (contenido, ruta)
            
        Returns:
            Lista de DocumentClassification
        """
        results = []
        for content, path in contents:
            result = self.classify(content, path)
            results.append(result)
        return results
    
    def get_classification_summary(self, classifications: List[DocumentClassification]) -> Dict[str, Any]:
        """
        Genera resumen de clasificaciones.
        
        Args:
            classifications: Lista de clasificaciones
            
        Returns:
            Diccionario con estadísticas
        """
        by_category = {}
        by_complexity = {'bajo': 0, 'medio': 0, 'alto': 0}
        by_language = {}
        all_tags = []
        
        for cls in classifications:
            # Por categoría
            cat = cls.category or 'unknown'
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # Por complejidad
            by_complexity[cls.complexity] = by_complexity.get(cls.complexity, 0) + 1
            
            # Por idioma
            lang = cls.language or 'unknown'
            by_language[lang] = by_language.get(lang, 0) + 1
            
            # Todos los tags
            all_tags.extend(cls.tags)
        
        # Tags más comunes
        from collections import Counter
        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(10)
        
        return {
            'total_documents': len(classifications),
            'by_category': by_category,
            'by_complexity': by_complexity,
            'by_language': by_language,
            'top_tags': top_tags,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de clasificación.
        
        Returns:
            Diccionario con estadísticas de uso de heurística vs LLM
        """
        total = max(self.stats['total_classifications'], 1)
        return {
            **self.stats,
            'heuristic_rate_percent': round(self.stats['heuristic_classifications'] / total * 100, 2),
            'llm_rate_percent': round(self.stats['llm_classifications'] / total * 100, 2),
            'threshold_configured': self.heuristic_threshold,
        }
    
    def reset_stats(self):
        """Reinicia las estadísticas de clasificación."""
        self.stats = {
            'total_classifications': 0,
            'heuristic_classifications': 0,
            'llm_classifications': 0,
        }
