// Add hover effects for language switcher button
document.addEventListener('DOMContentLoaded', function() {
    const langButton = document.getElementById('languageDropdown');
    if (langButton) {
        langButton.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(255, 255, 255, 0.2) !important';
            this.style.borderColor = 'white !important';
        });

        langButton.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'rgba(255, 255, 255, 0.1) !important';
            this.style.borderColor = 'rgba(255, 255, 255, 0.5) !important';
        });
    }

    // Add hover effects for dropdown items
    const dropdownItems = document.querySelectorAll('.language-switcher .dropdown-item:not(.active)');
    dropdownItems.forEach(function(item) {
        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa !important';
            this.style.color = '#212529 !important';
            // Ensure the language name text is also dark
            const nameSpan = this.querySelector('span.flex-grow-1');
            if (nameSpan) {
                nameSpan.style.color = '#212529 !important';
            }
        });

        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'transparent !important';
            this.style.color = '#212529 !important';
            // Ensure the language name text stays dark
            const nameSpan = this.querySelector('span.flex-grow-1');
            if (nameSpan) {
                nameSpan.style.color = '#212529 !important';
            }
        });
    });
});

function switchLanguage(languageCode) {
    // Get current path and search params
    let currentPath = window.location.pathname;
    let currentSearch = window.location.search;
    let currentHash = window.location.hash;

    // List of supported language codes
    const languageCodes = ['en', 'es', 'fr', 'ar', 'hi', 'pt', 'de', 'it'];

    // Check if we're in admin area
    if (currentPath.startsWith('/admin/')) {
        // For admin area, use traditional set_language approach
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/set_language/';

        // Add CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '{{ csrf_token }}';
        form.appendChild(csrfInput);

        // Add language input
        const languageInput = document.createElement('input');
        languageInput.type = 'hidden';
        languageInput.name = 'language';
        languageInput.value = languageCode;
        form.appendChild(languageInput);

        // Add next URL
        const nextInput = document.createElement('input');
        nextInput.type = 'hidden';
        nextInput.name = 'next';
        nextInput.value = currentPath + currentSearch;
        form.appendChild(nextInput);

        // Submit form
        document.body.appendChild(form);
        form.submit();
        return;
    }

    // For user-facing pages, use URL-based switching
    let cleanPath = currentPath;

    // Remove existing language prefix if present
    for (const lang of languageCodes) {
        if (currentPath.startsWith('/' + lang + '/')) {
            cleanPath = currentPath.substring(('/' + lang).length);
            break;
        } else if (currentPath === '/' + lang || currentPath === '/' + lang + '/') {
            cleanPath = '/';
            break;
        }
    }

    // Ensure clean path starts with /
    if (!cleanPath.startsWith('/')) {
        cleanPath = '/' + cleanPath;
    }

    // Create new URL with language prefix
    let newPath = '/' + languageCode + cleanPath;

    // Handle root path
    if (cleanPath === '/' || cleanPath === '') {
        newPath = '/' + languageCode + '/';
    }

    // Redirect to new URL
    window.location.href = newPath + currentSearch + currentHash;
}
