/**
 * Dataset Analysis - Main Module
 * Point d'entrée principal pour l'analyse de dataset
 */

import { initializeBucketConnectionTesting } from './tasks.js';
import { initializeAnalysis } from './audit.js';
import { initializeIAAnalysis } from './ia_analysis.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize bucket connection testing
    initializeBucketConnectionTesting();
    
    // Initialize audit analysis
    initializeAnalysis();
    
    // Initialize IA analysis
    initializeIAAnalysis();
    
    // Initialize tab functionality
    initializeAnalysisTabs();
});

/**
 * Initialize tab functionality
 */
function initializeAnalysisTabs() {
    const dataAnalysisTab = document.getElementById('data-analysis-tab');
    const iaAnalysisTab = document.getElementById('ia-analysis-tab');
    
    if (dataAnalysisTab) {
        dataAnalysisTab.addEventListener('click', function() {
            switchToDataAnalysisTab();
        });
    }
    
    if (iaAnalysisTab) {
        iaAnalysisTab.addEventListener('click', function() {
            switchToIAAnalysisTab();
        });
    }
}

/**
 * Switch to IA analysis tab
 */
function switchToIAAnalysisTab() {
    const dataAnalysisContent = document.getElementById('data-analysis-content');
    const iaAnalysisContent = document.getElementById('ia-analysis-content');
    
    if (dataAnalysisContent) {
        dataAnalysisContent.classList.remove('show', 'active');
    }
    
    if (iaAnalysisContent) {
        iaAnalysisContent.classList.add('show', 'active');
    }
    
    updateTabButtonStates('ia-analysis');
}

/**
 * Switch to data analysis tab
 */
function switchToDataAnalysisTab() {
    const dataAnalysisContent = document.getElementById('data-analysis-content');
    const iaAnalysisContent = document.getElementById('ia-analysis-content');
    
    if (dataAnalysisContent) {
        dataAnalysisContent.classList.add('show', 'active');
    }
    
    if (iaAnalysisContent) {
        iaAnalysisContent.classList.remove('show', 'active');
    }
    
    updateTabButtonStates('data-analysis');
}

/**
 * Update tab button states
 */
function updateTabButtonStates(activeTab) {
    const dataAnalysisTab = document.getElementById('data-analysis-tab');
    const iaAnalysisTab = document.getElementById('ia-analysis-tab');
    
    if (activeTab === 'data-analysis') {
        if (dataAnalysisTab) {
            dataAnalysisTab.classList.add('active');
            dataAnalysisTab.setAttribute('aria-selected', 'true');
        }
        if (iaAnalysisTab) {
            iaAnalysisTab.classList.remove('active');
            iaAnalysisTab.setAttribute('aria-selected', 'false');
        }
    } else if (activeTab === 'ia-analysis') {
        if (dataAnalysisTab) {
            dataAnalysisTab.classList.remove('active');
            dataAnalysisTab.setAttribute('aria-selected', 'false');
        }
        if (iaAnalysisTab) {
            iaAnalysisTab.classList.add('active');
            iaAnalysisTab.setAttribute('aria-selected', 'true');
        }
    }
}

/**
 * Add tab indicator
 */
export function addTabIndicator(tabId, indicatorType = 'success') {
    const tab = document.getElementById(tabId);
    if (tab) {
        const existingIndicator = tab.querySelector('.tab-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        const indicator = document.createElement('span');
        indicator.className = `badge bg-${indicatorType} ms-2 tab-indicator`;
        indicator.innerHTML = '<i class="fas fa-check"></i>';
        tab.appendChild(indicator);
    }
}

/**
 * Remove tab indicator
 */
export function removeTabIndicator(tabId) {
    const tab = document.getElementById(tabId);
    if (tab) {
        const indicator = tab.querySelector('.tab-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
}

// Export functions for use in other modules
export { switchToIAAnalysisTab, switchToDataAnalysisTab }; 