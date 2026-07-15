// RAG System - Aplicación JavaScript

const API_BASE = '';

// Elementos del DOM
const elements = {
    // Stats
    statDocuments: document.getElementById('stat-documents'),
    statModel: document.getElementById('stat-model'),
    statEmbeddings: document.getElementById('stat-embeddings'),
    statChunkSize: document.getElementById('stat-chunk-size'),
    refreshStatsBtn: document.getElementById('refresh-stats'),
    
    // Index Form
    indexForm: document.getElementById('index-form'),
    directoryInput: document.getElementById('directory'),
    fileTypesInput: document.getElementById('file-types'),
    clearExistingCheckbox: document.getElementById('clear-existing'),
    indexResult: document.getElementById('index-result'),
    
    // Query Form
    queryForm: document.getElementById('query-form'),
    questionInput: document.getElementById('question'),
    temperatureInput: document.getElementById('temperature'),
    tempValue: document.getElementById('temp-value'),
    maxTokensInput: document.getElementById('max-tokens'),
    includeSourcesCheckbox: document.getElementById('include-sources'),
    queryResult: document.getElementById('query-result'),
    
    // Response
    answerDisplay: document.getElementById('answer-display'),
    sourcesDisplay: document.getElementById('sources-display'),
    
    // Actions
    clearDbBtn: document.getElementById('clear-db')
};

// Actualizar valor del slider de temperatura
elements.temperatureInput.addEventListener('input', (e) => {
    elements.tempValue.textContent = e.target.value;
});

// Cargar estadísticas iniciales
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
});

// Event Listeners
elements.refreshStatsBtn.addEventListener('click', loadStats);
elements.indexForm.addEventListener('submit', handleIndex);
elements.queryForm.addEventListener('submit', handleQuery);
elements.clearDbBtn.addEventListener('click', clearDatabase);

// Funciones

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) throw new Error('Error al cargar estadísticas');
        
        const stats = await response.json();
        
        elements.statDocuments.textContent = stats.total_documents;
        elements.statModel.textContent = stats.model_path.split('/').pop() || 'Cargado';
        elements.statEmbeddings.textContent = stats.embedding_model;
        elements.statChunkSize.textContent = stats.chunk_size;
        
    } catch (error) {
        console.error('Error loading stats:', error);
        elements.statDocuments.textContent = 'Error';
        elements.statModel.textContent = '-';
        elements.statEmbeddings.textContent = '-';
        elements.statChunkSize.textContent = '-';
    }
}

async function handleIndex(e) {
    e.preventDefault();
    
    const directory = elements.directoryInput.value.trim();
    const fileTypes = elements.fileTypesInput.value.trim();
    const clearExisting = elements.clearExistingCheckbox.checked;
    
    if (!directory) {
        showResult(elements.indexResult, 'Por favor ingresa un directorio', 'error');
        return;
    }
    
    const payload = {
        directory: directory,
        clear_existing: clearExisting
    };
    
    if (fileTypes) {
        payload.file_types = fileTypes.split(',').map(t => t.trim());
    }
    
    showResult(elements.indexResult, '<span class="spinner"></span> Indexando documentos...', 'loading');
    disableButton(elements.indexForm.querySelector('button[type="submit"]'), true);
    
    try {
        const response = await fetch(`${API_BASE}/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showResult(
                elements.indexResult, 
                `✅ ${result.message}<br>Documentos: ${result.documents_loaded} | Chunks: ${result.chunks_created} | Total en DB: ${result.total_in_db}`,
                'success'
            );
            loadStats(); // Actualizar stats
        } else {
            showResult(elements.indexResult, `❌ Error: ${result.detail}`, 'error');
        }
        
    } catch (error) {
        showResult(elements.indexResult, `❌ Error de conexión: ${error.message}`, 'error');
    } finally {
        disableButton(elements.indexForm.querySelector('button[type="submit"]'), false);
    }
}

async function handleQuery(e) {
    e.preventDefault();
    
    const question = elements.questionInput.value.trim();
    const temperature = parseFloat(elements.temperatureInput.value);
    const maxTokens = parseInt(elements.maxTokensInput.value);
    const includeSources = elements.includeSourcesCheckbox.checked;
    
    if (!question) {
        showResult(elements.queryResult, 'Por favor ingresa una pregunta', 'error');
        return;
    }
    
    const payload = {
        question: question,
        temperature: temperature,
        max_tokens: maxTokens,
        include_sources: includeSources
    };
    
    // Mostrar estado de carga
    elements.answerDisplay.innerHTML = '<span class="spinner"></span> Procesando consulta...';
    elements.sourcesDisplay.innerHTML = '';
    showResult(elements.queryResult, '', 'loading');
    disableButton(elements.queryForm.querySelector('button[type="submit"]'), true);
    
    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Mostrar respuesta
            elements.answerDisplay.innerHTML = `<p>${formatAnswer(result.answer)}</p>`;
            
            // Mostrar fuentes si están disponibles
            if (includeSources && result.sources && result.sources.length > 0) {
                let sourcesHtml = '<h3>Fuentes:</h3>';
                result.sources.forEach((source, index) => {
                    const score = result.scores && result.scores[index] 
                        ? `(Score: ${result.scores[index].toFixed(4)})` 
                        : '';
                    sourcesHtml += `
                        <div class="source-item">
                            <div>${source}</div>
                            <div class="source-score">${score}</div>
                        </div>
                    `;
                });
                elements.sourcesDisplay.innerHTML = sourcesHtml;
            } else {
                elements.sourcesDisplay.innerHTML = '';
            }
            
            showResult(elements.queryResult, '✅ Consulta completada', 'success');
        } else {
            elements.answerDisplay.innerHTML = '<p class="placeholder">Error al obtener respuesta</p>';
            showResult(elements.queryResult, `❌ Error: ${result.detail}`, 'error');
        }
        
    } catch (error) {
        elements.answerDisplay.innerHTML = '<p class="placeholder">Error de conexión</p>';
        showResult(elements.queryResult, `❌ Error: ${error.message}`, 'error');
    } finally {
        disableButton(elements.queryForm.querySelector('button[type="submit"]'), false);
    }
}

async function clearDatabase() {
    if (!confirm('¿Estás seguro de que deseas limpiar toda la base de datos? Esta acción no se puede deshacer.')) {
        return;
    }
    
    disableButton(elements.clearDbBtn, true);
    
    try {
        const response = await fetch(`${API_BASE}/vector-db/clear`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('✅ Base de datos limpiada exitosamente');
            loadStats();
        } else {
            alert(`❌ Error: ${result.detail}`);
        }
        
    } catch (error) {
        alert(`❌ Error de conexión: ${error.message}`);
    } finally {
        disableButton(elements.clearDbBtn, false);
    }
}

// Utilidades

function showResult(element, message, type) {
    element.className = `result-message ${type}`;
    element.innerHTML = message;
}

function disableButton(button, disabled) {
    button.disabled = disabled;
    if (disabled) {
        button.style.opacity = '0.6';
        button.style.cursor = 'not-allowed';
    } else {
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
    }
}

function formatAnswer(text) {
    // Formato básico para saltos de línea
    return text.replace(/\n/g, '<br>');
}
