function switchLanguage(languageCode) {
    // Get current path
    let currentPath = window.location.pathname;
    let currentSearch = window.location.search;

    // List of supported language codes
    const languageCodes = ['en', 'es', 'fr', 'ar', 'hi', 'pt', 'de', 'it'];

    // Remove existing language prefix if present
    let cleanPath = currentPath;
    for (const lang of languageCodes) {
        if (currentPath.startsWith('/' + lang + '/')) {
            cleanPath = currentPath.substring(('/' + lang).length);
            break;
        } else if (currentPath === '/' + lang) {
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
    if (cleanPath === '/') {
        newPath = '/' + languageCode + '/';
    }

    // Redirect to new URL
    window.location.href = newPath + currentSearch;
}
