import $ from 'jquery';
import * as bootstrap from 'bootstrap';
import { getCookie, pollUploadStatus } from './task.js';

// Make jQuery and bootstrap available globally
window.$ = $;
window.jQuery = $;
window.bootstrap = bootstrap;

// Fonction utilitaire pour afficher des toasts Bootstrap
function showToast(message, type = 'info', duration = 5000) {
    // Créer l'élément toast
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Créer le conteneur de toasts s'il n'existe pas
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Ajouter le toast au conteneur
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Récupérer l'élément toast et l'initialiser
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });
    
    // Afficher le toast
    toast.show();
    
    // Supprimer l'élément du DOM après la fermeture
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Import DataTables core first and wait for it to be ready
import('datatables.net').then(() => {
    console.log("DataTables core loaded");
    
    // Import DataTables plugins in correct order
    return Promise.all([
        import('datatables.net-bs5'),
        import('datatables.net-responsive'),
        import('datatables.net-responsive-bs5')
    ]);
}).then(() => {
    console.log("DataTables plugins loaded");
    
    // Import DataTables Buttons core only (without Bootstrap 5 styling)
    return import('datatables.net-buttons');
}).then(() => {
    console.log("DataTables Buttons core loaded");
    
    // Import required libraries for export functionality
    return Promise.all([
        import('jszip'),
        import('file-saver')
    ]);
}).then(([jszip, fileSaver]) => {
    console.log("Export libraries loaded");
    window.saveAs = fileSaver.saveAs;
    
    // Initialize the dataset list after everything is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDatasetList);
    } else {
        initializeDatasetList();
    }
}).catch(error => {
    console.error("Error loading DataTables modules:", error);
});

// Fonction pour gérer la suppression de dataset
function handleDatasetDeletion() {
    const deleteModal = document.getElementById('deleteDatasetModal');
    if (!deleteModal) return;

    // Ajouter un gestionnaire d'événement pour le clic sur les boutons delete
    document.addEventListener('click', function (event) {
        if (event.target.closest('.btn-danger[data-bs-target="#deleteDatasetModal"]')) {
            const button = event.target.closest('.btn-danger[data-bs-target="#deleteDatasetModal"]');
            const datasetId = button.dataset.datasetId;
            const datasetName = button.dataset.datasetName;
            const datasetApiUrl = button.dataset.datasetApiUrl;

            // Mettre à jour le contenu de la modal
            const nameSpan = document.getElementById('datasetNameToDelete');
            if (nameSpan) {
                nameSpan.textContent = datasetName;
            }

            const deleteButton = document.getElementById('deleteDatasetModalButton');
            if (deleteButton) {
                deleteButton.onclick = function () {
                    fetch(datasetApiUrl, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': getCookie("csrftoken")
                        }
                    }).then(response => {
                        if (response.ok) {
                            if (typeof bootstrap !== 'undefined') {
                                const modal = bootstrap.Modal.getInstance(deleteModal);
                                if (modal) modal.hide();
                            }
                            showToast("Dataset deleted successfully", "success");
                            window.location.reload();
                        } else {
                            showToast("Failed to delete dataset", "danger");
                        }
                    });
                };
            }

            // Ouvrir la modal manuellement si Bootstrap est disponible
            if (typeof bootstrap !== 'undefined') {
                const modal = new bootstrap.Modal(deleteModal);
                modal.show();
            } else {
                // Fallback: afficher la modal avec display block
                deleteModal.style.display = 'block';
                deleteModal.classList.add('show');
                document.body.classList.add('modal-open');
            }
        }
    });
}

