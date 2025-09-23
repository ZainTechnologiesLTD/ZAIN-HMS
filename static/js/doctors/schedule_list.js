document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const filterForm = document.getElementById('filterForm');
    const searchInput = document.getElementById('search');
    const departmentSelect = document.getElementById('department');
    const scheduleStatusSelect = document.getElementById('schedule_status');
    const doctorCards = document.getElementById('doctorCards');

    // Auto-submit on filter change
    let filterTimeout;

    function handleFilterChange() {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(() => {
            showLoadingOverlay();
            filterForm.submit();
        }, 300);
    }

    // Event listeners
    searchInput.addEventListener('input', handleFilterChange);
    departmentSelect.addEventListener('change', handleFilterChange);
    scheduleStatusSelect.addEventListener('change', handleFilterChange);

    // Loading overlay
    function showLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay').cloneNode(true);
        overlay.id = 'activeLoadingOverlay';
        overlay.classList.remove('d-none');
        doctorCards.appendChild(overlay);
    }

    // Card hover effects
    const scheduleCards = document.querySelectorAll('.schedule-card');
    scheduleCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Stats cards hover effects
    const statsCards = document.querySelectorAll('.stats-card');
    statsCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Search input focus effects
    searchInput.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });

    searchInput.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });

    // Clear search functionality
    if (searchInput.value) {
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn btn-link p-0 position-absolute top-50 end-0 translate-middle-y me-2';
        clearBtn.innerHTML = '<i class="bi bi-x-circle text-muted"></i>';
        clearBtn.style.zIndex = '10';

        clearBtn.addEventListener('click', function() {
            searchInput.value = '';
            handleFilterChange();
        });

        searchInput.parentElement.style.position = 'relative';
        searchInput.parentElement.appendChild(clearBtn);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search').focus();
    }
});
