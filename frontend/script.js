// Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const singleValidationForm = document.getElementById('singleValidationForm');
const bulkValidationForm = document.getElementById('bulkValidationForm');
const downloadSampleBtn = document.getElementById('downloadSample');
const exportResultsBtn = document.getElementById('exportResultsBtn');
const clearResultsBtn = document.getElementById('clearResultsBtn');
const validAccountsTable = document.getElementById('validAccountsTable');
const invalidAccountsTable = document.getElementById('invalidAccountsTable');
const singleResult = document.getElementById('singleResult');
const singleResultContent = document.getElementById('singleResultContent');
const bulkResultsContainer = document.getElementById('bulkResultsContainer');
const resultsSummary = document.getElementById('resultsSummary');
const validCount = document.getElementById('validCount');
const invalidCount = document.getElementById('invalidCount');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');

// Bootstrap modals
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
const errorModalContent = document.getElementById('errorModalContent');

// Store validation results for export
let validationResults = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    singleValidationForm.addEventListener('submit', handleSingleValidation);
    bulkValidationForm.addEventListener('submit', handleBulkValidation);
    downloadSampleBtn.addEventListener('click', downloadSampleCSV);
    exportResultsBtn.addEventListener('click', exportResults);
    clearResultsBtn.addEventListener('click', clearResults);
});

/**
 * Single Account Validation
 */
