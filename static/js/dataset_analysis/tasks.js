/**
 * Dataset Analysis - Tasks Module
 * Gestion des tâches et fonctions utilitaires
 */

/**
 * Handle standardized API responses
 * @param {Object} data - Response data with standardized format
 * @param {string} data.status - Response status
 * @param {string} data.message - Response message
 * @param {string} data.task_id - Task identifier
 * @param {string} data.error - Error message (if applicable)
 * @param {Object} data.result - Result data (if applicable)
 * @returns {Object} - Processed response object
 */
export function handleStandardizedResponse(data) {
    const response = {
        status: data.status,
        message: data.message,
        task_id: data.task_id,
        error: data.error,
        result: data.result,
        isValid: true
    };
    
    // Validation de base
    if (!data.status) {
        response.isValid = false;
        response.error = 'Format de réponse invalide: statut manquant';
    }
    
    // Validation selon le statut
    switch (data.status) {
        case 'pending':
        case 'running':
            if (!data.task_id) {
                response.isValid = false;
                response.error = 'ID de tâche manquant pour le statut: ' + data.status;
            }
            break;
        case 'completed':
            if (!data.task_id && !data.result) {
                response.isValid = false;
                response.error = 'ID de tâche manquant pour le statut: ' + data.status;
            }
            break;
        case 'failed':
            if (!data.error && !data.message) {
                response.isValid = false;
                response.error = 'Message d\'erreur manquant pour le statut: failed';
            }
            break;
        case 'unknown':
            if (!data.message) {
                response.isValid = false;
                response.error = 'Message manquant pour le statut: unknown';
            }
            break;
        default:
            response.isValid = false;
            response.error = 'Statut inconnu: ' + data.status;
    }
    
    return response;
}

/**
 * Initialize bucket connection testing
 */
export function initializeBucketConnectionTesting() {
    const testButtons = document.querySelectorAll('.test-connection-btn');
    
    testButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Prevent multiple simultaneous tests
            if (this.getAttribute('data-testing') === 'true') {
                return;
            }
            
            const bucketId = this.getAttribute('data-bucket-id');
            testBucketConnection(this, bucketId);
        });
    });
}

/**
 * Test bucket connection
 */
function testBucketConnection(button, bucketId) {
    // Set testing state
    button.setAttribute('data-testing', 'true');
    button.disabled = true;
    
    // Store original content
    const originalContent = button.innerHTML;
    
    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Test en cours...';
    button.classList.remove('btn-outline-primary', 'btn-success', 'btn-danger');
    button.classList.add('btn-outline-secondary');
    
    // Get the URL from the hidden input
    const urlInput = document.getElementById(`test-connection-url-${bucketId}`);
    if (!urlInput) {
        console.error('URL input not found for bucket:', bucketId);
        return;
    }
    
    const testUrl = urlInput.value;
    
    // Make API call
    fetch(testUrl, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Success state
            button.innerHTML = '<i class="fas fa-check-circle"></i> Connexion réussie';
            button.classList.remove('btn-outline-secondary', 'btn-danger');
            button.classList.add('btn-success');
        } else {
            // Error state
            button.innerHTML = '<i class="fas fa-times-circle"></i> Échec';
            button.classList.remove('btn-outline-secondary', 'btn-success');
            button.classList.add('btn-danger');
        }
        
        // Reset after 3 seconds
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.classList.remove('btn-success', 'btn-danger', 'btn-outline-secondary');
            button.classList.add('btn-outline-primary');
            button.disabled = false;
            button.setAttribute('data-testing', 'false');
        }, 3000);
    })
    .catch(error => {
        console.error('Error testing bucket connection:', error);
        
        // Error state
        button.innerHTML = '<i class="fas fa-times-circle"></i> Erreur';
        button.classList.remove('btn-outline-secondary', 'btn-success');
        button.classList.add('btn-danger');
        
        // Reset after 3 seconds
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.classList.remove('btn-success', 'btn-danger', 'btn-outline-secondary');
            button.classList.add('btn-outline-primary');
            button.disabled = false;
            button.setAttribute('data-testing', 'false');
        }, 3000);
    });
}

/**
 * Poll analysis status
 */
export function pollAnalysisStatus(type, config, datasetId, taskId, onComplete, onError) {
    // Get the appropriate button based on type and context
    let launchButton;
    if (type === 'ia') {
        // For IA analysis, use the tab button since there's no main button
        launchButton = document.getElementById(config.tabLaunchBtn);
    } else {
        launchButton = document.getElementById(config.launchBtn);
    }
    
    // Check if button exists
    if (!launchButton) {
        console.error(`Launch button not found for ${type} analysis polling:`, config.tabLaunchBtn || config.launchBtn);
        onError(`Bouton de lancement non trouvé pour le polling de l'analyse ${type}`, null, null);
        return;
    }
    
    const analysisUrl = launchButton.getAttribute('data-url');
    const statusUrl = `${analysisUrl}?task_id=${taskId}`;
    
    const pollInterval = setInterval(() => {
        fetch(statusUrl, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            const response = handleStandardizedResponse(data);
            
            if (response.isValid) {
                if (response.status === 'completed') {
                    clearInterval(pollInterval);
                    onComplete(response.result);
                } else if (response.status === 'failed') {
                    clearInterval(pollInterval);
                    let errorMessage = response.error || response.message || `L'analyse a échoué`;
                    let errorDetails = null;
                    
                    if (response.result) {
                        errorDetails = response.result;
                        if (response.result.error) {
                            errorMessage = response.result.error;
                        } else if (response.result.detail) {
                            errorMessage = response.result.detail;
                        } else if (response.result.message) {
                            errorMessage = response.result.message;
                        }
                    }
                    
                    onError(errorMessage, errorDetails, {
                        task_id: response.task_id,
                        status: response.status,
                        message: response.message
                    });
                } else if (response.status === 'running' || response.status === 'pending') {
                    // Task is running, continue polling
                    console.log(`${type} analysis is running...`);
                } else if (response.status === 'unknown') {
                    clearInterval(pollInterval);
                    onError(response.message || 'Statut de tâche inconnu', null, {
                        task_id: response.task_id,
                        status: response.status
                    });
                } else {
                    clearInterval(pollInterval);
                    onError(`Statut de tâche inattendu: ${response.status}`, null, {
                        task_id: response.task_id,
                        status: response.status
                    });
                }
            } else {
                clearInterval(pollInterval);
                onError(response.error || `Statut de tâche inattendu: ${response.status}`, null, {
                    task_id: response.task_id,
                    status: response.status
                });
            }
        })
        .catch(error => {
            console.error(`Error polling ${type} analysis status:`, error);
            clearInterval(pollInterval);
            onError('Erreur lors de la vérification du statut', null, null);
        });
    }, 2000);
}

