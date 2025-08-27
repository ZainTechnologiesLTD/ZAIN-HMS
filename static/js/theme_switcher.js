document.addEventListener('DOMContentLoaded', function () {
    // --- 1. CREATE THE THEME SWITCHER BUTTON ---
    const themeSwitcher = document.createElement('li');
    themeSwitcher.className = 'nav-item';
    themeSwitcher.innerHTML = `
        <a class="nav-link" href="#" id="theme-toggle" role="button" aria-pressed="false" aria-label="Toggle theme" title="Toggle theme" tabindex="0">
            <i class="fas fa-sun" aria-hidden="true"></i>
        </a>
    `;

    // --- 2. ADD THE BUTTON TO THE NAVBAR ---
    // Find the topbar nav and add the button before the user menu dropdown
    let topbarNav = document.querySelector('.navbar-nav.ml-auto');
    if (!topbarNav) {
        // fallback - try different selector used by some Jazzmin versions
        topbarNav = document.querySelector('.navbar-nav');
    }
    if (topbarNav) {
        const userMenu = topbarNav.querySelector('.dropdown');
        try {
            topbarNav.insertBefore(themeSwitcher, userMenu);
        } catch (err) {
            topbarNav.appendChild(themeSwitcher);
        }
    } else {
        // if navbar not present, append to body as last resort
        document.body.appendChild(themeSwitcher);
    }

    // --- 3. THEME HANDLING LOGIC ---
    const toggle = document.getElementById('theme-toggle');
    const rootEl = document.documentElement || document.body;
    const icon = toggle.querySelector('i');

    // Function to apply the correct theme and icon
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            rootEl.classList.add('dark-mode');
            toggle.setAttribute('aria-pressed', 'true');
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            toggle.title = 'Switch to light mode';
        } else {
            rootEl.classList.remove('dark-mode');
            toggle.setAttribute('aria-pressed', 'false');
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            toggle.title = 'Switch to dark mode';
        }
    };

    // --- 4. LOAD SAVED THEME & ATTACH EVENT LISTENER ---
    // Load saved theme: localStorage -> if not found, use OS preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme ? savedTheme : (prefersDark ? 'dark' : 'light');
    applyTheme(initialTheme);

    // Toggle handler (click + keyboard)
    const toggleHandler = (e) => {
        e && e.preventDefault();
        const currentTheme = rootEl.classList.contains('dark-mode') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };

    toggle.addEventListener('click', toggleHandler);

    // Keyboard accessibility: Enter and Space
    toggle.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleHandler(e);
        }
    });

    // Keep UI in sync if OS preference changes and user has not set a manual choice
    if (!savedTheme && window.matchMedia) {
        const mq = window.matchMedia('(prefers-color-scheme: dark)');
        mq.addEventListener && mq.addEventListener('change', (e) => {
            const newPref = e.matches ? 'dark' : 'light';
            // only apply if user hasn't chosen manually
            if (!localStorage.getItem('theme')) {
                applyTheme(newPref);
            }
        });
    }
});
