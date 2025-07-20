/**
 * Dataset Analysis - IA Analysis Module
 * Gestion de l'analyse IA de dataset
 */

import { 
    pollAnalysisStatus, 
    launchAnalysisTask, 
    checkExistingAnalysisStatus,
    formatErrorMessage,
    addCollapsibleErrorDetails
} from './tasks.js';
import { addTabIndicator, switchToIAAnalysisTab } from './main.js';

// Configuration pour l'analyse IA
const IA_CONFIG = {
    launchBtn: null, // No main button for IA
    relaunchBtn: 'relaunch-ia-analysis-btn',
    retryBtn: 'retry-ia-analysis-btn',
    statusDiv: 'ia-analysis-status',
    loadingDiv: 'ia-analysis-loading',
    errorDiv: 'ia-analysis-error',
    resultsDiv: 'ia-analysis-results',
    contentDiv: 'handle-ia-analyse',
    errorMessageDiv: 'ia-analysis-error-message',
    tabId: 'ia-analysis-tab',
    tabLaunchBtn: 'launch-ia-analysis-tab-btn'
};

/**
 * Initialize IA analysis
 */
export function initializeIAAnalysis() {
    const relaunchButton = document.getElementById(IA_CONFIG.relaunchBtn);
    const retryButton = document.getElementById(IA_CONFIG.retryBtn);
    const tabLaunchButton = document.getElementById(IA_CONFIG.tabLaunchBtn);
    
    if (tabLaunchButton) {
        // Check existing status on page load for IA analysis
        checkExistingAnalysisStatus(
            tabLaunchButton.getAttribute('data-url'),
            (results) => {
                // Analysis has already been completed, show results
                showAnalysisResults(results);
                showIAAnalysisTabButton();
            },
            (errorMessage, errorDetails, taskInfo) => {
                // Previous analysis failed, show error but allow retry
                showAnalysisError(errorMessage, errorDetails, taskInfo);
                showIAAnalysisTabButton();
            },
            () => {
                // No analysis has been performed yet, show initial state
                hideAllAnalysisSections();
                document.getElementById(IA_CONFIG.contentDiv).classList.remove('d-none');
                showIAAnalysisTabButton();
            }
        ).then(taskId => {
            if (taskId) {
                // Analysis is currently running, start polling
                pollAnalysisStatus('ia', IA_CONFIG, tabLaunchButton.getAttribute('data-dataset-id'), taskId,
                    (results) => {
                        showAnalysisResults(results);
                        showIAAnalysisTabButton();
                    },
                    (errorMessage, errorDetails, taskInfo) => {
                        showAnalysisError(errorMessage, errorDetails, taskInfo);
                        showIAAnalysisTabButton();
                    }
                );
            }
        });
        
        tabLaunchButton.addEventListener('click', function(e) {
            e.preventDefault();
            // Switch to IA analysis tab first
            switchToIAAnalysisTab();
            launchAnalysis();
        });
    }
    
    if (relaunchButton) {
        relaunchButton.addEventListener('click', function(e) {
            e.preventDefault();
            launchAnalysis();
        });
    }
    
    if (retryButton) {
        retryButton.addEventListener('click', function(e) {
            e.preventDefault();
            launchAnalysis();
        });
    }
}

/**
 * Launch IA analysis
 */
function launchAnalysis() {
    // Get the appropriate button based on type and context
    const launchButton = document.getElementById(IA_CONFIG.tabLaunchBtn);
    
    // Check if button exists
    if (!launchButton) {
        console.error('Launch button not found for IA analysis:', IA_CONFIG.tabLaunchBtn);
        showAnalysisError('Bouton de lancement non trouvé pour l\'analyse IA', null, null);
        return;
    }
    
    const datasetId = launchButton.getAttribute('data-dataset-id');
    const analysisUrl = launchButton.getAttribute('data-url');
    
    // Validate required attributes
    if (!datasetId || !analysisUrl) {
        console.error('Missing required attributes for IA analysis:', { datasetId, analysisUrl });
        showAnalysisError('Attributs manquants pour l\'analyse IA', null, null);
        return;
    }
    
    // Ensure the IA tab is visible
    switchToIAAnalysisTab();
    
    // Disable button and show loading state
    launchButton.disabled = true;
    const originalContent = launchButton.innerHTML;
    launchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Lancement...';
    
    // Hide previous results and show status
    hideAllAnalysisSections();
    showAnalysisStatus('loading');
    
    // Launch analysis task
    launchAnalysisTask(analysisUrl,
        (taskId) => {
            // Task launched successfully, start polling
            pollAnalysisStatus('ia', IA_CONFIG, datasetId, taskId,
                (results) => {
                    showAnalysisResults(results);
                    showIAAnalysisTabButton();
                },
                (errorMessage, errorDetails, taskInfo) => {
                    showAnalysisError(errorMessage, errorDetails, taskInfo);
                    showIAAnalysisTabButton();
                }
            );
            hideIAAnalysisTabButton();
        },
        (errorMessage, errorDetails) => {
            showAnalysisError(errorMessage, errorDetails, null);
            showIAAnalysisTabButton();
            resetIAAnalysisTabButton(launchButton, originalContent);
        }
    );
}

