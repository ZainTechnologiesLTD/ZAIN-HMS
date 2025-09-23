        // Sidebar Dropdown Toggle Function
        window.toggleDropdown = function(element, event) {
            console.log('toggleDropdown called with:', element, event);

            if (!element) {
                console.error('No element provided to toggleDropdown');
                return false;
            }

            event.preventDefault();
            event.stopPropagation();

            const dropdown = element.parentElement;
            if (!dropdown) {
                console.error('No parent element found for dropdown toggle');
                return false;
            }

            console.log('dropdown element:', dropdown);
            const isCurrentlyOpen = dropdown.classList.contains('show');
            console.log('isCurrentlyOpen:', isCurrentlyOpen);

            // Close all dropdowns first
            document.querySelectorAll('.nav-dropdown.show').forEach(function(openDropdown) {
                openDropdown.classList.remove('show');
                console.log('closed dropdown:', openDropdown);
            });

            // If the clicked dropdown wasn't open, open it
            if (!isCurrentlyOpen) {
                dropdown.classList.add('show');
                console.log('opened dropdown:', dropdown);
            }

            return false; // Prevent default link behavior
        }

        // Setup dropdown event listeners
        function setupDropdownListeners() {
            console.log('Setting up dropdown listeners...');
            const toggleElements = document.querySelectorAll('[data-dropdown-toggle]');
            console.log(`Found ${toggleElements.length} dropdown toggle elements`);

            toggleElements.forEach(function(toggle, index) {
                // Prevent double event listeners
                if (toggle.hasAttribute('data-listener-added')) {
                    console.log(`Skipping element ${index} - already has listener`);
                    return;
                }
                toggle.setAttribute('data-listener-added', 'true');

                console.log(`Adding listener to element ${index}:`, toggle);
                toggle.addEventListener('click', function(event) {
                    console.log('Dropdown clicked!', this);

                    // Prevent Alpine.js from interfering
                    event.stopImmediatePropagation();

                    window.toggleDropdown(this, event);
                });
            });

            console.log('Dropdown listeners setup complete');
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.nav-dropdown')) {
                document.querySelectorAll('.nav-dropdown.show').forEach(function(dropdown) {
                    dropdown.classList.remove('show');
                });
            }
        });

        // Enhanced Sidebar Toggle Functionality - Single source of truth
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Base dashboard script initializing...');

            // Initialize dropdown listeners after a small delay to ensure Alpine.js is ready
            setTimeout(() => {
                console.log('Initializing dropdown listeners...');
                setupDropdownListeners();
            }, 200); // Increased delay slightly

            const sidebar = document.getElementById('sidebar');
            const sidebarToggle = document.getElementById('sidebarToggle');
            const mainContent = document.querySelector('.main-content');

            // Prevent multiple event listeners
            if (sidebarToggle && sidebar && !sidebarToggle.hasAttribute('data-listener-added')) {
                sidebarToggle.setAttribute('data-listener-added', 'true');

                sidebarToggle.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();

                    // Toggle collapsed class on sidebar
                    sidebar.classList.toggle('collapsed');

                    // Enhanced margin calculations - Use fixed pixel values to prevent gaps
                    const isCollapsed = sidebar.classList.contains('collapsed');
                    if (mainContent) {
                        // Use exact pixel values matching CSS and admin template
                        if (isCollapsed) {
                            mainContent.style.marginLeft = '80px';
                        } else {
                            mainContent.style.marginLeft = '281px';
                        }
                    }

                    // Trigger a resize event to help any responsive components adjust
                    window.dispatchEvent(new Event('resize'));

                    // Store sidebar state
                    localStorage.setItem('sidebarCollapsed', isCollapsed);
                });
            }

            // Mobile Sidebar Toggle - Separate logic to avoid conflicts
            function handleMobileSidebar() {
                if (window.innerWidth <= 768) {
                    if (sidebar) {
                        sidebar.addEventListener('click', function(e) {
                            e.stopPropagation();
                        });

                        // Close sidebar when clicking outside on mobile
                        document.addEventListener('click', function(e) {
                            if (!sidebar.contains(e.target) &&
                                !e.target.closest('#sidebarToggle')) {
                                sidebar.classList.remove('active');
                            }
                        });
                    }
                }
            }

            // Initialize mobile behavior
            handleMobileSidebar();

            // Restore sidebar state from localStorage
            const sidebarCollapsed = localStorage.getItem('sidebarCollapsed');
            if (sidebarCollapsed === 'true' && sidebar) {
                sidebar.classList.add('collapsed');
                if (mainContent) {
                    // Use fixed pixel values matching CSS
                    mainContent.style.marginLeft = '80px';
                }
            } else if (mainContent) {
                // Ensure expanded state has proper margin with fixed pixels
                mainContent.style.marginLeft = '281px';
            }

            // Initialize dropdown state based on active menu items
            console.log('Initializing dropdowns...');
            document.querySelectorAll('.nav-dropdown').forEach(function(dropdown) {
                console.log('checking dropdown:', dropdown);
                const hasActiveItem = dropdown.querySelector('.nav-dropdown-menu .active');
                console.log('hasActiveItem:', hasActiveItem);
                if (hasActiveItem) {
                    dropdown.classList.add('show');
                    console.log('Auto-opened dropdown due to active item:', dropdown);
                }
            });

            // Setup dropdown event listeners
            setupDropdownListeners();

            // Fallback / progressive enhancement: event delegation (handles dynamically added nodes)
            document.addEventListener('click', function(e) {
                const toggle = e.target.closest('[data-dropdown-toggle]');
                if (toggle) {
                    e.preventDefault();
                    const dropdown = toggle.parentElement;
                    const isOpen = dropdown.classList.contains('show');
                    document.querySelectorAll('.nav-dropdown.show').forEach(d => {
                        if (d !== dropdown) d.classList.remove('show');
                    });
                    if (!isOpen) dropdown.classList.add('show'); else dropdown.classList.remove('show');
                }
            });

            // Ensure Bootstrap header dropdowns are interactive even if other listeners exist
            try {
                const headerDropdownButtons = document.querySelectorAll('.main-header [data-bs-toggle="dropdown"]');
                console.log(`Found ${headerDropdownButtons.length} header dropdown toggles`);
                headerDropdownButtons.forEach((btn, idx) => {
                    // Deduplicate
                    if (btn.hasAttribute('data-bs-listener-added')) return;
                    btn.setAttribute('data-bs-listener-added', 'true');

                    // Capture-phase listener to avoid interference
                    btn.addEventListener('click', function(e) {
                        console.log('Header dropdown clicked:', idx, this);
                        // Let Bootstrap handle it when available; avoid canceling default behavior
                        try {
                            if (window.bootstrap && bootstrap.Dropdown) {
                                // Ensure an instance exists; do not call toggle twice
                                bootstrap.Dropdown.getOrCreateInstance(this);
                                // Do not preventDefault; Bootstrap will process data attributes
                            } else {
                                // Fallback manual toggle if Bootstrap API not available
                                e.preventDefault();
                                e.stopPropagation();
                                const parent = this.closest('.dropdown');
                                const menu = parent && parent.querySelector('.dropdown-menu');
                                if (menu) menu.classList.toggle('show');
                            }
                        } catch (err) {
                            console.warn('Bootstrap Dropdown toggle failed:', err);
                            e.preventDefault();
                            e.stopPropagation();
                            const parent = this.closest('.dropdown');
                            const menu = parent && parent.querySelector('.dropdown-menu');
                            if (menu) menu.classList.toggle('show');
                        }
                    }, { capture: true });
                });

                // Close header dropdowns when clicking outside
                document.addEventListener('click', function(e) {
                    if (!e.target.closest('.main-header .dropdown')) {
                        document.querySelectorAll('.main-header .dropdown-menu.show').forEach(menu => {
                            try {
                                const toggleBtn = menu.parentElement?.querySelector('[data-bs-toggle="dropdown"]');
                                if (toggleBtn) {
                                    if (window.bootstrap && bootstrap.Dropdown) {
                                        const inst = bootstrap.Dropdown.getOrCreateInstance(toggleBtn);
                                        inst.hide();
                                    } else {
                                        menu.classList.remove('show');
                                    }
                                }
                            } catch(_) {}
                        });
                    }
                });
            } catch (e) {
                console.warn('Header dropdown bootstrap init failed:', e);
            }

            // Global Search (bind reliably after DOM is ready)
            const searchInput = document.getElementById('globalSearch');
            if (searchInput) {
                searchInput.addEventListener('keyup', function(e) {
                    if (e.key === 'Enter') {
                        const query = this.value.trim();
                        if (query.length > 2) {
                            // Use general search route by default
                            window.location.href = `/search/?q=${encodeURIComponent(query)}`;
                        }
                    }
                });
            }

            const searchBtn = document.querySelector('#globalSearch + button');
            if (searchBtn) {
                searchBtn.addEventListener('click', function() {
                    const input = document.getElementById('globalSearch');
                    const query = input ? input.value.trim() : '';
                    if (query.length > 2) {
                        window.location.href = `/search/?q=${encodeURIComponent(query)}`;
                    }
                });
            }
        });

        // Auto-dismiss alerts after 5 seconds
        setTimeout(function() {
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => {
                if (alert.classList.contains('show')) {
                    alert.classList.remove('show');
                    alert.classList.add('fade');
                    setTimeout(() => alert.remove(), 300);
                }
            });
        }, 5000);

        // CSRF Token for AJAX requests
        function getCsrfToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        }

        // Handle window resize for responsive behavior
        window.addEventListener('resize', function() {
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.querySelector('.main-content');

            if (window.innerWidth <= 768) {
                // Mobile: reset sidebar state
                if (sidebar) {
                    sidebar.classList.remove('collapsed');
                }
                if (mainContent) {
                    mainContent.style.marginLeft = '0';
                }
            } else {
                // Desktop: restore sidebar state
                const sidebarCollapsed = localStorage.getItem('sidebarCollapsed');
                if (sidebar && sidebarCollapsed === 'true') {
                    sidebar.classList.add('collapsed');
                    if (mainContent) {
                        mainContent.style.marginLeft = '80px';
                    }
                }
            }
        });
