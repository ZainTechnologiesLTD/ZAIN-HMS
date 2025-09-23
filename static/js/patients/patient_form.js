    let currentTab = 0;
    const tabs = ['personal', 'contact', 'medical', 'emergency'];

    function showTab(n) {
        // Hide all tabs
        tabs.forEach((tab, index) => {
            const tabPane = document.getElementById(tab);
            const tabButton = document.getElementById(tab + '-tab');
            if (index === n) {
                tabPane.classList.add('show', 'active');
                tabButton.classList.add('active');
            } else {
                tabPane.classList.remove('show', 'active');
                tabButton.classList.remove('active');
            }
        });

        // Update navigation buttons
        document.getElementById('prevBtn').style.display = n === 0 ? 'none' : 'inline-block';
        document.getElementById('nextBtn').style.display = n === (tabs.length - 1) ? 'none' : 'inline-block';
        document.getElementById('submitBtn').style.display = n === (tabs.length - 1) ? 'inline-block' : 'none';

        currentTab = n;
    }

    function nextTab() {
        // Validate current tab before moving to next
        if (validateCurrentTab() && currentTab < tabs.length - 1) {
            currentTab++;
            showTab(currentTab);
        }
    }

    function previousTab() {
        if (currentTab > 0) {
            currentTab--;
            showTab(currentTab);
        }
    }

    function validateCurrentTab() {
        const currentTabElement = document.getElementById(tabs[currentTab]);
        const requiredFields = currentTabElement.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });

        if (!isValid) {
            showNotification('Please fill all required fields before proceeding', 'error');
        }

        return isValid;
    }

    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        showTab(0);

        // Add click handlers for tab buttons
        tabs.forEach((tab, index) => {
            document.getElementById(tab + '-tab').addEventListener('click', function() {
                if (index > currentTab) {
                    // Moving forward - validate current tab
                    if (validateCurrentTab()) {
                        showTab(index);
                    }
                } else {
                    // Moving backward - no validation needed
                    showTab(index);
                }
            });
        });

        // Form submission validation
        document.getElementById('patientForm').addEventListener('submit', function(e) {
            let isFormValid = true;

            // Validate all tabs
            tabs.forEach((tab, index) => {
                const tabElement = document.getElementById(tab);
                const requiredFields = tabElement.querySelectorAll('input[required], select[required], textarea[required]');

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.classList.add('is-invalid');
                        isFormValid = false;
                    }
                });
            });

            if (!isFormValid) {
                e.preventDefault();
                showNotification('Please fill all required fields in all tabs', 'error');
                // Show first tab with errors
                for (let i = 0; i < tabs.length; i++) {
                    const tabElement = document.getElementById(tabs[i]);
                    if (tabElement.querySelector('.is-invalid')) {
                        showTab(i);
                        break;
                    }
                }
            } else {
                // Show loading state
                const submitBtn = document.getElementById('submitBtn');
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            }
        });

        // Real-time validation for required fields
        document.querySelectorAll('input[required], select[required], textarea[required]').forEach(field => {
            field.addEventListener('blur', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                }
            });
        });

        // Initialize Custom Searchable Country Dropdown
        initializeCountryDropdown();

        function initializeCountryDropdown() {
            const countryInput = document.querySelector('.country-search-input');
            if (!countryInput) return;

            console.log('Initializing custom country dropdown...');

            // Countries data - comprehensive list
            const countries = [
                {code: 'AF', name: 'Afghanistan'},
                {code: 'AL', name: 'Albania'},
                {code: 'DZ', name: 'Algeria'},
                {code: 'AS', name: 'American Samoa'},
                {code: 'AD', name: 'Andorra'},
                {code: 'AO', name: 'Angola'},
                {code: 'AI', name: 'Anguilla'},
                {code: 'AQ', name: 'Antarctica'},
                {code: 'AG', name: 'Antigua and Barbuda'},
                {code: 'AR', name: 'Argentina'},
                {code: 'AM', name: 'Armenia'},
                {code: 'AW', name: 'Aruba'},
                {code: 'AU', name: 'Australia'},
                {code: 'AT', name: 'Austria'},
                {code: 'AZ', name: 'Azerbaijan'},
                {code: 'BS', name: 'Bahamas'},
                {code: 'BH', name: 'Bahrain'},
                {code: 'BD', name: 'Bangladesh'},
                {code: 'BB', name: 'Barbados'},
                {code: 'BY', name: 'Belarus'},
                {code: 'BE', name: 'Belgium'},
                {code: 'BZ', name: 'Belize'},
                {code: 'BJ', name: 'Benin'},
                {code: 'BM', name: 'Bermuda'},
                {code: 'BT', name: 'Bhutan'},
                {code: 'BO', name: 'Bolivia'},
                {code: 'BA', name: 'Bosnia and Herzegovina'},
                {code: 'BW', name: 'Botswana'},
                {code: 'BR', name: 'Brazil'},
                {code: 'BN', name: 'Brunei'},
                {code: 'BG', name: 'Bulgaria'},
                {code: 'BF', name: 'Burkina Faso'},
                {code: 'BI', name: 'Burundi'},
                {code: 'KH', name: 'Cambodia'},
                {code: 'CM', name: 'Cameroon'},
                {code: 'CA', name: 'Canada'},
                {code: 'CV', name: 'Cape Verde'},
                {code: 'KY', name: 'Cayman Islands'},
                {code: 'CF', name: 'Central African Republic'},
                {code: 'TD', name: 'Chad'},
                {code: 'CL', name: 'Chile'},
                {code: 'CN', name: 'China'},
                {code: 'CO', name: 'Colombia'},
                {code: 'KM', name: 'Comoros'},
                {code: 'CG', name: 'Congo'},
                {code: 'CD', name: 'Congo (Democratic Republic)'},
                {code: 'CR', name: 'Costa Rica'},
                {code: 'CI', name: 'Côte d\'Ivoire'},
                {code: 'HR', name: 'Croatia'},
                {code: 'CU', name: 'Cuba'},
                {code: 'CY', name: 'Cyprus'},
                {code: 'CZ', name: 'Czech Republic'},
                {code: 'DK', name: 'Denmark'},
                {code: 'DJ', name: 'Djibouti'},
                {code: 'DM', name: 'Dominica'},
                {code: 'DO', name: 'Dominican Republic'},
                {code: 'EC', name: 'Ecuador'},
                {code: 'EG', name: 'Egypt'},
                {code: 'SV', name: 'El Salvador'},
                {code: 'GQ', name: 'Equatorial Guinea'},
                {code: 'ER', name: 'Eritrea'},
                {code: 'EE', name: 'Estonia'},
                {code: 'ET', name: 'Ethiopia'},
                {code: 'FJ', name: 'Fiji'},
                {code: 'FI', name: 'Finland'},
                {code: 'FR', name: 'France'},
                {code: 'GA', name: 'Gabon'},
                {code: 'GM', name: 'Gambia'},
                {code: 'GE', name: 'Georgia'},
                {code: 'DE', name: 'Germany'},
                {code: 'GH', name: 'Ghana'},
                {code: 'GR', name: 'Greece'},
                {code: 'GD', name: 'Grenada'},
                {code: 'GT', name: 'Guatemala'},
                {code: 'GN', name: 'Guinea'},
                {code: 'GW', name: 'Guinea-Bissau'},
                {code: 'GY', name: 'Guyana'},
                {code: 'HT', name: 'Haiti'},
                {code: 'HN', name: 'Honduras'},
                {code: 'HU', name: 'Hungary'},
                {code: 'IS', name: 'Iceland'},
                {code: 'IN', name: 'India'},
                {code: 'ID', name: 'Indonesia'},
                {code: 'IR', name: 'Iran'},
                {code: 'IQ', name: 'Iraq'},
                {code: 'IE', name: 'Ireland'},
                {code: 'IL', name: 'Israel'},
                {code: 'IT', name: 'Italy'},
                {code: 'JM', name: 'Jamaica'},
                {code: 'JP', name: 'Japan'},
                {code: 'JO', name: 'Jordan'},
                {code: 'KZ', name: 'Kazakhstan'},
                {code: 'KE', name: 'Kenya'},
                {code: 'KI', name: 'Kiribati'},
                {code: 'KP', name: 'Korea (North)'},
                {code: 'KR', name: 'Korea (South)'},
                {code: 'KW', name: 'Kuwait'},
                {code: 'KG', name: 'Kyrgyzstan'},
                {code: 'LA', name: 'Laos'},
                {code: 'LV', name: 'Latvia'},
                {code: 'LB', name: 'Lebanon'},
                {code: 'LS', name: 'Lesotho'},
                {code: 'LR', name: 'Liberia'},
                {code: 'LY', name: 'Libya'},
                {code: 'LI', name: 'Liechtenstein'},
                {code: 'LT', name: 'Lithuania'},
                {code: 'LU', name: 'Luxembourg'},
                {code: 'MG', name: 'Madagascar'},
                {code: 'MW', name: 'Malawi'},
                {code: 'MY', name: 'Malaysia'},
                {code: 'MV', name: 'Maldives'},
                {code: 'ML', name: 'Mali'},
                {code: 'MT', name: 'Malta'},
                {code: 'MH', name: 'Marshall Islands'},
                {code: 'MR', name: 'Mauritania'},
                {code: 'MU', name: 'Mauritius'},
                {code: 'MX', name: 'Mexico'},
                {code: 'FM', name: 'Micronesia'},
                {code: 'MD', name: 'Moldova'},
                {code: 'MC', name: 'Monaco'},
                {code: 'MN', name: 'Mongolia'},
                {code: 'ME', name: 'Montenegro'},
                {code: 'MA', name: 'Morocco'},
                {code: 'MZ', name: 'Mozambique'},
                {code: 'MM', name: 'Myanmar'},
                {code: 'NA', name: 'Namibia'},
                {code: 'NR', name: 'Nauru'},
                {code: 'NP', name: 'Nepal'},
                {code: 'NL', name: 'Netherlands'},
                {code: 'NZ', name: 'New Zealand'},
                {code: 'NI', name: 'Nicaragua'},
                {code: 'NE', name: 'Niger'},
                {code: 'NG', name: 'Nigeria'},
                {code: 'NO', name: 'Norway'},
                {code: 'OM', name: 'Oman'},
                {code: 'PK', name: 'Pakistan'},
                {code: 'PW', name: 'Palau'},
                {code: 'PS', name: 'Palestine'},
                {code: 'PA', name: 'Panama'},
                {code: 'PG', name: 'Papua New Guinea'},
                {code: 'PY', name: 'Paraguay'},
                {code: 'PE', name: 'Peru'},
                {code: 'PH', name: 'Philippines'},
                {code: 'PL', name: 'Poland'},
                {code: 'PT', name: 'Portugal'},
                {code: 'QA', name: 'Qatar'},
                {code: 'RO', name: 'Romania'},
                {code: 'RU', name: 'Russia'},
                {code: 'RW', name: 'Rwanda'},
                {code: 'WS', name: 'Samoa'},
                {code: 'SM', name: 'San Marino'},
                {code: 'ST', name: 'São Tomé and Príncipe'},
                {code: 'SA', name: 'Saudi Arabia'},
                {code: 'SN', name: 'Senegal'},
                {code: 'RS', name: 'Serbia'},
                {code: 'SC', name: 'Seychelles'},
                {code: 'SL', name: 'Sierra Leone'},
                {code: 'SG', name: 'Singapore'},
                {code: 'SK', name: 'Slovakia'},
                {code: 'SI', name: 'Slovenia'},
                {code: 'SB', name: 'Solomon Islands'},
                {code: 'SO', name: 'Somalia'},
                {code: 'ZA', name: 'South Africa'},
                {code: 'SS', name: 'South Sudan'},
                {code: 'ES', name: 'Spain'},
                {code: 'LK', name: 'Sri Lanka'},
                {code: 'SD', name: 'Sudan'},
                {code: 'SR', name: 'Suriname'},
                {code: 'SZ', name: 'Eswatini'},
                {code: 'SE', name: 'Sweden'},
                {code: 'CH', name: 'Switzerland'},
                {code: 'SY', name: 'Syria'},
                {code: 'TW', name: 'Taiwan'},
                {code: 'TJ', name: 'Tajikistan'},
                {code: 'TZ', name: 'Tanzania'},
                {code: 'TH', name: 'Thailand'},
                {code: 'TL', name: 'Timor-Leste'},
                {code: 'TG', name: 'Togo'},
                {code: 'TO', name: 'Tonga'},
                {code: 'TT', name: 'Trinidad and Tobago'},
                {code: 'TN', name: 'Tunisia'},
                {code: 'TR', name: 'Turkey'},
                {code: 'TM', name: 'Turkmenistan'},
                {code: 'TV', name: 'Tuvalu'},
                {code: 'UG', name: 'Uganda'},
                {code: 'UA', name: 'Ukraine'},
                {code: 'AE', name: 'United Arab Emirates'},
                {code: 'GB', name: 'United Kingdom'},
                {code: 'US', name: 'United States'},
                {code: 'UY', name: 'Uruguay'},
                {code: 'UZ', name: 'Uzbekistan'},
                {code: 'VU', name: 'Vanuatu'},
                {code: 'VA', name: 'Vatican City'},
                {code: 'VE', name: 'Venezuela'},
                {code: 'VN', name: 'Vietnam'},
                {code: 'YE', name: 'Yemen'},
                {code: 'ZM', name: 'Zambia'},
                {code: 'ZW', name: 'Zimbabwe'}
            ];

            // Create wrapper and dropdown elements
            const wrapper = document.createElement('div');
            wrapper.className = 'custom-searchable-select';

            countryInput.parentNode.insertBefore(wrapper, countryInput);
            wrapper.appendChild(countryInput);

            // Create dropdown arrow
            const arrow = document.createElement('i');
            arrow.className = 'fas fa-chevron-down dropdown-arrow';
            wrapper.appendChild(arrow);

            // Create dropdown list
            const dropdownList = document.createElement('div');
            dropdownList.className = 'dropdown-list';
            wrapper.appendChild(dropdownList);

            // Remove readonly and add event listeners
            countryInput.removeAttribute('readonly');

            let selectedCountry = '';
            let filteredCountries = countries.slice(1); // Remove empty option
            let highlightedIndex = -1;

            // Render dropdown items
            function renderDropdown(countriesToShow) {
                dropdownList.innerHTML = '';
                if (countriesToShow.length === 0) {
                    const noResults = document.createElement('div');
                    noResults.className = 'no-results';
                    noResults.textContent = 'No countries found';
                    dropdownList.appendChild(noResults);
                    return;
                }

                countriesToShow.forEach((country, index) => {
                    const item = document.createElement('div');
                    item.className = 'dropdown-item';
                    item.textContent = country.name;
                    item.dataset.code = country.code;
                    item.dataset.name = country.name;

                    if (index === highlightedIndex) {
                        item.classList.add('highlighted');
                        // Scroll to highlighted item
                        setTimeout(() => {
                            item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                        }, 0);
                    }

                    item.addEventListener('click', () => {
                        selectCountry(country.name, country.code);
                    });

                    dropdownList.appendChild(item);
                });
            }

            // Select a country
            function selectCountry(name, code) {
                countryInput.value = name;
                selectedCountry = name;
                hideDropdown();

                // Set the actual form value
                const hiddenInput = document.querySelector('input[name="country"]');
                if (hiddenInput && hiddenInput !== countryInput) {
                    hiddenInput.value = name;
                } else {
                    countryInput.setAttribute('name', 'country');
                }

                // Update validation state
                if (name) {
                    countryInput.classList.remove('is-invalid');
                    countryInput.classList.add('is-valid');
                } else if (countryInput.hasAttribute('required')) {
                    countryInput.classList.add('is-invalid');
                    countryInput.classList.remove('is-valid');
                }
            }

            // Show dropdown
            function showDropdown() {
                dropdownList.classList.add('show');
                arrow.classList.add('open');
                highlightedIndex = -1; // Reset highlight when showing
                renderDropdown(filteredCountries);
            }

            // Hide dropdown
            function hideDropdown() {
                dropdownList.classList.remove('show');
                arrow.classList.remove('open');
                highlightedIndex = -1;
            }

            // Filter countries based on input
            function filterCountries(query) {
                if (!query) {
                    filteredCountries = countries.slice(1);
                } else {
                    filteredCountries = countries.filter(country =>
                        country.name.toLowerCase().includes(query.toLowerCase()) &&
                        country.name !== ''
                    );
                }
                highlightedIndex = -1;
                renderDropdown(filteredCountries);
            }

            // Event listeners
            countryInput.addEventListener('focus', () => {
                showDropdown();
            });

            countryInput.addEventListener('input', (e) => {
                const query = e.target.value;
                if (query !== selectedCountry) {
                    selectedCountry = '';
                }
                filterCountries(query);
                showDropdown();
            });

            countryInput.addEventListener('keydown', (e) => {
                if (!dropdownList.classList.contains('show')) return;

                switch (e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        if (filteredCountries.length === 0) return;
                        highlightedIndex = highlightedIndex < filteredCountries.length - 1 ? highlightedIndex + 1 : 0;
                        renderDropdown(filteredCountries);
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        if (filteredCountries.length === 0) return;
                        highlightedIndex = highlightedIndex > 0 ? highlightedIndex - 1 : filteredCountries.length - 1;
                        renderDropdown(filteredCountries);
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (highlightedIndex >= 0 && filteredCountries[highlightedIndex]) {
                            selectCountry(filteredCountries[highlightedIndex].name, filteredCountries[highlightedIndex].code);
                        }
                        break;
                    case 'Escape':
                        e.preventDefault();
                        hideDropdown();
                        countryInput.blur();
                        break;
                }
            });

            // Click outside to close
            document.addEventListener('click', (e) => {
                if (!wrapper.contains(e.target)) {
                    hideDropdown();
                }
            });

            console.log('Custom country dropdown initialized successfully!');
        }
    });

