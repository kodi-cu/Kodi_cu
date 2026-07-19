"""
Orquestador de Agentes para Gestión Documental

Coordina múltiples agentes especializados para:
- Recibir instrucciones en lenguaje natural
- Coordinar búsqueda, lectura, análisis y gestión
- Retornar respuestas coherentes y completas

Optimizaciones:
- Cacheo de intenciones comunes para evitar llamadas innecesarias al LLM
- Umbral de confianza para clasificación heurística vs LLM
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from collections import OrderedDict


class IntentCache:
    """
    Cache LRU para intenciones comunes.
    Evita llamar al LLM para patrones frecuentes.
    """
    
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtiene intención cacheada."""
        if key in self.cache:
            self.hits += 1
            # Mover al final (más reciente)
            self.cache.move_to_end(key)
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, key: str, value: Dict[str, Any]):
        """Guarda intención en cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)  # Eliminar el más antiguo
            self.cache[key] = value
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de cache."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate_percent': round(hit_rate, 2),
            'cached_items': len(self.cache),
        }


class AgentOrchestrator:
    """
    Orquestador que coordina todos los agentes del sistema.
    
    Flujo típico:
    1. Recibe instrucción del usuario
    2. Detecta patrón común (cache) o analiza intención (LLM)
    3. Coordina agentes necesarios
    4. Consolida resultados
    5. Retorna respuesta
    
    Optimizaciones:
    - Patrones comunes se detectan sin LLM (regex + cache)
    - Solo se usa LLM cuando no hay match con patrones conocidos
    """
    
    # Patrones regex para intenciones comunes (sin necesidad de LLM)
    COMMON_PATTERNS = {
        'BUSCAR_ARCHIVOS': [
            r'(?i)\b(busca|buscar|encuentra|encontrar|localiza)\b.*\b(archivo|archivos|documento|documentos|pdf|odt|fichero)\b',
            r'(?i)\bdónde\s+(está|están|hay|quedan)\b.*\b(archivo|documentos|pdf)\b',
            r'(?i)\b(muéstrame|muestra|lista|listar)\b.*\b(archivos|documentos|pdfs)\b',
            r'(?i)\b(busco|necesito)\b.*\b(archivo|documento|pdf|informe)\b',
        ],
        'LEER_DOCUMENTO': [
            r'(?i)\b(lee|leer|abre|abrir|muestra|mostrar)\b.*\b(este|el|ese|aquel)\b.*\b(archivo|documento)\b',
            r'(?i)\b(qué\s+dice|qué\s+contiene|contenido)\b.*\b(archivo|documento)\b',
        ],
        'CLASIFICAR_DOCUMENTO': [
            r'(?i)\b(clasifica|clasificar|categoriza|categorizar|etiqueta|etiquetar)\b.*\b(documento|archivo)\b',
            r'(?i)\b(de\s+qué\s+trata|qué\s+tipo\s+es|qué\s+categoría)\b',
        ],
        'ANALIZAR_DOCUMENTO': [
            r'(?i)\b(analiza|analizar|resume|resumir|sintetiza|sintetizar)\b.*\b(documento|archivo)\b',
            r'(?i)\b(puntos\s+clave|ideas\s+principales|conclusiones|resumen)\b.*\b(documento|archivo)\b',
        ],
        'CREAR_DOCUMENTO': [
            r'(?i)\b(crea|crear|genera|generar|redacta|redactar|escribe|escribir)\b.*\b(documento|archivo|texto|informe)\b',
            r'(?i)\bnecesito\s+un\b.*\b(documento|informe|reporte|carta)\b',
        ],
        'ORGANIZAR_ARCHIVOS': [
            r'(?i)\b(organiza|organizar|ordena|ordenar|clasifica)\b.*\b(archivos|carpetas|directorios)\b',
            r'(?i)\b(mueve|mover|copia|copiar|renombrar)\b.*\b(archivo|archivos)\b',
        ],
        'COMPARAR_DOCUMENTOS': [
            r'(?i)\b(compara|comparar|diferencias|similitudes)\b.*\b(documentos|archivos)\b',
        ],
        'RESPONDER_PREGUNTA': [
            r'(?i)^(\bcuál\b|\bcuales\b|\bqué\b|\bquién\b|\bquienes\b|\bcuándo\b|\bdónde\b|\bpor\s+qué\b|\bcómo\b)',
            r'(?i)\b(explica|dime|cuéntame)\b.*\b(sobre|acerca\s+de)\b',
        ],
    }
    
    def __init__(self, llm_client, base_directory: str = ".", enable_cache: bool = True):
        """
        Inicializa el orquestador con todos los agentes.
        
        Args:
            llm_client: Cliente OpenAI-compatible para LLM
            base_directory: Directorio base para operaciones
            enable_cache: Habilitar cache de intenciones (default: True)
        """
        self.llm_client = llm_client
        self.enable_cache = enable_cache
        
        # Importar e inicializar agentes
        from .file_finder import FileFinderAgent
        from .document_reader import DocumentReaderAgent
        from .document_classifier import DocumentClassifierAgent
        from .document_analyzer import DocumentAnalyzerAgent
        from .document_manager import DocumentManagerAgent
        
        self.file_finder = FileFinderAgent(base_directory)
        self.document_reader = DocumentReaderAgent()
        self.document_classifier = DocumentClassifierAgent(
            llm_client, 
            heuristic_threshold=0.7  # Umbral: si < 0.7, usar LLM
        )
        self.document_analyzer = DocumentAnalyzerAgent(llm_client)
        self.document_manager = DocumentManagerAgent(base_directory)
        
        # Cache de intenciones
        self.intent_cache = IntentCache(max_size=100) if enable_cache else None
        
        # Estadísticas
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'pattern_matches': 0,
            'llm_calls': 0,
        }
        
        # Historial de acciones
        self.action_history = []
    
    def process_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Procesa una instrucción en lenguaje natural.
        
        Flujo optimizado:
        1. Normalizar instrucción
        2. Buscar en cache (si habilitado)
        3. Detectar patrón común con regex
        4. Si no hay match, usar LLM
        5. Ejecutar acción y cacheear resultado
        
        Args:
            instruction: Instrucción del usuario
            
        Returns:
            Resultado consolidado
        """
        self.stats['total_requests'] += 1
        
        # Paso 1: Normalizar instrucción para cache
        normalized = self._normalize_instruction(instruction)
        
        # Paso 2: Buscar en cache (si habilitado)
        if self.enable_cache and self.intent_cache:
            cached_intent = self.intent_cache.get(normalized)
            if cached_intent:
                self.stats['cache_hits'] += 1
                result = self._execute_action(cached_intent, instruction)
                self.action_history.append({
                    'instruction': instruction,
                    'intent': cached_intent,
                    'result': result,
                    'from_cache': True,
                })
                return result
        
        # Paso 3: Intentar detectar patrón común (sin LLM)
        intent = self._detect_pattern(instruction)
        
        if intent:
            self.stats['pattern_matches'] += 1
            # Cacheear si está habilitado
            if self.enable_cache and self.intent_cache:
                self.intent_cache.put(normalized, intent)
        else:
            # Paso 4: No hay patrón conocido, usar LLM
            intent = self._analyze_intent_with_llm(instruction)
            self.stats['llm_calls'] += 1
            # Cacheear resultado para futuras consultas
            if self.enable_cache and self.intent_cache:
                self.intent_cache.put(normalized, intent)
        
        # Paso 5: Ejecutar acción
        result = self._execute_action(intent, instruction)
        
        # Paso 6: Registrar en historial
        self.action_history.append({
            'instruction': instruction,
            'intent': intent,
            'result': result,
            'from_cache': False,
            'used_llm': intent.get('_used_llm', False),
        })
        
        return result
    
    def _normalize_instruction(self, instruction: str) -> str:
        """
        Normaliza instrucción para usar como clave de cache.
        
        - Minúsculas
        - Eliminar espacios múltiples
        - Eliminar puntuación excesiva
        """
        normalized = instruction.lower().strip()
        # Reemplazar múltiples espacios por uno solo
        normalized = re.sub(r'\s+', ' ', normalized)
        # Eliminar puntuación al inicio/final
        normalized = normalized.strip('.,!?;:')
        return normalized
    
    def _detect_pattern(self, instruction: str) -> Optional[Dict[str, Any]]:
        """
        Detecta intención usando patrones regex predefinidos.
        
        Args:
            instruction: Instrucción del usuario
            
        Returns:
            Diccionario con intención y parámetros, o None si no hay match
        """
        for action, patterns in self.COMMON_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, instruction):
                    # Extraer parámetros comunes según el tipo de acción
                    params = self._extract_params_from_pattern(action, instruction)
                    return {
                        'action': action,
                        'parameters': params,
                        'requires_multiple_steps': False,
                        'steps': [action.lower()],
                        '_used_llm': False,
                        '_matched_pattern': pattern[:50],  # Para debugging
                    }
        return None
    
    def _extract_params_from_pattern(self, action: str, instruction: str) -> Dict[str, Any]:
        """
        Extrae parámetros de la instrucción basado en el patrón detectado.
        
        Args:
            action: Acción detectada
            instruction: Instrucción original
            
        Returns:
            Diccionario con parámetros extraídos
        """
        params = {}
        instruction_lower = instruction.lower()
        
        # Extraer patrones de archivos comunes
        file_extensions = ['pdf', 'odt', 'odp', 'odg', 'docx', 'xlsx', 'pptx', 'txt']
        for ext in file_extensions:
            if ext in instruction_lower:
                params['file_type'] = ext
                break
        
        # Extraer directorio si se menciona
        dir_patterns = [r'en\s+la\s+carpeta\s+["\']?([^"\']+)["\']?', 
                        r'en\s+el\s+directorio\s+["\']?([^"\']+)["\']?',
                        r'ruta[:\s]+([^\s,]+)']
        for pattern in dir_patterns:
            match = re.search(pattern, instruction_lower)
            if match:
                params['directory'] = match.group(1).strip()
                break
        
        # Extraer nombre de archivo si se menciona
        file_patterns = [r'archivo\s+["\']?([^"\']+)["\']?', 
                         r'documento\s+["\']?([^"\']+)["\']?',
                         r'llamado\s+["\']?([^"\']+)["\']?']
        for pattern in file_patterns:
            match = re.search(pattern, instruction_lower)
            if match:
                params['pattern'] = f"*{match.group(1).strip()}*"
                break
        
        # Para búsqueda, usar instrucción completa como patrón si no hay nada específico
        if action == 'BUSCAR_ARCHIVOS' and 'pattern' not in params:
            # Extraer palabras después del verbo de búsqueda
            search_words = re.search(r'(?:busca|buscar|encuentra|encontrar)\s+(.+)', instruction_lower)
            if search_words:
                params['pattern'] = f"*{search_words.group(1).strip()}*"
        
        return params
    
    def _analyze_intent_with_llm(self, instruction: str) -> Dict[str, Any]:
        """
        Analiza la intención de la instrucción usando LLM (fallback).
        
        Solo se llama cuando los patrones regex no coinciden.
        
        Args:
            instruction: Instrucción del usuario
            
        Returns:
            Diccionario con intención y parámetros
        """
        prompt = f"""Analiza la siguiente instrucción y determina qué acción se debe realizar:

INSTRUCCIÓN: "{instruction}"

ACCIONES POSIBLES:
1. BUSCAR_ARCHIVOS - Encontrar documentos por nombre, tipo o patrón
2. LEER_DOCUMENTO - Extraer contenido de un archivo específico
3. CLASIFICAR_DOCUMENTO - Categorizar un documento por tema/tipo
4. ANALIZAR_DOCUMENTO - Obtener resumen, puntos clave, entidades
5. CREAR_DOCUMENTO - Generar nuevo documento con contenido
6. ORGANIZAR_ARCHIVOS - Mover/copiar/renombrar archivos
7. CONSOLIDAR - Unir múltiples documentos en uno
8. COMPARAR_DOCUMENTOS - Analizar similitudes/diferencias entre documentos
9. RESPONDER_PREGUNTA - Responder pregunta basada en documentos

Responde ÚNICAMENTE en JSON:
{{
    "action": "NOMBRE_ACCION",
    "parameters": {{
        "pattern": "...",  // si aplica
        "file_type": "...",  // si aplica
        "directory": "...",  // si aplica
        "question": "...",  // si aplica
        "content": "...",  // si aplica
    }},
    "requires_multiple_steps": true/false,
    "steps": ["paso1", "paso2"]  // si requiere múltiples acciones
}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="local-model",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Baja temperatura para consistencia
                max_tokens=400,
            )
            
            import json
            intent = json.loads(response.choices[0].message.content)
            intent['_used_llm'] = True
            return intent
        except Exception as e:
            print(f"Error analizando intención con LLM: {e}")
            return {
                "action": "ERROR",
                "parameters": {},
                "error": str(e),
                "_used_llm": True,
            }
    
    # Mantener alias para compatibilidad
    _analyze_intent = _analyze_intent_with_llm
    
    def _execute_action(self, intent: Dict[str, Any], 
                       original_instruction: str) -> Dict[str, Any]:
        """
        Ejecuta la acción determinada.
        
        Args:
            intent: Intención analizada
            original_instruction: Instrucción original
            
        Returns:
            Resultado de la ejecución
        """
        action = intent.get('action', '')
        params = intent.get('parameters', {})
        
        if action == 'BUSCAR_ARCHIVOS':
            return self._handle_search(params)
        
        elif action == 'LEER_DOCUMENTO':
            return self._handle_read(params)
        
        elif action == 'CLASIFICAR_DOCUMENTO':
            return self._handle_classify(params)
        
        elif action == 'ANALIZAR_DOCUMENTO':
            return self._handle_analyze(params)
        
        elif action == 'CREAR_DOCUMENTO':
            return self._handle_create(params, original_instruction)
        
        elif action == 'ORGANIZAR_ARCHIVOS':
            return self._handle_organize(params)
        
        elif action == 'CONSOLIDAR':
            return self._handle_consolidate(params)
        
        elif action == 'COMPARAR_DOCUMENTOS':
            return self._handle_compare(params)
        
        elif action == 'RESPONDER_PREGUNTA':
            return self._handle_question(original_instruction)
        
        else:
            return {
                "success": False,
                "error": f"Acción no reconocida: {action}",
            }
    
    def _handle_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja búsqueda de archivos."""
        pattern = params.get('pattern', '*')
        file_type = params.get('file_type')
        directory = params.get('directory', '.')
        
        # Actualizar directorio base si se especifica
        if directory != '.':
            self.file_finder.base_directory = Path(directory).resolve()
        
        if file_type:
            files = self.file_finder.find_by_type(file_type)
        else:
            files = self.file_finder.find_files(pattern)
        
        return {
            "success": True,
            "action": "search",
            "files_found": len(files),
            "files": [self.file_finder.to_dict(f) for f in files[:20]],  # Limitar a 20
            "statistics": self.file_finder.get_statistics(files),
        }
    
    def _handle_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja lectura de documentos."""
        file_path = params.get('file_path')
        
        if not file_path:
            return {"success": False, "error": "No se especificó ruta del archivo"}
        
        try:
            content = self.document_reader.read_document(file_path)
            return {
                "success": True,
                "action": "read",
                "content": content.content[:2000],  # Primeros 2000 chars
                "metadata": content.metadata,
                "full_content_available": True,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_classify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja clasificación de documentos."""
        file_path = params.get('file_path')
        
        if not file_path:
            return {"success": False, "error": "No se especificó ruta del archivo"}
        
        try:
            content = self.document_reader.read_document(file_path)
            classification = self.document_classifier.classify(
                content.content, 
                file_path
            )
            
            return {
                "success": True,
                "action": "classify",
                "classification": {
                    "category": classification.category,
                    "subcategory": classification.subcategory,
                    "file_type": classification.file_type,
                    "tags": classification.tags,
                    "language": classification.language,
                    "complexity": classification.complexity,
                    "confidence": classification.confidence,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja análisis de documentos."""
        file_path = params.get('file_path')
        analysis_type = params.get('type', 'complete')
        
        if not file_path:
            return {"success": False, "error": "No se especificó ruta del archivo"}
        
        try:
            content = self.document_reader.read_document(file_path)
            analysis = self.document_analyzer.analyze(
                content.content,
                file_path,
                analysis_type
            )
            
            return {
                "success": True,
                "action": "analyze",
                "summary": analysis.summary,
                "key_points": analysis.key_points,
                "entities": analysis.entities,
                "action_items": analysis.action_items,
                "metadata": analysis.metadata,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_create(self, params: Dict[str, Any], 
                      instruction: str) -> Dict[str, Any]:
        """Maneja creación de documentos."""
        # Usar LLM para generar contenido basado en la instrucción
        prompt = f"""Genera el contenido para un documento basado en esta solicitud:

SOLICITUD: "{instruction}"

Proporciona el contenido completo del documento, listo para guardar.
Si es un reporte, usa formato Markdown con títulos y secciones claras.
"""
        
        response = self.llm_client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        
        content = response.choices[0].message.content
        
        # Determinar nombre de archivo
        filename = params.get('filename', 'documento_generado.txt')
        directory = params.get('directory', '')
        
        file_path = self.document_manager.create_document(
            content=content,
            filename=filename,
            directory=directory,
        )
        
        return {
            "success": True,
            "action": "create",
            "file_path": file_path,
            "content_preview": content[:500],
        }
    
    def _handle_organize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja organización de archivos."""
        directory = params.get('directory', '.')
        operation = params.get('operation', 'by_type')
        
        if operation == 'by_type':
            result = self.document_manager.organize_by_type(directory)
            return {
                "success": True,
                "action": "organize",
                "organized": result,
            }
        
        return {"success": False, "error": "Operación no soportada"}
    
    def _handle_consolidate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja consolidación de documentos."""
        file_paths = params.get('file_paths', [])
        output_filename = params.get('output', 'consolidado.txt')
        
        if not file_paths:
            return {"success": False, "error": "No se especificaron archivos"}
        
        file_path = self.document_manager.consolidate_texts(
            file_paths=file_paths,
            output_filename=output_filename,
        )
        
        return {
            "success": True,
            "action": "consolidate",
            "file_path": file_path,
            "files_processed": len(file_paths),
        }
    
    def _handle_compare(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja comparación de documentos."""
        file1 = params.get('file1')
        file2 = params.get('file2')
        aspect = params.get('aspect', 'general')
        
        if not file1 or not file2:
            return {"success": False, "error": "Se necesitan dos archivos"}
        
        try:
            content1 = self.document_reader.read_document(file1)
            content2 = self.document_reader.read_document(file2)
            
            comparison = self.document_analyzer.compare_documents(
                content1.content,
                content2.content,
                aspect
            )
            
            return {
                "success": True,
                "action": "compare",
                "comparison": comparison,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_question(self, instruction: str) -> Dict[str, Any]:
        """Maneja preguntas sobre documentos."""
        # Primero buscar documentos relevantes
        files = self.file_finder.find_documents(recursive=True)
        
        if not files:
            return {
                "success": False,
                "error": "No se encontraron documentos para analizar",
            }
        
        # Leer primeros documentos (limitar para no exceder contexto)
        contents = []
        for file_info in files[:5]:  # Máximo 5 documentos
            try:
                content = self.document_reader.read_document(file_info.path)
                contents.append((content.content[:1500], file_info.path))
            except Exception:
                continue
        
        # Construir contexto
        context = "\n\n".join([f"[{path}]\n{content}" for content, path in contents])
        
        # Preguntar al LLM
        prompt = f"""Basándote en los siguientes documentos, responde la pregunta:

{context}

PREGUNTA: {instruction}

Responde de forma clara y cita las fuentes cuando sea posible.
"""
        
        response = self.llm_client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        
        return {
            "success": True,
            "action": "answer",
            "answer": response.choices[0].message.content,
            "sources": [path for _, path in contents],
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna estado del sistema con estadísticas de optimización."""
        cache_stats = self.intent_cache.get_stats() if self.intent_cache else {}
        
        return {
            "agents_initialized": [
                "FileFinderAgent",
                "DocumentReaderAgent",
                "DocumentClassifierAgent",
                "DocumentAnalyzerAgent",
                "DocumentManagerAgent",
            ],
            "base_directory": str(self.file_finder.base_directory),
            "actions_in_history": len(self.action_history),
            "llm_configured": self.llm_client is not None,
            "optimization_stats": {
                "total_requests": self.stats['total_requests'],
                "cache_hits": self.stats['cache_hits'],
                "pattern_matches": self.stats['pattern_matches'],
                "llm_calls": self.stats['llm_calls'],
                "cache_enabled": self.enable_cache,
                **cache_stats,
            },
            "llm_usage_rate": f"{(self.stats['llm_calls'] / max(self.stats['total_requests'], 1) * 100):.1f}%",
        }
    
    def reset_cache(self):
        """Reinicia la cache de intenciones."""
        if self.intent_cache:
            self.intent_cache = IntentCache(max_size=100)
            self.stats['cache_hits'] = 0
            self.stats['pattern_matches'] = 0
            self.stats['llm_calls'] = 0
    
    def warmup_cache(self, common_instructions: List[str]):
        """
        Precarga instrucciones comunes en la cache.
        
        Args:
            common_instructions: Lista de instrucciones frecuentes
        """
        print("Precargando cache con instrucciones comunes...")
        for instruction in common_instructions:
            # Procesar sin ejecutar para llenar cache
            normalized = self._normalize_instruction(instruction)
            intent = self._detect_pattern(instruction)
            if intent and self.intent_cache:
                self.intent_cache.put(normalized, intent)
        print(f"Cache precargada con {len(common_instructions)} patrones comunes")
