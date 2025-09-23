/*!
 * ZAIN HMS - Core Utilities
 * Global utility functions and helpers
 * Version: 2.0.0
 * © 2025 ZAIN Technologies
 * Licensed under MIT License
 */

(function(window, document) {
    'use strict';

    // ZAIN HMS Global Namespace
    window.ZAIN_HMS = window.ZAIN_HMS || {};

    const ZAIN_HMS = window.ZAIN_HMS;

    // Configuration
    ZAIN_HMS.config = {
        version: '2.0.0',
        name: 'ZAIN HMS - Unified Hospital Management System',
        vendor: 'ZAIN Technologies',
        apiUrl: '/api/',
        debug: false
    };

    // Utility Functions
    ZAIN_HMS.utils = {
        // DOM Ready
        ready: function(fn) {
            if (document.readyState !== 'loading') {
                fn();
            } else {
                document.addEventListener('DOMContentLoaded', fn);
            }
        },

        // AJAX Request Helper
        ajax: function(url, options = {}) {
            const defaults = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            };

            const config = Object.assign(defaults, options);

            return fetch(url, config)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('AJAX Error:', error);
                    throw error;
                });
        },

        // Get Cookie Value
        getCookie: function(name) {
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
        },

        // Show Toast Notification
        showToast: function(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `zain-toast zain-toast-${type}`;
            toast.innerHTML = `
                <div class="zain-toast-content">
                    <span class="zain-toast-message">${message}</span>
                    <button class="zain-toast-close" onclick="this.parentNode.parentNode.remove()">×</button>
                </div>
            `;

            document.body.appendChild(toast);

            // Auto remove
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, duration);

            return toast;
        },

        // Format Currency
        formatCurrency: function(amount, currency = '$') {
            return currency + parseFloat(amount).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        },

        // Format Date
        formatDate: function(date, format = 'YYYY-MM-DD') {
            const d = new Date(date);
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');

            return format
                .replace('YYYY', year)
                .replace('MM', month)
                .replace('DD', day);
        },

        // Debounce Function
        debounce: function(func, wait, immediate) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    if (!immediate) func(...args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func(...args);
            };
        }
    };

    // UI Components
    ZAIN_HMS.ui = {
        init: function() {
            this.initSidebar();
            this.initTooltips();
            this.initModals();
        },

        initSidebar: function() {
            const sidebar = document.querySelector('.sidebar');
            const toggle = document.querySelector('.sidebar-toggle');

            if (toggle && sidebar) {
                toggle.addEventListener('click', () => {
                    sidebar.classList.toggle('collapsed');
                    localStorage.setItem('zain-sidebar-collapsed', sidebar.classList.contains('collapsed'));
                });
            }

            // Restore sidebar state
            if (localStorage.getItem('zain-sidebar-collapsed') === 'true' && sidebar) {
                sidebar.classList.add('collapsed');
            }
        },

        initTooltips: function() {
            // Initialize Bootstrap tooltips if available
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            }
        },

        initModals: function() {
            // Initialize Bootstrap modals if available
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                document.querySelectorAll('.modal').forEach(modalEl => {
                    new bootstrap.Modal(modalEl);
                });
            }
        }
    };

    // Initialize on DOM ready
    ZAIN_HMS.utils.ready(() => {
        ZAIN_HMS.ui.init();
        console.log('ZAIN HMS Core Utilities Loaded');
    });

})(window, document);