// Quick Add Form Functionality (consolidated from quick_add.js)
document.addEventListener('DOMContentLoaded', function() {
    // Form validation for quick add forms
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Initialize Select2 for dropdowns (if available)
    if (typeof $ !== 'undefined' && $.fn.select2) {
        $('.form-select').select2({
            theme: 'bootstrap',
            width: '100%'
        });
    }

    // Add loading state to submit buttons
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        if (submitBtn.length) {
            submitBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>Adding...').prop('disabled', true);
        }
    });

    // Quick add specific functionality
    const quickAddForm = document.getElementById('quickAddForm');
    if (quickAddForm) {
        quickAddForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adding Patient...';

            // Submit via AJAX if HTMX is available, otherwise regular submit
            if (typeof htmx !== 'undefined') {
                // Let HTMX handle it
                return true;
            } else {
                // Manual AJAX submission
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        showNotification('Patient added successfully!', 'success');
                        // Reset form
                        this.reset();
                        // Close modal if in modal
                        const modal = this.closest('.modal');
                        if (modal) {
                            const bsModal = bootstrap.Modal.getInstance(modal);
                            if (bsModal) bsModal.hide();
                        }
                        // Refresh patient list if on list page
                        if (typeof dataTable !== 'undefined' && dataTable) {
                            dataTable.ajax.reload();
                        }
                    } else {
                        showNotification(data.message || 'Error adding patient', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification('Error adding patient', 'error');
                })
                .finally(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Add Patient';
                });
            }
        });
    }
});
