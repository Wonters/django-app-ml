/**
 * Dataset Analysis JavaScript
 * Handles bucket connection testing and dataset audit functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize bucket connection testing
    initializeBucketConnectionTesting();
    
    // Initialize dataset audit functionality
    initializeDatasetAudit();
});

function initializeBucketConnectionTesting() {
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

function initializeDatasetAudit() {
    const launchButton = document.getElementById('launch-audit-btn');
    const retryButton = document.getElementById('retry-audit-btn');
    
    if (launchButton) {
        launchButton.addEventListener('click', function(e) {
            e.preventDefault();
            launchDatasetAudit();
        });
    }
    
    if (retryButton) {
        retryButton.addEventListener('click', function(e) {
            e.preventDefault();
            launchDatasetAudit();
        });
    }
}

function launchDatasetAudit() {
    const launchButton = document.getElementById('launch-audit-btn');
    const datasetId = launchButton.getAttribute('data-dataset-id');
    const auditUrl = launchButton.getAttribute('data-audit-url');
    
    // Disable button and show loading state
    launchButton.disabled = true;
    launchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Lancement...';
    
    // Hide previous results and show status
    hideAllAuditSections();
    showAuditStatus('loading');
    
    // Launch audit task
    fetch(auditUrl, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message_id) {
            // Task launched successfully, start polling
            pollAuditStatus(datasetId, data.message_id);
        } else {
            throw new Error(data.error || 'Erreur lors du lancement de l\'audit');
        }
    })
    .catch(error => {
        console.error('Error launching audit:', error);
        showAuditError(error.message);
        resetLaunchButton();
    });
}

function pollAuditStatus(datasetId, taskId) {
    const auditUrl = document.getElementById('launch-audit-btn').getAttribute('data-audit-url');
    const statusUrl = `${auditUrl}?task_id=${taskId}`;
    
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
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                showAuditResults(data.result);
                resetLaunchButton();
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                showAuditError(data.error || 'L\'audit a échoué');
                resetLaunchButton();
            } else if (data.status === 'error') {
                clearInterval(pollInterval);
                showAuditError(data.error || 'Erreur lors de la récupération des résultats');
                resetLaunchButton();
            }
            // If status is 'running', continue polling
        })
        .catch(error => {
            console.error('Error polling audit status:', error);
            clearInterval(pollInterval);
            showAuditError('Erreur lors de la vérification du statut');
            resetLaunchButton();
        });
    }, 2000); // Poll every 2 seconds
}

function showAuditStatus(type) {
    hideAllAuditSections();
    
    const statusDiv = document.getElementById('audit-status');
    const loadingDiv = document.getElementById('audit-loading');
    const errorDiv = document.getElementById('audit-error');
    
    statusDiv.classList.remove('d-none');
    
    if (type === 'loading') {
        loadingDiv.classList.remove('d-none');
        errorDiv.classList.add('d-none');
    } else if (type === 'error') {
        loadingDiv.classList.add('d-none');
        errorDiv.classList.remove('d-none');
    }
}

function showAuditError(message) {
    showAuditStatus('error');
    document.getElementById('audit-error-message').textContent = message;
}

function showAuditResults(results) {
    hideAllAuditSections();
    
    const resultsDiv = document.getElementById('audit-results');
    resultsDiv.classList.remove('d-none');
    
    // Display basic info
    if (results.basic_info) {
        displayBasicInfo(results.basic_info);
    }
    
    // Display missing values
    if (results.missing_values) {
        displayMissingValues(results.missing_values);
    }
    
    // Display descriptive stats
    if (results.descriptive_stats) {
        displayDescriptiveStats(results.descriptive_stats);
    }
    
    // Display categorical stats
    if (results.categorical_stats) {
        displayCategoricalStats(results.categorical_stats);
    }
}

function displayBasicInfo(basicInfo) {
    const section = document.getElementById('basic-info-section');
    section.classList.remove('d-none');
    
    document.getElementById('row-count').textContent = basicInfo.row_count?.toLocaleString() || '-';
    document.getElementById('column-count').textContent = basicInfo.column_count?.toLocaleString() || '-';
    document.getElementById('memory-usage').textContent = formatBytes(basicInfo.memory_usage) || '-';
}

function displayMissingValues(missingValues) {
    const section = document.getElementById('missing-values-section');
    const tableBody = document.getElementById('missing-values-table');
    
    section.classList.remove('d-none');
    tableBody.innerHTML = '';
    
    Object.entries(missingValues).forEach(([column, count]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${column}</td>
            <td>${count.toLocaleString()}</td>
        `;
        tableBody.appendChild(row);
    });
}

function displayDescriptiveStats(descriptiveStats) {
    const section = document.getElementById('descriptive-stats-section');
    const tableBody = document.getElementById('descriptive-stats-table');
    
    section.classList.remove('d-none');
    tableBody.innerHTML = '';
    
    Object.entries(descriptiveStats).forEach(([column, stats]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${column}</td>
            <td>${formatNumber(stats.mean)}</td>
            <td>${formatNumber(stats.std)}</td>
            <td>${formatNumber(stats.min)}</td>
            <td>${formatNumber(stats.max)}</td>
            <td>${formatNumber(stats.median)}</td>
        `;
        tableBody.appendChild(row);
    });
}

function displayCategoricalStats(categoricalStats) {
    const section = document.getElementById('categorical-stats-section');
    const content = document.getElementById('categorical-stats-content');
    
    section.classList.remove('d-none');
    content.innerHTML = '';
    
    Object.entries(categoricalStats).forEach(([column, stats]) => {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
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
                            ${Object.entries(stats.top_values).map(([value, count]) => 
                                `<tr><td>${value}</td><td>${count.toLocaleString()}</td></tr>`
                            ).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        content.appendChild(card);
    });
}

function hideAllAuditSections() {
    document.getElementById('analysis-content').classList.add('d-none');
    document.getElementById('audit-status').classList.add('d-none');
    document.getElementById('audit-results').classList.add('d-none');
    document.getElementById('audit-loading').classList.add('d-none');
    document.getElementById('audit-error').classList.add('d-none');
    document.getElementById('basic-info-section').classList.add('d-none');
    document.getElementById('missing-values-section').classList.add('d-none');
    document.getElementById('descriptive-stats-section').classList.add('d-none');
    document.getElementById('categorical-stats-section').classList.add('d-none');
}

function resetLaunchButton() {
    const launchButton = document.getElementById('launch-audit-btn');
    launchButton.disabled = false;
    launchButton.innerHTML = '<i class="fas fa-play"></i> Lancer l\'analyse';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    if (typeof num === 'number') {
        return num.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
    return num;
}

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