// Fonction pour gérer le téléchargement de dataset
function handleDatasetDownload() {
    document.addEventListener('click', function (event) {
        // Vérifier si le clic est sur un lien de téléchargement de dataset
        const downloadLink = event.target.closest('a[href*="/api/datasets/"][href*="/download/"]');
        if (downloadLink) {
            event.preventDefault(); // Empêcher la navigation directe
            
            const url = downloadLink.href;
            const originalText = downloadLink.innerHTML;
            
            // Changer le texte du bouton pour indiquer le chargement
            downloadLink.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Téléchargement...';
            downloadLink.style.pointerEvents = 'none'; // Désactiver le clic
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCookie("csrftoken"),
                    'Accept': 'application/json, application/zip'
                }
            })
            .then(response => {
                // Check if response is a file download (ZIP) or JSON
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/zip')) {
                    // It's a ZIP file download
                    return response.blob().then(blob => {
                        // Create download link
                        const downloadUrl = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = downloadUrl;
                        
                        // Get filename from Content-Disposition header
                        const contentDisposition = response.headers.get('content-disposition');
                        let filename = 'dataset.zip';
                        if (contentDisposition) {
                            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                            if (filenameMatch) {
                                filename = filenameMatch[1];
                            }
                        }
                        
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(downloadUrl);
                        
                        showToast('Dataset téléchargé avec succès en local !', 'success');
                        return { success: true };
                    });
                } else {
                    // It's a JSON response (S3 upload task)
                    return response.json();
                }
            })
            .then(data => {
                if (data && data.status === 'pending' && data.task_id) {
                    // Task launched, start polling for status
                    showToast('Tâche d\'upload lancée ! Vérification du statut...', 'info');
                    pollUploadStatus(data.task_id, downloadLink, originalText);
                } else if (data && data.status === 'success') {
                    showToast('Dataset téléchargé et uploadé avec succès vers S3 !', 'success');
                    window.location.reload(); // Recharger la page pour mettre à jour l'état
                } else if (data && data.status === 'already_exists') {
                    showToast('Dataset déjà présent dans le bucket S3.', 'warning');
                    window.location.reload(); // Recharger la page pour mettre à jour l'état
                } else if (data && data.success) {
                    // ZIP download was successful, already handled above
                    return;
                } else if (data && data.error) {
                    showToast('Erreur: ' + data.error, 'danger');
                } else {
                    showToast('Erreur inconnue lors du téléchargement', 'danger');
                }
                
                // Restaurer le bouton seulement si ce n'est pas une tâche en cours
                if (!data || !data.task_id) {
                    downloadLink.innerHTML = originalText;
                    downloadLink.style.pointerEvents = 'auto';
                }
            })
            .catch(error => {
                console.error('Erreur lors du téléchargement:', error);
                showToast('Erreur lors du téléchargement du dataset', 'danger');
                // Restaurer le bouton en cas d'erreur
                downloadLink.innerHTML = originalText;
                downloadLink.style.pointerEvents = 'auto';
            });
        }
    });
}

// Fonction pour gérer la sélection de bucket
function handleBucketSelection() {
    const selectBucketModal = document.getElementById('selectBucketModal');
    if (!selectBucketModal) return;

    // Gestionnaire pour l'ouverture de la modal
    selectBucketModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const datasetId = button.getAttribute('data-dataset-id');
        const datasetName = button.getAttribute('data-dataset-name');
        
        // Mettre à jour le nom du dataset dans la modal
        const datasetNameSpan = document.getElementById('datasetNameForBucket');
        if (datasetNameSpan) {
            datasetNameSpan.textContent = datasetName;
        }
        
        // Stocker l'ID du dataset pour l'utiliser lors de la sélection
        selectBucketModal.setAttribute('data-dataset-id', datasetId);
    });

    // Gestionnaire pour la sélection d'un bucket (délégué d'événement)
    document.addEventListener('click', function (event) {
        const selectButton = event.target.closest('.select-bucket-btn');
        if (selectButton && selectBucketModal.classList.contains('show')) {
            const bucketId = selectButton.getAttribute('data-bucket-id');
            const bucketName = selectButton.getAttribute('data-bucket-name');
            const datasetId = selectBucketModal.getAttribute('data-dataset-id');
            
            // Désactiver tous les boutons pendant la mise à jour
            const bucketList = document.getElementById('bucketList');
            const allButtons = bucketList.querySelectorAll('.select-bucket-btn');
            allButtons.forEach(btn => {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mise à jour...';
            });
            
            // Appel API pour mettre à jour le bucket du dataset
            fetch(`/ml_app/api/datasets/${datasetId}/`, {
                method: 'PATCH',
                headers: {
                    'X-CSRFToken': getCookie("csrftoken"),
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    bucket_id: bucketId
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur lors de la mise à jour');
                }
                return response.json();
            })
            .then(data => {
                // Le ModelViewSet retourne directement les données du dataset mis à jour
                if (data && data.bucket) {
                    // Fermer la modal
                    if (typeof bootstrap !== 'undefined') {
                        const modal = bootstrap.Modal.getInstance(selectBucketModal);
                        if (modal) modal.hide();
                    }
                    
                    // Afficher un message de succès
                    showToast(`Bucket ${bucketName} assigné avec succès au dataset !`, 'success');
                    
                    // Recharger la page
                    window.location.reload();
                } else {
                    throw new Error('Erreur lors de la mise à jour du bucket');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la mise à jour du bucket:', error);
                showToast('Erreur lors de la mise à jour du bucket: ' + error.message, 'danger');
                
                // Réactiver les boutons
                allButtons.forEach(btn => {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-check"></i> Sélectionner';
                });
            });
        }
    });
}

