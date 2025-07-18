/**
 * JavaScript pour la page de détail du modèle
 * Gère les interactions et fonctionnalités de la page de détail d'un modèle d'IA
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Model detail page loaded');
    
    // Initialisation des tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Animation des cartes de métriques
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Gestion des boutons d'action
    setupActionButtons();
    
    // Initialisation des graphiques (placeholder)
    initializeCharts();
});

/**
 * Configure les boutons d'action de la page
 */
function setupActionButtons() {
    // Bouton d'export du modèle
    const exportBtn = document.querySelector('button[onclick="exportModel()"]');
    if (exportBtn) {
        exportBtn.addEventListener('click', function(e) {
            e.preventDefault();
            exportModel();
        });
    }

    // Bouton d'historique
    const historyBtn = document.querySelector('button[onclick="showModelHistory()"]');
    if (historyBtn) {
        historyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showModelHistory();
        });
    }
}

/**
 * Fonction d'export du modèle
 */
function exportModel() {
    // Récupérer l'ID du modèle depuis l'URL ou les données de la page
    const modelId = getModelIdFromPage();
    
    if (!modelId) {
        showAlert('Erreur: Impossible de récupérer l\'ID du modèle', 'danger');
        return;
    }

    // Afficher un indicateur de chargement
    showLoadingIndicator('Export en cours...');

    // Simulation d'une requête d'export (à remplacer par une vraie API)
    setTimeout(() => {
        hideLoadingIndicator();
        
        // Créer un lien de téléchargement simulé
        const link = document.createElement('a');
        link.href = '#';
        link.download = `model_${modelId}.zip`;
        link.textContent = 'Télécharger le modèle';
        
        // Afficher une notification de succès
        showAlert('Modèle exporté avec succès!', 'success');
        
        // Dans une vraie implémentation, vous feriez un appel API ici
        console.log(`Exporting model ${modelId}`);
    }, 2000);
}

/**
 * Fonction d'affichage de l'historique du modèle
 */
function showModelHistory() {
    const modelId = getModelIdFromPage();
    
    if (!modelId) {
        showAlert('Erreur: Impossible de récupérer l\'ID du modèle', 'danger');
        return;
    }

    // Créer une modal pour afficher l'historique
    const modalHtml = `
        <div class="modal fade" id="modelHistoryModal" tabindex="-1" aria-labelledby="modelHistoryModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="modelHistoryModalLabel">
                            <i class="fas fa-history"></i> Historique du modèle
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center py-4">
                            <i class="fas fa-clock fa-3x text-muted mb-3"></i>
                            <h6 class="text-muted">Historique en cours de développement</h6>
                            <p class="text-muted">
                                Cette fonctionnalité affichera l'historique des entraînements, 
                                des modifications et des performances du modèle.
                            </p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Ajouter la modal au DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Afficher la modal
    const modal = new bootstrap.Modal(document.getElementById('modelHistoryModal'));
    modal.show();
    
    // Nettoyer la modal après fermeture
    document.getElementById('modelHistoryModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

/**
 * Initialise les graphiques de la page (placeholder)
 */
function initializeCharts() {
    // Placeholder pour les graphiques
    // Dans une vraie implémentation, vous utiliseriez Chart.js, D3.js, ou une autre librairie
    console.log('Charts initialization placeholder');
    
    // Exemple avec Chart.js (si disponible)
    if (typeof Chart !== 'undefined') {
        // Code pour initialiser les graphiques
        console.log('Chart.js is available');
    }
}

/**
 * Récupère l'ID du modèle depuis la page
 */
function getModelIdFromPage() {
    // Essayer de récupérer depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const modelId = urlParams.get('model_id');
    
    if (modelId) {
        return modelId;
    }
    
    // Essayer de récupérer depuis les données de la page
    const modelDataElement = document.querySelector('[data-model-id]');
    if (modelDataElement) {
        return modelDataElement.dataset.modelId;
    }
    
    // Essayer de récupérer depuis l'URL path
    const pathParts = window.location.pathname.split('/');
    const modelIndex = pathParts.indexOf('model');
    if (modelIndex !== -1 && pathParts[modelIndex + 1]) {
        return pathParts[modelIndex + 1];
    }
    
    return null;
}

/**
 * Affiche une alerte
 */
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Ajouter l'alerte en haut de la page
    const container = document.querySelector('.container');
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto-supprimer après 5 secondes
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Affiche un indicateur de chargement
 */
function showLoadingIndicator(message = 'Chargement...') {
    const loadingHtml = `
        <div id="loadingIndicator" class="position-fixed top-50 start-50 translate-middle">
            <div class="d-flex align-items-center">
                <div class="spinner-border text-primary me-3" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
                <span class="text-primary">${message}</span>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

/**
 * Cache l'indicateur de chargement
 */
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Fonctions globales pour les onclick
window.exportModel = exportModel;
window.showModelHistory = showModelHistory; 