/**
 * ZAIN HMS - Common Enhanced JavaScript Utilities
 * Shared functionality across all enhanced templates
 */

// Global notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications of the same type
    const existingNotifications = document.querySelectorAll(`.notification-${type}`);
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        color: white;
        font-weight: 500;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        animation: slideInRight 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#22c55e',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // Add icon based on type
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    const icon = document.createElement('i');
    icon.className = icons[type] || icons.info;
    notification.appendChild(icon);
    
    // Add message
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    notification.appendChild(messageSpan);
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '&times;';
    closeButton.style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        margin-left: auto;
    `;
    closeButton.onclick = () => notification.remove();
    notification.appendChild(closeButton);
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }
    }, duration);
}

// Loading overlay utility
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'global-loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(5px);
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: white;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        max-width: 300px;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
        width: 40px;
        height: 40px;
        border: 4px solid #e5e7eb;
        border-top: 4px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem;
    `;
    
    const messageEl = document.createElement('div');
    messageEl.textContent = message;
    messageEl.style.cssText = `
        font-weight: 600;
        color: #374151;
    `;
    
    content.appendChild(spinner);
    content.appendChild(messageEl);
    overlay.appendChild(content);
    document.body.appendChild(overlay);
    
    return overlay;
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('global-loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Form validation utilities
function validateForm(form) {
    const errors = [];
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            errors.push(`${field.name || field.id} is required`);
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Email validation
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            errors.push('Please enter a valid email address');
            field.classList.add('is-invalid');
        }
    });
    
    // Phone validation
    const phoneFields = form.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(field => {
        if (field.value && !isValidPhone(field.value)) {
            errors.push('Please enter a valid phone number');
            field.classList.add('is-invalid');
        }
    });
    
    return errors;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

// Date utilities
function formatDate(date, format = 'MM/dd/yyyy') {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const options = {
        'MM/dd/yyyy': { month: '2-digit', day: '2-digit', year: 'numeric' },
        'dd/MM/yyyy': { day: '2-digit', month: '2-digit', year: 'numeric' },
        'yyyy-MM-dd': { year: 'numeric', month: '2-digit', day: '2-digit' },
        'MMM dd, yyyy': { month: 'short', day: 'numeric', year: 'numeric' },
        'MMMM dd, yyyy': { month: 'long', day: 'numeric', year: 'numeric' }
    };
    
    if (format === 'yyyy-MM-dd') {
        return date.toISOString().split('T')[0];
    }
    
    return date.toLocaleDateString('en-US', options[format] || options['MM/dd/yyyy']);
}

function formatTime(date, format = '12h') {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const options = format === '24h' 
        ? { hour: '2-digit', minute: '2-digit', hour12: false }
        : { hour: 'numeric', minute: '2-digit', hour12: true };
    
    return date.toLocaleTimeString('en-US', options);
}

function getRelativeTime(date) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
    
    return formatDate(date, 'MMM dd, yyyy');
}

// Local storage utilities
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function getFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Failed to read from localStorage:', error);
        return defaultValue;
    }
}

function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Failed to remove from localStorage:', error);
        return false;
    }
}

// URL utilities
function updateURLParameter(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.replaceState({}, '', url);
}

function getURLParameter(param) {
    const url = new URL(window.location);
    return url.searchParams.get(param);
}

function removeURLParameter(param) {
    const url = new URL(window.location);
    url.searchParams.delete(param);
    window.history.replaceState({}, '', url);
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle utility
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Copy to clipboard utility
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification(successMessage, 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text, successMessage);
        });
    } else {
        fallbackCopyToClipboard(text, successMessage);
    }
}

function fallbackCopyToClipboard(text, successMessage) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification(successMessage, 'success');
    } catch (err) {
        showNotification('Failed to copy to clipboard', 'error');
    }
    
    document.body.removeChild(textArea);
}

// CSRF token utility
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

// File download utility
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add CSS animations if not already present
    if (!document.querySelector('#enhanced-animations')) {
        const style = document.createElement('style');
        style.id = 'enhanced-animations';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            .pulse { animation: pulse 2s infinite; }
            .fade-in { animation: fadeIn 0.3s ease-in; }
            .fade-out { animation: fadeOut 0.3s ease-out; }
        `;
        document.head.appendChild(style);
    }
    
    // Initialize form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const errors = validateForm(this);
            if (errors.length > 0) {
                e.preventDefault();
                showNotification(errors.join('<br>'), 'error');
            }
        });
    });
    
    // Initialize tooltips for Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize auto-saving forms
    const autoSaveForms = document.querySelectorAll('form[data-auto-save]');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                const formData = new FormData(form);
                const data = Object.fromEntries(formData.entries());
                saveToLocalStorage(`form-${form.id}`, data);
            }, 1000));
        });
        
        // Load saved data
        const savedData = getFromLocalStorage(`form-${form.id}`);
        if (savedData) {
            Object.keys(savedData).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = savedData[key];
                }
            });
        }
    });
});

// Export utilities for global access
window.showNotification = showNotification;
window.showLoadingOverlay = showLoadingOverlay;
window.hideLoadingOverlay = hideLoadingOverlay;
window.validateForm = validateForm;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.getRelativeTime = getRelativeTime;
window.saveToLocalStorage = saveToLocalStorage;
window.getFromLocalStorage = getFromLocalStorage;
window.removeFromLocalStorage = removeFromLocalStorage;
window.updateURLParameter = updateURLParameter;
window.getURLParameter = getURLParameter;
window.removeURLParameter = removeURLParameter;
window.debounce = debounce;
window.throttle = throttle;
window.copyToClipboard = copyToClipboard;
window.getCookie = getCookie;
window.downloadFile = downloadFile;