// Fonction d'initialisation principale
function initializeDatasetList() {
    console.log("Initializing dataset list...");

    // Vérifier si Bootstrap est chargé
    if (typeof bootstrap !== 'undefined') {
        console.log("Bootstrap is loaded");
    } else {
        console.error("Bootstrap is not loaded!");
    }

    // Vérifier si jQuery est disponible
    if (typeof $ === 'undefined') {
        console.error("jQuery is not loaded!");
        return;
    }

    // Vérifier si DataTable est disponible
    if (typeof $.fn.DataTable === 'undefined') {
        console.error("DataTable is not loaded!");
        return;
    }

    // Vérifier si DataTables Buttons est disponible
    if (typeof $.fn.dataTable.Buttons === 'undefined') {
        console.error("DataTables Buttons plugin is not loaded!");
        return;
    }

    // Vérifier si l'élément table existe
    const tableElement = document.getElementById('datasetsTable');
    if (!tableElement) {
        console.error("Table element 'datasetsTable' not found!");
        return;
    }

    try {
        // Initialiser DataTable avec les boutons d'export
        const dataTable = $(tableElement).DataTable({
            responsive: false,
            pageLength: 10,
            dom: '<"row"<"col-sm-12"B>>' +
                 '<"row"<"col-sm-12"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-12"<"d-flex justify-content-center align-items-center gap-3"ip>>>',
            pagingType: 'full_numbers',
            buttons: [
                {
                    text: 'Excel',
                    className: 'btn btn-success btn-sm me-1',
                    action: function () {
                        // Export simple vers CSV (qui peut être ouvert dans Excel)
                        const table = $(tableElement);
                        const headers = [];
                        const rows = [];
                        
                        // Récupérer les en-têtes
                        table.find('thead th').each(function() {
                            headers.push($(this).text().trim());
                        });
                        
                        // Récupérer les données
                        table.find('tbody tr').each(function() {
                            const row = [];
                            $(this).find('td').each(function() {
                                let text = $(this).text().trim();
                                text = text.replace(/"/g, '""');
                                row.push('"' + text + '"');
                            });
                            rows.push(row.join(','));
                        });
                        
                        // Créer le contenu CSV
                        const csvContent = [headers.join(','), ...rows].join('\n');
                        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                        if (window.saveAs) {
                            window.saveAs(blob, 'datasets.csv');
                        }
                    }
                },
                {
                    text: 'CSV',
                    className: 'btn btn-info btn-sm me-1',
                    action: function () {
                        // Export CSV
                        const table = $(tableElement);
                        const headers = [];
                        const rows = [];
                        
                        table.find('thead th').each(function() {
                            headers.push($(this).text().trim());
                        });
                        
                        table.find('tbody tr').each(function() {
                            const row = [];
                            $(this).find('td').each(function() {
                                let text = $(this).text().trim();
                                text = text.replace(/"/g, '""');
                                row.push('"' + text + '"');
                            });
                            rows.push(row.join(','));
                        });
                        
                        const csvContent = [headers.join(','), ...rows].join('\n');
                        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                        if (window.saveAs) {
                            window.saveAs(blob, 'datasets.csv');
                        }
                    }
                },
                {
                    text: 'Imprimer',
                    className: 'btn btn-secondary btn-sm',
                    action: function () {
                        window.print();
                    }
                }
            ],
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/fr-FR.json'
            }
        });

        // Apply Bootstrap classes to pagination and search after initialization
        setTimeout(() => {
            const paginationContainer = $(tableElement).closest('.dataTables_wrapper').find('.dataTables_paginate');
            const researchContainer = $(tableElement).closest('.dataTables_wrapper').find('.dataTables_filter');
            
            if (paginationContainer.length) {
                paginationContainer.find('a').addClass('page-link');
                paginationContainer.find('li').addClass('page-item');
                paginationContainer.find('li.current').addClass('active');
            }
            
            if (researchContainer.length) {
                researchContainer.find('input').addClass('form-control');
                researchContainer.find('button').addClass('btn btn-outline-secondary');
            }
        }, 100);

        console.log("DataTable initialized successfully");
    } catch (error) {
        console.error("Error initializing DataTable:", error);
        return;
    }

    // Initialiser la gestion des suppressions
    handleDatasetDeletion();

    // Initialiser la gestion des téléchargements
    handleDatasetDownload();

    // Initialiser la gestion de la sélection de bucket
    handleBucketSelection();

    // Initialiser les tooltips Bootstrap
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        console.log("Bootstrap tooltips initialized");
    }
}

export {
    initializeDatasetList,
    handleDatasetDeletion,
    handleDatasetDownload,
    handleBucketSelection,
    showToast
};