async function handleSingleValidation(event) {
    event.preventDefault();
    
    const accountNumber = document.getElementById('accountNumber').value.trim();
    const bankCode = document.getElementById('bankCode').value.trim();
    
    if (!accountNumber || !bankCode) {
        showError('Please enter both account number and bank code.');
        return;
    }
    
    showLoading('Validating account...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                accountNumber,
                bankCode
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Validation failed');
        }
        
        displaySingleResult(result);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Display Single Validation Result
 */
function displaySingleResult(result) {
    singleResult.classList.remove('d-none');
    
    // Check if result indicates success or failure
    const isValid = !result.errorCode && !result.errorMessage;
    
    let html = '';
    if (isValid) {
        singleResultContent.classList.add('valid-result');
        singleResultContent.classList.remove('invalid-result');
        
        html = `
            <div class="row">
                <div class="col-md-6"><strong>Account Number:</strong></div>
                <div class="col-md-6">${result.accountNumber}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Bank Code:</strong></div>
                <div class="col-md-6">${result.bankCode}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Account Holder:</strong></div>
                <div class="col-md-6">${result.accountHolderName || 'N/A'}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Bank Name:</strong></div>
                <div class="col-md-6">${result.bankName || 'N/A'}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Currency:</strong></div>
                <div class="col-md-6">${result.currency || 'N/A'}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Status:</strong></div>
                <div class="col-md-6"><span class="badge bg-success">Valid Account</span></div>
            </div>
        `;
    } else {
        singleResultContent.classList.add('invalid-result');
        singleResultContent.classList.remove('valid-result');
        
        html = `
            <div class="row">
                <div class="col-md-6"><strong>Account Number:</strong></div>
                <div class="col-md-6">${result.accountNumber}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Bank Code:</strong></div>
                <div class="col-md-6">${result.bankCode}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Status:</strong></div>
                <div class="col-md-6"><span class="badge bg-danger">Invalid Account</span></div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Error Code:</strong></div>
                <div class="col-md-6">${result.errorCode || 'AC-01'}</div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6"><strong>Error Message:</strong></div>
                <div class="col-md-6">${result.errorMessage || 'Invalid account'}</div>
            </div>
        `;
    }
    
    singleResultContent.innerHTML = html;
}

/**
 * Bulk Account Validation
 */
async function handleBulkValidation(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('csvFile');
    if (!fileInput.files || fileInput.files.length === 0) {
        showError('Please select a CSV file to upload.');
        return;
    }
    
    const file = fileInput.files[0];
    if (!file.name.endsWith('.csv')) {
        showError('Please upload a valid CSV file.');
        return;
    }
    
    showLoading('Uploading and processing file...');
    showProgress();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/validate/bulk`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Bulk validation failed');
        }
        
        validationResults = result;
        displayBulkResults(result);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
        hideProgress();
    }
}

/**
 * Display Bulk Validation Results
 */
function displayBulkResults(results) {
    const { valid, invalid, summary } = results;
    
    // Update count badges
    validCount.textContent = valid.length;
    invalidCount.textContent = invalid.length;
    
    // Display summary
    resultsSummary.innerHTML = `
        <strong>Summary:</strong> Processed ${summary.total} accounts in ${summary.processingTime}s. 
        <span class="text-success">${summary.valid} valid</span> and 
        <span class="text-danger">${summary.invalid} invalid</span> accounts found.
    `;
    
    // Populate valid accounts table
    validAccountsTable.innerHTML = '';
    valid.forEach(account => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${account.accountNumber}</td>
            <td>${account.bankCode}</td>
            <td>${account.accountHolderName}</td>
            <td>${account.bankName}</td>
            <td>${account.currency}</td>
            <td><span class="badge bg-success">Valid</span></td>
        `;
        validAccountsTable.appendChild(row);
    });
    
    // Populate invalid accounts table
    invalidAccountsTable.innerHTML = '';
    invalid.forEach(account => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${account.accountNumber}</td>
            <td>${account.bankCode}</td>
            <td>${account.errorCode}</td>
            <td>${account.errorMessage}</td>
        `;
        invalidAccountsTable.appendChild(row);
    });
    
    // Show results container
    bulkResultsContainer.classList.remove('d-none');
}

/**
 * Download Sample CSV
 */
async function downloadSampleCSV(event) {
    event.preventDefault();
    
    try {
        const response = await fetch(`${API_BASE_URL}/sample`);
        
        if (!response.ok) {
            throw new Error('Failed to download sample CSV');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'sample_accounts.csv';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
}

/**
 * Export Results to CSV
 */
function exportResults() {
    if (!validationResults) {
        showError('No validation results to export.');
        return;
    }
    
    try {
        // Create CSV content
        let csvContent = 'Account Number,Bank Code,Status,Bank Name,Account Holder Name,Error Code,Error Message\n';
        
        // Add valid accounts
        validationResults.valid.forEach(account => {
            csvContent += `${account.accountNumber},${account.bankCode},Valid,${account.bankName || ''},${account.accountHolderName || ''},,\n`;
        });
        
        // Add invalid accounts
        validationResults.invalid.forEach(account => {
            csvContent += `${account.accountNumber},${account.bankCode},Invalid,,,${account.errorCode || ''},${account.errorMessage || ''}\n`;
        });
        
        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `account_validation_results_${new Date().toISOString().slice(0,10)}.csv`;
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        showError(`Error exporting results: ${error.message}`);
    }
}

/**
 * Clear Results
 */
function clearResults() {
    // Clear tables
    validAccountsTable.innerHTML = '';
    invalidAccountsTable.innerHTML = '';
    
    // Reset counts
    validCount.textContent = '0';
    invalidCount.textContent = '0';
    
    // Hide results container
    bulkResultsContainer.classList.add('d-none');
    
    // Clear validation results
    validationResults = null;
}

/**
 * Show Progress Bar
 */
function showProgress() {
    progressContainer.classList.remove('d-none');
    progressBar.style.width = '0%';
    
    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
        if (progress >= 90) {
            clearInterval(interval);
        } else {
            progress += Math.random() * 10;
            progressBar.style.width = `${Math.min(progress, 90)}%`;
        }
    }, 300);
    
    // Store interval ID to clear it later
    progressBar.dataset.intervalId = interval;
}

/**
 * Hide Progress Bar
 */
function hideProgress() {
    // Complete progress
    progressBar.style.width = '100%';
    
    // Clear interval if exists
    if (progressBar.dataset.intervalId) {
        clearInterval(parseInt(progressBar.dataset.intervalId));
    }
    
    // Hide after animation
    setTimeout(() => {
        progressContainer.classList.add('d-none');
    }, 500);
}

/**
 * Show Loading Modal
 */
function showLoading(message = 'Processing, please wait...') {
    document.getElementById('loadingMessage').textContent = message;
    loadingModal.show();
}

/**
 * Hide Loading Modal
 */
function hideLoading() {
    loadingModal.hide();
}

/**
 * Show Error Modal
 */
function showError(message) {
    errorModalContent.textContent = message;
    errorModal.show();
}