/**
 * Show analysis status
 */
function showAnalysisStatus(statusType) {
    hideAllAnalysisSections();
    
    const statusDiv = document.getElementById(IA_CONFIG.statusDiv);
    const loadingDiv = document.getElementById(IA_CONFIG.loadingDiv);
    const errorDiv = document.getElementById(IA_CONFIG.errorDiv);
    
    if (statusDiv) {
        statusDiv.classList.remove('d-none');
    }
    
    if (statusType === 'loading') {
        if (loadingDiv) loadingDiv.classList.remove('d-none');
        if (errorDiv) errorDiv.classList.add('d-none');
    } else if (statusType === 'error') {
        if (loadingDiv) loadingDiv.classList.add('d-none');
        if (errorDiv) errorDiv.classList.remove('d-none');
    }
}

/**
 * Show analysis error
 */
function showAnalysisError(message, errorDetails = null, taskInfo = null) {
    showAnalysisStatus('error');
    const errorMessageElement = document.getElementById(IA_CONFIG.errorMessageDiv);
    
    console.group('Erreur d\'analyse IA');
    console.error('Message:', message);
    if (errorDetails) console.error('Détails:', errorDetails);
    if (taskInfo) console.error('Informations de tâche:', taskInfo);
    console.groupEnd();
    
    let fullErrorMessage = message;
    
    if (errorDetails) {
        if (typeof errorDetails === 'string') {
            fullErrorMessage += '\n\nDétails: ' + errorDetails;
        } else if (typeof errorDetails === 'object') {
            fullErrorMessage += '\n\nDétails de l\'erreur:';
            
            if (errorDetails.error) fullErrorMessage += '\nErreur: ' + errorDetails.error;
            if (errorDetails.detail) fullErrorMessage += '\nDétail: ' + errorDetails.detail;
            if (errorDetails.message) fullErrorMessage += '\nMessage: ' + errorDetails.message;
            if (errorDetails.exception) fullErrorMessage += '\nException: ' + errorDetails.exception;
            if (errorDetails.warning) fullErrorMessage += '\nAvertissement: ' + errorDetails.warning;
            if (errorDetails.code) fullErrorMessage += '\nCode d\'erreur: ' + errorDetails.code;
            if (errorDetails.status_code) fullErrorMessage += '\nCode de statut HTTP: ' + errorDetails.status_code;
            if (errorDetails.exception_type) fullErrorMessage += '\nType d\'exception: ' + errorDetails.exception_type;
            if (errorDetails.exception_message) fullErrorMessage += '\nMessage d\'exception: ' + errorDetails.exception_message;
            if (errorDetails.traceback) fullErrorMessage += '\n\nStack trace:\n' + errorDetails.traceback;
        }
    }
    
    if (taskInfo) {
        fullErrorMessage += '\n\nInformations de la tâche:';
        if (taskInfo.task_id) fullErrorMessage += '\nID de la tâche: ' + taskInfo.task_id;
        if (taskInfo.status) fullErrorMessage += '\nStatut: ' + taskInfo.status;
        if (taskInfo.message) fullErrorMessage += '\nMessage: ' + taskInfo.message;
        if (taskInfo.start_time) fullErrorMessage += '\nHeure de début: ' + new Date(taskInfo.start_time).toLocaleString();
        if (taskInfo.end_time) fullErrorMessage += '\nHeure de fin: ' + new Date(taskInfo.end_time).toLocaleString();
        if (taskInfo.duration) fullErrorMessage += '\nDurée: ' + formatDuration(taskInfo.duration);
    }
    
    errorMessageElement.innerHTML = formatErrorMessage(fullErrorMessage);
    
    if (fullErrorMessage.length > 200) {
        addCollapsibleErrorDetails(errorMessageElement, fullErrorMessage);
    }
}

/**
 * Show analysis results
 */
function showAnalysisResults(results) {
    hideAllAnalysisSections();
    
    const resultsDiv = document.getElementById(IA_CONFIG.resultsDiv);
    resultsDiv.classList.remove('d-none');
    
    showIAAnalysisResults(results);
    
    // Add visual indicator on the tab
    addTabIndicator(IA_CONFIG.tabId, 'success');
}

