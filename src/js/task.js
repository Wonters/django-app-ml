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

// Fonction pour vérifier le statut d'une tâche d'upload
function pollUploadStatus(taskId, downloadLink, originalText) {
    const maxAttempts = 60; // 5 minutes max (60 * 5 secondes)
    let attempts = 0;
    
    // Extraire l'ID du dataset depuis l'URL originale
    const datasetIdMatch = downloadLink.href.match(/\/datasets\/(\d+)\/download/);
    const datasetId = datasetIdMatch ? datasetIdMatch[1] : '1';
    
    const checkStatus = () => {
        attempts++;
        
        // Utiliser l'URL de téléchargement avec le paramètre task_id
        const statusUrl = `/ml_app/api/datasets/${datasetId}/download/?task_id=${taskId}`;
        
        fetch(statusUrl, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie("csrftoken"),
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Upload status:', data);
            
            if (data.status === 'pending') {
                downloadLink.innerHTML = '<i class="fas fa-clock"></i> En attente...';
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 5000); // Vérifier toutes les 5 secondes
                } else {
                    alert('Timeout: La tâche d\'upload prend trop de temps');
                    downloadLink.innerHTML = originalText;
                    downloadLink.style.pointerEvents = 'auto';
                }
            } else if (data.status === 'running') {
                downloadLink.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Upload en cours...';
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 5000); // Vérifier toutes les 5 secondes
                } else {
                    alert('Timeout: La tâche d\'upload prend trop de temps');
                    downloadLink.innerHTML = originalText;
                    downloadLink.style.pointerEvents = 'auto';
                }
            } else if (data.status === 'completed') {
                downloadLink.innerHTML = '<i class="fas fa-check"></i> Terminé';
                setTimeout(() => {
                    alert('Dataset uploadé avec succès vers S3 !');
                    window.location.reload(); // Recharger la page pour mettre à jour l'état
                }, 1000);
            } else if (data.status === 'failed') {
                downloadLink.innerHTML = originalText;
                downloadLink.style.pointerEvents = 'auto';
                alert('Erreur lors de l\'upload: ' + (data.error || 'Erreur inconnue'));
            } else {
                downloadLink.innerHTML = originalText;
                downloadLink.style.pointerEvents = 'auto';
                alert('Statut inconnu: ' + data.status);
            }
        })
        .catch(error => {
            console.error('Erreur lors de la vérification du statut:', error);
            downloadLink.innerHTML = originalText;
            downloadLink.style.pointerEvents = 'auto';
            alert('Erreur lors de la vérification du statut de l\'upload');
        });
    };
    
    // Démarrer la vérification
    checkStatus();
}

// Fonction générique pour vérifier le statut d'une tâche
function pollTaskStatus(taskId, endpoint, element, originalText, taskName = "Tâche") {
    const maxAttempts = 60; // 5 minutes max (60 * 5 secondes)
    let attempts = 0;
    
    const checkStatus = () => {
        attempts++;
        
        fetch(`${endpoint}?task_id=${taskId}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie("csrftoken"),
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(`${taskName} status:`, data);
            
            if (data.status === 'pending') {
                if (element) {
                    element.innerHTML = '<i class="fas fa-clock"></i> En attente...';
                }
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 5000);
                } else {
                    alert(`Timeout: La ${taskName.toLowerCase()} prend trop de temps`);
                    if (element && originalText) {
                        element.innerHTML = originalText;
                        element.style.pointerEvents = 'auto';
                    }
                }
            } else if (data.status === 'running') {
                if (element) {
                    element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> En cours...';
                }
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 5000);
                } else {
                    alert(`Timeout: La ${taskName.toLowerCase()} prend trop de temps`);
                    if (element && originalText) {
                        element.innerHTML = originalText;
                        element.style.pointerEvents = 'auto';
                    }
                }
            } else if (data.status === 'completed') {
                if (element) {
                    element.innerHTML = '<i class="fas fa-check"></i> Terminé';
                }
                setTimeout(() => {
                    alert(`${taskName} terminée avec succès !`);
                    window.location.reload();
                }, 1000);
            } else if (data.status === 'failed') {
                if (element && originalText) {
                    element.innerHTML = originalText;
                    element.style.pointerEvents = 'auto';
                }
                alert(`Erreur lors de la ${taskName.toLowerCase()}: ` + (data.error || 'Erreur inconnue'));
            } else {
                if (element && originalText) {
                    element.innerHTML = originalText;
                    element.style.pointerEvents = 'auto';
                }
                alert('Statut inconnu: ' + data.status);
            }
        })
        .catch(error => {
            console.error(`Erreur lors de la vérification du statut de la ${taskName.toLowerCase()}:`, error);
            if (element && originalText) {
                element.innerHTML = originalText;
                element.style.pointerEvents = 'auto';
            }
            alert(`Erreur lors de la vérification du statut de la ${taskName.toLowerCase()}`);
        });
    };
    
    // Démarrer la vérification
    checkStatus();
}

// Fonction pour lancer une tâche et gérer le polling
function launchTaskAndPoll(taskEndpoint, taskData, element, originalText, taskName = "Tâche") {
    // Changer l'état de l'élément pour indiquer le lancement
    if (element) {
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Lancement...';
        element.style.pointerEvents = 'none';
    }
    
    fetch(taskEndpoint, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie("csrftoken"),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'pending' && data.task_id) {
            // Tâche lancée, commencer le polling
            alert(`${taskName} lancée ! Vérification du statut...`);
            pollTaskStatus(data.task_id, taskEndpoint, element, originalText, taskName);
        } else if (data.error) {
            // Erreur lors du lancement
            alert(`Erreur lors du lancement de la ${taskName.toLowerCase()}: ` + data.error);
            if (element && originalText) {
                element.innerHTML = originalText;
                element.style.pointerEvents = 'auto';
            }
        } else {
            // Autre cas
            alert(`Réponse inattendue: ${JSON.stringify(data)}`);
            if (element && originalText) {
                element.innerHTML = originalText;
                element.style.pointerEvents = 'auto';
            }
        }
    })
    .catch(error => {
        console.error(`Erreur lors du lancement de la ${taskName.toLowerCase()}:`, error);
        alert(`Erreur lors du lancement de la ${taskName.toLowerCase()}`);
        if (element && originalText) {
            element.innerHTML = originalText;
            element.style.pointerEvents = 'auto';
        }
    });
}

export {
    getCookie,
    pollUploadStatus,
    pollTaskStatus,
    launchTaskAndPoll
}; 