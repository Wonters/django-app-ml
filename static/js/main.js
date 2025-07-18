import $ from 'jquery';
import * as bootstrap from 'bootstrap';

// Make jQuery and bootstrap available globally
window.$ = $;
window.jQuery = $;
window.bootstrap = bootstrap;

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

// Fonction pour obtenir le cookie CSRF
function getCookie(name) {
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
                            alert("Dataset deleted successfully");
                            window.location.reload();
                        } else {
                            alert("Failed to delete dataset");
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
}

export {
    initializeDatasetList,
    handleDatasetDeletion
};