/**
 * Show launch button
 */
function showLaunchButton() {
    const launchButton = document.getElementById(IA_CONFIG.tabLaunchBtn);
    const relaunchButton = document.getElementById(IA_CONFIG.relaunchBtn);
    
    if (launchButton) {
        launchButton.classList.remove('d-none');
        launchButton.disabled = false;
        launchButton.innerHTML = `<i class="fas fa-brain"></i> Lancer l'analyse IA`;
    }
    
    if (relaunchButton) {
        relaunchButton.classList.add('d-none');
    }
}

/**
 * Show relaunch button
 */
function showRelaunchButton() {
    const launchButton = document.getElementById(IA_CONFIG.tabLaunchBtn);
    const relaunchButton = document.getElementById(IA_CONFIG.relaunchBtn);
    
    if (launchButton) {
        launchButton.classList.add('d-none');
    }
    
    if (relaunchButton) {
        relaunchButton.classList.remove('d-none');
    }
}

/**
 * Hide all analysis sections
 */
function hideAllAnalysisSections() {
    const contentDiv = document.getElementById(IA_CONFIG.contentDiv);
    const statusDiv = document.getElementById(IA_CONFIG.statusDiv);
    const resultsDiv = document.getElementById(IA_CONFIG.resultsDiv);
    const loadingDiv = document.getElementById(IA_CONFIG.loadingDiv);
    const errorDiv = document.getElementById(IA_CONFIG.errorDiv);
    
    if (contentDiv) contentDiv.classList.add('d-none');
    if (statusDiv) statusDiv.classList.add('d-none');
    if (resultsDiv) resultsDiv.classList.add('d-none');
    if (loadingDiv) loadingDiv.classList.add('d-none');
    if (errorDiv) errorDiv.classList.add('d-none');
}

/**
 * Show IA analysis results
 */
function showIAAnalysisResults(results) { 
    const iaAnalysisResults = document.getElementById('ia-analysis-results');
    iaAnalysisResults.innerHTML = '';
    
    const resultsContent = document.createElement('div');
    resultsContent.className = 'ia-analysis-results';
    
    if (results && results.results) {
        const aiAnalysis = results.results;
        
        // Message de succès
        let htmlContent = `
            <div class="alert alert-success" role="alert">
                <i class="fas fa-check-circle"></i> ${aiAnalysis.message || 'Analyse IA terminée avec succès'}
            </div>
        `;
        
        // Traitement automatique des données par clé-valeur
        if (Array.isArray(aiAnalysis)) {
            // Si c'est une liste de dictionnaires
            aiAnalysis.forEach((item, index) => {
                htmlContent += generateDynamicCard(item, `Résultat ${index + 1}`, index);
            });
        } else if (typeof aiAnalysis === 'object') {
            // Si c'est un objet avec des propriétés
            Object.entries(aiAnalysis).forEach(([key, value], index) => {
                // Ignorer les propriétés déjà traitées
                if (key !== 'message') {
                    htmlContent += generateDynamicCard(value, formatKeyName(key), index);
                }
            });
        }
        
        resultsContent.innerHTML = htmlContent;
    } else {
        resultsContent.innerHTML = `
            <div class="alert alert-info" role="alert">
                <i class="fas fa-info-circle"></i> Analyse IA terminée. Aucun résultat détaillé disponible.
            </div>
        `;
    }
    
    iaAnalysisResults.appendChild(resultsContent);
    iaAnalysisResults.classList.remove('d-none');
}

/**
 * Generate dynamic card based on data type
 */
