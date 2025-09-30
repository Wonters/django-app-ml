/**
 * Dataset Analysis - Audit Module
 * Gestion de l'audit de dataset
 */

import { 
    pollAnalysisStatus, 
    launchAnalysisTask, 
    checkExistingAnalysisStatus,
    formatErrorMessage,
    addCollapsibleErrorDetails,
    formatBytes,
    formatNumber
} from './tasks.js';
import { addTabIndicator } from './main.js';

// Configuration pour l'audit
const AUDIT_CONFIG = {
    launchBtn: 'launch-audit-btn',
    relaunchBtn: 'relaunch-audit-btn',
    retryBtn: 'retry-audit-btn',
    statusDiv: 'audit-status',
    loadingDiv: 'audit-loading',
    errorDiv: 'audit-error',
    resultsDiv: 'audit-results',
    contentDiv: 'analysis-content',
    errorMessageDiv: 'audit-error-message',
    tabId: 'data-analysis-tab'
};

/**
 * Initialize audit analysis
 */
export function initializeAnalysis() {
    const launchButton = document.getElementById(AUDIT_CONFIG.launchBtn);
    const relaunchButton = document.getElementById(AUDIT_CONFIG.relaunchBtn);
    const retryButton = document.getElementById(AUDIT_CONFIG.retryBtn);
    
    if (launchButton) {
        // Check existing status on page load for audit
        checkExistingAnalysisStatus(
            launchButton.getAttribute('data-url'),
            (results) => {
                // Analysis has already been completed, show results
                showAnalysisResults(results);
                showRelaunchButton();
            },
            (errorMessage, errorDetails, taskInfo) => {
                // Previous analysis failed, show error but allow retry
                showAnalysisError(errorMessage, errorDetails, taskInfo);
                showLaunchButton();
            },
            () => {
                // No analysis has been performed yet, show initial state
                hideAllAnalysisSections();
                document.getElementById(AUDIT_CONFIG.contentDiv).classList.remove('d-none');
                showLaunchButton();
            }
        ).then(taskId => {
            if (taskId) {
                // Analysis is currently running, start polling
                pollAnalysisStatus('audit', AUDIT_CONFIG, launchButton.getAttribute('data-dataset-id'), taskId,
                    (results) => {
                        showAnalysisResults(results);
                        showRelaunchButton();
                    },
                    (errorMessage, errorDetails, taskInfo) => {
                        showAnalysisError(errorMessage, errorDetails, taskInfo);
                        showLaunchButton();
                    }
                );
            }
        });
        
        launchButton.addEventListener('click', function(e) {
            e.preventDefault();
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
 * Launch audit analysis
 */
function launchAnalysis() {
    const launchButton = document.getElementById(AUDIT_CONFIG.launchBtn);
    
    if (!launchButton) {
        console.error('Launch button not found for audit analysis');
        showAnalysisError('Bouton de lancement non trouvé pour l\'analyse d\'audit', null, null);
        return;
    }
    
    const datasetId = launchButton.getAttribute('data-dataset-id');
    const analysisUrl = launchButton.getAttribute('data-url');
    
    // Validate required attributes
    if (!datasetId || !analysisUrl) {
        console.error('Missing required attributes for audit analysis:', { datasetId, analysisUrl });
        showAnalysisError('Attributs manquants pour l\'analyse d\'audit', null, null);
        return;
    }
    
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
            pollAnalysisStatus('audit', AUDIT_CONFIG, datasetId, taskId,
                (results) => {
                    showAnalysisResults(results);
                    showRelaunchButton();
                },
                (errorMessage, errorDetails, taskInfo) => {
                    showAnalysisError(errorMessage, errorDetails, taskInfo);
                    showLaunchButton();
                }
            );
        },
        (errorMessage, errorDetails) => {
            showAnalysisError(errorMessage, errorDetails, null);
            showLaunchButton();
        }
    );
}

/**
 * Show analysis status
 */
function showAnalysisStatus(statusType) {
    hideAllAnalysisSections();
    
    const statusDiv = document.getElementById(AUDIT_CONFIG.statusDiv);
    const loadingDiv = document.getElementById(AUDIT_CONFIG.loadingDiv);
    const errorDiv = document.getElementById(AUDIT_CONFIG.errorDiv);
    
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
    const errorMessageElement = document.getElementById(AUDIT_CONFIG.errorMessageDiv);
    
    console.group('Erreur d\'analyse audit');
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
    
    const resultsDiv = document.getElementById(AUDIT_CONFIG.resultsDiv);
    resultsDiv.classList.remove('d-none');
    
    showAuditResults(results);
    
    // Add visual indicator on the tab
    addTabIndicator(AUDIT_CONFIG.tabId, 'success');
}

/**
 * Show launch button
 */
function showLaunchButton() {
    const launchButton = document.getElementById(AUDIT_CONFIG.launchBtn);
    const relaunchButton = document.getElementById(AUDIT_CONFIG.relaunchBtn);
    
    if (launchButton) {
        launchButton.classList.remove('d-none');
        launchButton.disabled = false;
        launchButton.innerHTML = `<i class="fas fa-play"></i> Lancer l'analyse`;
    }
    
    if (relaunchButton) {
        relaunchButton.classList.add('d-none');
    }
}

/**
 * Show relaunch button
 */
function showRelaunchButton() {
    const launchButton = document.getElementById(AUDIT_CONFIG.launchBtn);
    const relaunchButton = document.getElementById(AUDIT_CONFIG.relaunchBtn);
    
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
    const contentDiv = document.getElementById(AUDIT_CONFIG.contentDiv);
    const statusDiv = document.getElementById(AUDIT_CONFIG.statusDiv);
    const resultsDiv = document.getElementById(AUDIT_CONFIG.resultsDiv);
    const loadingDiv = document.getElementById(AUDIT_CONFIG.loadingDiv);
    const errorDiv = document.getElementById(AUDIT_CONFIG.errorDiv);
    
    if (contentDiv) contentDiv.classList.add('d-none');
    if (statusDiv) statusDiv.classList.add('d-none');
    if (resultsDiv) resultsDiv.classList.add('d-none');
    if (loadingDiv) loadingDiv.classList.add('d-none');
    if (errorDiv) errorDiv.classList.add('d-none');
}

/**
 * Show audit results
 */
function showAuditResults(results) {
    const resultsDiv = document.getElementById('audit-results');
    results = results.results;
    
    if (!results) {
        console.warn('Aucun résultat reçu pour l\'audit');
        showAnalysisError('Aucun résultat disponible pour l\'audit', null, null);
        return;
    }
    
    console.group('Résultats d\'audit de dataset');
    console.log('Résultats reçus:', results);
    console.groupEnd();
    
    if (results.error === true || results.exception || (results.warning && !results.basic_info)) {
        showAnalysisError(results.error || results.exception || results.warning || 'Erreur dans les résultats d\'audit', results, null);
        return;
    }
    
    createAuditAccordion(results);
}

/**
 * Create audit accordion
 */
function createAuditAccordion(results) {
    const resultsDiv = document.getElementById('audit-results');
    let accordionHtml = `
        <div class="row">
            <div class="col-12">
                <h6 class="text-success mb-3">
                    <i class="fas fa-check-circle"></i> Analyse terminée avec succès
                </h6>
            </div>
        </div>
        <div class="accordion" id="auditAccordion">
    `;
    
    let accordionItemCount = 0;
    
    if (results.basic_info) {
        accordionItemCount++;
        accordionHtml += createAccordionItem('basic-info', accordionItemCount, 'Informations de base', 'fas fa-info-circle', 'basic-info-content');
    }
    
    if (results.missing_values) {
        accordionItemCount++;
        accordionHtml += createAccordionItem('missing-values', accordionItemCount, 'Valeurs manquantes', 'fas fa-exclamation-triangle', 'missing-values-content');
    }
    
    if (results.descriptive_stats) {
        accordionItemCount++;
        accordionHtml += createAccordionItem('descriptive-stats', accordionItemCount, 'Statistiques descriptives', 'fas fa-chart-bar', 'descriptive-stats-content');
    }
    
    if (results.categorical_stats) {
        accordionItemCount++;
        accordionHtml += createAccordionItem('categorical-stats', accordionItemCount, 'Statistiques catégorielles', 'fas fa-list', 'categorical-stats-content');
    }
    
    if (accordionItemCount === 0) {
        accordionHtml += `
            <div class="alert alert-info">
                <h5>Audit terminé</h5>
                <p>L'audit s'est terminé avec succès mais aucun résultat détaillé n'est disponible.</p>
                <pre class="mt-2" style="font-size: 0.9em; background: #f8f9fa; padding: 10px; border-radius: 4px;">${JSON.stringify(results, null, 2)}</pre>
            </div>
        `;
    }
    
    accordionHtml += '</div>';
    resultsDiv.innerHTML = accordionHtml;
    
    if (results.basic_info) fillBasicInfoContent(results.basic_info);
    if (results.missing_values) fillMissingValuesContent(results.missing_values);
    if (results.descriptive_stats) fillDescriptiveStatsContent(results.descriptive_stats);
    if (results.categorical_stats) fillCategoricalStatsContent(results.categorical_stats);
}

/**
 * Create accordion item
 */
function createAccordionItem(id, count, title, icon, contentId) {
    const isFirst = count === 1;
    return `
        <div class="accordion-item">
            <h2 class="accordion-header" id="heading-${id}">
                <button class="accordion-button ${isFirst ? '' : 'collapsed'}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${id}" aria-expanded="${isFirst}" aria-controls="collapse-${id}">
                    <i class="${icon} me-2"></i> ${title}
                </button>
            </h2>
            <div id="collapse-${id}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}" aria-labelledby="heading-${id}" data-bs-parent="#auditAccordion">
                <div class="accordion-body" id="${contentId}">
                    <div class="text-center">
                        <div class="spinner-border spinner-border-sm" role="status">
                            <span class="visually-hidden">Chargement...</span>
                        </div>
                        Chargement...
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Fill basic info content
 */
function fillBasicInfoContent(basicInfo) {
    const contentDiv = document.getElementById('basic-info-content');
    contentDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <dl class="row">
                    <dt class="col-sm-6">Nombre de lignes:</dt>
                    <dd class="col-sm-6">${basicInfo.row_count?.toLocaleString() || '-'}</dd>
                    
                    <dt class="col-sm-6">Nombre de colonnes:</dt>
                    <dd class="col-sm-6">${basicInfo.column_count?.toLocaleString() || '-'}</dd>
                </dl>
            </div>
            <div class="col-md-6">
                <dl class="row">
                    <dt class="col-sm-6">Utilisation mémoire:</dt>
                    <dd class="col-sm-6">${formatBytes(basicInfo.memory_usage) || '-'}</dd>
                </dl>
            </div>
        </div>
    `;
}

/**
 * Fill missing values content
 */
function fillMissingValuesContent(missingValues) {
    const contentDiv = document.getElementById('missing-values-content');
    let tableRows = '';
    
    Object.entries(missingValues).forEach(([column, count]) => {
        tableRows += `
            <tr>
                <td>${column}</td>
                <td>${count.toLocaleString()}</td>
            </tr>
        `;
    });
    
    contentDiv.innerHTML = `
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Colonne</th>
                        <th>Valeurs manquantes</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Fill descriptive stats content
 */
function fillDescriptiveStatsContent(descriptiveStats) {
    const contentDiv = document.getElementById('descriptive-stats-content');
    let tableRows = '';
    
    Object.entries(descriptiveStats).forEach(([column, stats]) => {
        tableRows += `
            <tr>
                <td>${column}</td>
                <td>${formatNumber(stats.mean)}</td>
                <td>${formatNumber(stats.std)}</td>
                <td>${formatNumber(stats.min)}</td>
                <td>${formatNumber(stats.max)}</td>
                <td>${formatNumber(stats.median)}</td>
            </tr>
        `;
    });
    
    contentDiv.innerHTML = `
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Colonne</th>
                        <th>Moyenne</th>
                        <th>Écart-type</th>
                        <th>Min</th>
                        <th>Max</th>
                        <th>Médiane</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Fill categorical stats content
 */
function fillCategoricalStatsContent(categoricalStats) {
    const contentDiv = document.getElementById('categorical-stats-content');
    let cardsHtml = '';
    
    Object.entries(categoricalStats).forEach(([column, stats]) => {
        let tableRows = '';
        Object.entries(stats.top_values).forEach(([value, count]) => {
            tableRows += `<tr><td>${value}</td><td>${count.toLocaleString()}</td></tr>`;
        });
        
        cardsHtml += `
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0">${column}</h6>
                </div>
                <div class="card-body">
                    <p><strong>Valeurs uniques:</strong> ${stats.unique_count.toLocaleString()}</p>
                    <h6>Top 10 des valeurs:</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Valeur</th>
                                    <th>Comptage</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tableRows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    });
    
    contentDiv.innerHTML = cardsHtml;
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