/**
 * Launch analysis task
 */
export function launchAnalysisTask(analysisUrl, onSuccess, onError) {
    return fetch(analysisUrl, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
    })
    .then(response => response.json())
    .then(data => {
        const response = handleStandardizedResponse(data);
        
        if (response.isValid) {
            if (response.status === 'pending' && response.task_id) {
                onSuccess(response.task_id);
            } else if (response.status === 'failed') {
                throw new Error(response.error || response.message || `Erreur lors du lancement de l'analyse`);
            } else {
                throw new Error('Format de réponse inattendu lors du lancement de l\'analyse');
            }
        } else {
            throw new Error(response.error || 'Format de réponse invalide lors du lancement de l\'analyse');
        }
    })
    .catch(error => {
        console.error('Error launching analysis task:', error);
        let errorMessage = error.message;
        let errorDetails = null;
        
        if (error.response) {
            try {
                const errorData = error.response.json();
                if (errorData.error) {
                    errorMessage = errorData.error;
                } else if (errorData.message) {
                    errorMessage = errorData.message;
                }
                if (errorData.result && errorData.result.error) {
                    errorDetails = errorData.result;
                    errorMessage = errorData.result.detail || errorData.result.error || errorMessage;
                }
            } catch (e) {
                errorMessage = error.response.text || errorMessage;
            }
        }
        
        onError(errorMessage, errorDetails);
    });
}

/**
 * Check existing analysis status
 */
export function checkExistingAnalysisStatus(analysisUrl, onComplete, onError, onUnknown) {
    return fetch(analysisUrl, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        const response = handleStandardizedResponse(data);
        console.log('Analysis status response:', response);
        
        if (response.isValid) {
            if (response.status === 'completed') {
                onComplete(response.result);
            } else if (response.status === 'unknown') {
                onUnknown();
            } else if (response.status === 'running' || response.status === 'pending') {
                if (response.task_id) {
                    return response.task_id; // Return task_id for polling
                } else {
                    onError(`Statut d'analyse incohérent: tâche en cours sans ID`, null, {
                        status: response.status,
                        message: response.message
                    });
                }
            } else if (response.status === 'failed') {
                onError(response.error || response.message || `Analyse précédente échouée`, null, {
                    status: response.status,
                    message: response.message
                });
            } else {
                onError(`Statut d'analyse inattendu: ${response.status}`, null, {
                    status: response.status,
                    message: response.message
                });
            }
        } else {
            onError(response.error || 'Format de réponse invalide lors de la vérification', null, {
                status: response.status,
                message: response.message
            });
        }
    })
    .catch(error => {
        console.error('Error checking existing analysis status:', error);
        onUnknown();
    });
}

/**
 * Get CSRF token from cookies
 */
export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Format error message
 */
export function formatErrorMessage(message) {
    return message.replace(/\n/g, '<br>');
}

/**
 * Add collapsible error details
 */
export function addCollapsibleErrorDetails(errorElement, fullMessage) {
    const shortMessage = fullMessage.substring(0, 200) + '...';
    const fullMessageHtml = formatErrorMessage(fullMessage);
    
    errorElement.innerHTML = `
        <div class="error-summary">${formatErrorMessage(shortMessage)}</div>
        <button class="btn btn-sm btn-outline-secondary mt-2" onclick="toggleErrorDetails(this)">
            <i class="fas fa-chevron-down"></i> Afficher les détails complets
        </button>
        <div class="error-details mt-2" style="display: none;">
            <div class="alert alert-danger">
                <pre class="mb-0" style="white-space: pre-wrap; font-size: 0.9em;">${fullMessage}</pre>
            </div>
        </div>
    `;
}

/**
 * Toggle error details
 */
export function toggleErrorDetails(button) {
    const detailsDiv = button.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (detailsDiv.style.display === 'none') {
        detailsDiv.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        button.innerHTML = '<i class="fas fa-chevron-up"></i> Masquer les détails';
    } else {
        detailsDiv.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        button.innerHTML = '<i class="fas fa-chevron-down"></i> Afficher les détails complets';
    }
}

/**
 * Format duration
 */
export function formatDuration(seconds) {
    if (seconds < 60) {
        return seconds + ' secondes';
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return minutes + 'm ' + remainingSeconds + 's';
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return hours + 'h ' + minutes + 'm';
    }
}

/**
 * Format bytes
 */
export function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format number
 */
export function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    if (typeof num === 'number') {
        return num.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
    return num;
} 