function generateDynamicCard(data, title, index) {
    const cardId = `ia-card-${index}`;
    let cardContent = '';
    
    if (Array.isArray(data)) {
        // Traitement des listes
        if (data.length === 0) {
            cardContent = '<p class="text-muted">Aucune donnée disponible.</p>';
        } else if (typeof data[0] === 'string') {
            // Liste de chaînes
            cardContent = data.map(item => 
                `<p class="mb-2"><i class="fas fa-arrow-right text-primary"></i> ${escapeHtml(item)}</p>`
            ).join('');
        } else if (typeof data[0] === 'object') {
            // Liste d'objets - récursion pour chaque objet
            cardContent = data.map((item, itemIndex) => {
                if (typeof item === 'object' && item !== null) {
                    return generateDynamicCard(item, `Élément ${itemIndex + 1}`, `${index}-${itemIndex}`);
                } else {
                    return `<p class="mb-2"><i class="fas fa-arrow-right text-primary"></i> ${escapeHtml(String(item))}</p>`;
                }
            }).join('');
        } else {
            // Autres types de listes
            cardContent = data.map(item => 
                `<p class="mb-2"><i class="fas fa-arrow-right text-primary"></i> ${escapeHtml(String(item))}</p>`
            ).join('');
        }
    } else if (typeof data === 'object' && data !== null) {
        // Traitement des objets - récursion pour chaque propriété
        const objectEntries = Object.entries(data);
        if (objectEntries.length === 0) {
            cardContent = '<p class="text-muted">Objet vide.</p>';
        } else {
            cardContent = objectEntries.map(([key, value], keyIndex) => {
                const subTitle = formatKeyName(key);
                const subIndex = `${index}-${keyIndex}`;
                
                if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                    // Récursion pour les objets imbriqués
                    return generateDynamicCard(value, subTitle, subIndex);
                } else if (Array.isArray(value)) {
                    // Traitement des listes
                    if (value.length === 0) {
                        return `<div class="mb-3">
                            <h6 class="text-primary">${escapeHtml(subTitle)}</h6>
                            <p class="text-muted ms-3">Aucune donnée</p>
                        </div>`;
                    } else if (typeof value[0] === 'object' && value[0] !== null) {
                        // Liste d'objets - récursion pour chaque élément
                        return `<div class="mb-3">
                            <h6 class="text-primary">${escapeHtml(subTitle)}</h6>
                            <div class="ms-3">
                                ${value.map((item, itemIndex) => 
                                    generateDynamicCard(item, `Élément ${itemIndex + 1}`, `${subIndex}-${itemIndex}`)
                                ).join('')}
                            </div>
                        </div>`;
                    } else {
                        // Liste de valeurs simples
                        return `<div class="mb-3">
                            <h6 class="text-primary">${escapeHtml(subTitle)}</h6>
                            ${value.map(item => 
                                `<p class="mb-1 ms-3"><i class="fas fa-arrow-right text-secondary"></i> ${escapeHtml(String(item))}</p>`
                            ).join('')}
                        </div>`;
                    }
                } else {
                    // Valeur simple
                    return `<div class="mb-2">
                        <strong>${escapeHtml(subTitle)}:</strong> 
                        <span class="ms-2">${escapeHtml(String(value))}</span>
                    </div>`;
                }
            }).join('');
        }
    } else {
        // Traitement des valeurs simples
        cardContent = `<p class="mb-2">${escapeHtml(String(data))}</p>`;
    }
    
    return `
        <div class="row mt-3">
            <div class="col-12">
                <div class="card" id="${cardId}">
                    <div class="card-header">
                        <h6 class="card-title mb-0">
                            <i class="fas fa-chart-bar"></i> ${escapeHtml(title)}
                        </h6>
                    </div>
                    <div class="card-body">
                        ${cardContent}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Format key name for display
 */
function formatKeyName(key) {
    // Conversion des clés en format lisible
    const keyMappings = {
        'insights': 'Insights IA',
        'recommendations': 'Recommandations',
        'analysis': 'Analyse',
        'summary': 'Résumé',
        'details': 'Détails',
        'metrics': 'Métriques',
        'statistics': 'Statistiques',
        'findings': 'Découvertes',
        'observations': 'Observations',
        'suggestions': 'Suggestions',
        'warnings': 'Avertissements',
        'errors': 'Erreurs',
        'data_quality': 'Qualité des données',
        'data_issues': 'Problèmes de données',
        'patterns': 'Motifs',
        'trends': 'Tendances',
        'anomalies': 'Anomalies',
        'correlations': 'Corrélations'
    };
    
    // Remplacer les underscores par des espaces et capitaliser
    let formatted = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    // Utiliser le mapping si disponible
    return keyMappings[key.toLowerCase()] || formatted;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Hide IA analysis tab button
 */
function hideIAAnalysisTabButton() {
    const launchButton = document.getElementById(IA_CONFIG.tabLaunchBtn);
    const relaunchButton = document.getElementById(IA_CONFIG.relaunchBtn);
    
    if (launchButton) launchButton.classList.add('d-none');
    if (relaunchButton) relaunchButton.classList.remove('d-none');
}

/**
 * Show IA analysis tab button
 */
function showIAAnalysisTabButton() {
    const launchButton = document.getElementById(IA_CONFIG.tabLaunchBtn);
    const relaunchButton = document.getElementById(IA_CONFIG.relaunchBtn);
    
    if (launchButton) launchButton.classList.remove('d-none');
    if (relaunchButton) relaunchButton.classList.add('d-none');
}

/**
 * Reset IA analysis tab button
 */
function resetIAAnalysisTabButton(button, originalContent) {
    button.innerHTML = originalContent;
    button.disabled = false;
}

/**
 * Format duration helper function
 */
function formatDuration(seconds) {
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