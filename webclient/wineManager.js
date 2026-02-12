// Wine Management Module
import { WineInstance } from './models/WineInstance.js';
import { WineReference } from './models/WineReference.js';
import { API } from './api.js';
import { Cellar } from './models/Cellar.js';
import { findInstanceLocation } from './utils/locationUtils.js';

class WineManager {
    constructor() {
        this.wineInstances = [];
        this.wineReferences = [];
        this.cellars = [];
        this.filteredInstances = [];
        this.currentFilters = {
            wineTypes: [],
            varietals: [],
            countries: [],
            showConsumed: false,
            showUnshelved: true,
            showShelved: true,
            showCoravined: false,
            searchText: '',
            sortBy: 'name',
            sortOrder: 'asc'
        };
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Filter button
        const filterBtn = document.getElementById('wines-filter-btn');
        if (filterBtn) {
            filterBtn.addEventListener('click', () => this.toggleFilterPanel());
        }

        // Filter panel interactions
        this.setupFilterListeners();

        // Set up live filter updates (no apply button needed)
        this.setupLiveFilters();
        
        // Reset filters button
        const resetFiltersBtn = document.getElementById('reset-filters-btn');
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', () => this.resetFilters());
        }
    }

    setupFilterListeners() {
        // Wine type dropdown
        const wineTypeToggle = document.getElementById('wine-type-toggle');
        const wineTypeMenu = document.getElementById('wine-type-menu');
        if (wineTypeToggle && wineTypeMenu) {
            wineTypeToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const dropdown = wineTypeToggle.closest('.filter-dropdown');
                const isActive = dropdown.classList.contains('active');
                
                // Close all other dropdowns first
                document.querySelectorAll('.filter-dropdown').forEach(d => {
                    if (d !== dropdown) {
                        d.classList.remove('active');
                    }
                });
                
                // Toggle this dropdown
                dropdown.classList.toggle('active');
            });
        }

        // Varietal dropdown
        const varietalToggle = document.getElementById('varietal-toggle');
        const varietalMenu = document.getElementById('varietal-menu');
        if (varietalToggle && varietalMenu) {
            varietalToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const dropdown = varietalToggle.closest('.filter-dropdown');
                const isActive = dropdown.classList.contains('active');
                
                // Close all other dropdowns first
                document.querySelectorAll('.filter-dropdown').forEach(d => {
                    if (d !== dropdown) {
                        d.classList.remove('active');
                    }
                });
                
                // Toggle this dropdown
                dropdown.classList.toggle('active');
            });
        }

        // Country dropdown
        const countryToggle = document.getElementById('country-toggle');
        const countryMenu = document.getElementById('country-menu');
        if (countryToggle && countryMenu) {
            countryToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const dropdown = countryToggle.closest('.filter-dropdown');
                const isActive = dropdown.classList.contains('active');
                
                // Close all other dropdowns first
                document.querySelectorAll('.filter-dropdown').forEach(d => {
                    if (d !== dropdown) {
                        d.classList.remove('active');
                    }
                });
                
                // Toggle this dropdown
                dropdown.classList.toggle('active');
            });
        }

        // Sort select dropdown
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                this.applyFilters();
            });
        }

        // Sort order button
        const sortOrderBtn = document.getElementById('sort-order-btn');
        const sortOrderIcon = sortOrderBtn ? sortOrderBtn.querySelector('.sort-order-icon') : null;
        if (sortOrderBtn && sortOrderIcon) {
            // Initialize sort order button state
            sortOrderBtn.classList.add('ascending');
            sortOrderIcon.textContent = '▲';
            
            sortOrderBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isAscending = sortOrderBtn.classList.contains('ascending');
                if (isAscending) {
                    sortOrderBtn.classList.remove('ascending');
                    sortOrderBtn.classList.add('descending');
                    sortOrderIcon.textContent = '▼';
                } else {
                    sortOrderBtn.classList.remove('descending');
                    sortOrderBtn.classList.add('ascending');
                    sortOrderIcon.textContent = '▲';
                }
                this.applyFilters();
            });
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.filter-dropdown')) {
                document.querySelectorAll('.filter-dropdown').forEach(dropdown => {
                    dropdown.classList.remove('active');
                });
            }
        });
    }

    setupLiveFilters() {
        // Listen for checkbox changes (wine type and varietal)
        document.addEventListener('change', (e) => {
            // Handle "Select all" checkbox changes
            if (e.target.id === 'filter-type-select-all') {
                const isChecked = e.target.checked;
                document.querySelectorAll('#wine-type-menu input[type="checkbox"][data-filter="wineType"]').forEach(cb => {
                    cb.checked = isChecked;
                });
                this.updateSelectAllState('wine-type');
                this.updateFilterLabels();
                this.applyFilters();
            } else if (e.target.id === 'filter-varietal-select-all') {
                const isChecked = e.target.checked;
                document.querySelectorAll('#varietal-menu input[type="checkbox"][data-filter="varietal"]').forEach(cb => {
                    cb.checked = isChecked;
                });
                this.updateSelectAllState('varietal');
                this.updateFilterLabels();
                this.applyFilters();
            } else if (e.target.id === 'filter-country-select-all') {
                const isChecked = e.target.checked;
                document.querySelectorAll('#country-menu input[type="checkbox"][data-filter="country"]').forEach(cb => {
                    cb.checked = isChecked;
                });
                this.updateSelectAllState('country');
                this.updateFilterLabels();
                this.applyFilters();
            } else if (e.target.matches('#wine-type-menu input[type="checkbox"][data-filter="wineType"]')) {
                this.updateSelectAllState('wine-type');
                this.updateFilterLabels();
                this.applyFilters();
            } else if (e.target.matches('#varietal-menu input[type="checkbox"][data-filter="varietal"]')) {
                this.updateSelectAllState('varietal');
                this.updateFilterLabels();
                this.applyFilters();
            } else if (e.target.matches('#country-menu input[type="checkbox"][data-filter="country"]')) {
                this.updateSelectAllState('country');
                this.updateFilterLabels();
                this.applyFilters();
            } else if (e.target.matches('#filter-consumed') ||
                       e.target.matches('#filter-unshelved') ||
                       e.target.matches('#filter-shelved') ||
                       e.target.matches('#filter-coravined')) {
                this.applyFilters();
            }
        });

        // Listen for search input changes (with debounce)
        let searchTimeout;
        const searchInput = document.getElementById('filter-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.applyFilters();
                }, 300); // 300ms debounce
            });
        }
    }

    async loadWines(searchTerm = null) {
        try {
            const [instancesData, globalRefsData, userRefsData, cellarsData] = await Promise.all([
                API.get('/wine-instances'),
                API.get('/wine-references'),
                API.get('/user-wine-references'),
                API.get('/cellars')
            ]);

            // Build global reference map (keyed by GlobalWineReference ID)
            const globalRefsMap = {};
            globalRefsData.forEach(refData => {
                globalRefsMap[refData.id] = refData;
            });

            // Build merged WineReference objects from UserWineReference + GlobalWineReference
            // Keyed by UserWineReference ID for instance resolution
            const referencesMap = {};
            this.wineReferences = userRefsData.map(userRefData => {
                const globalRefData = globalRefsMap[userRefData.globalReferenceId];
                if (!globalRefData) return null;
                const mergedData = {
                    ...globalRefData,
                    userReferenceId: userRefData.id,
                    rating: userRefData.rating,
                    tastingNotes: userRefData.tastingNotes
                };
                const ref = WineReference.fromDict(mergedData);
                referencesMap[userRefData.id] = ref;
                return ref;
            }).filter(r => r !== null);

            // Create cellar map
            this.cellars = cellarsData.map(cellarData => Cellar.fromDict(cellarData));

            // Create wine instances (referenceId is now a UserWineReference ID)
            this.wineInstances = instancesData.map(instData => {
                const reference = referencesMap[instData.referenceId];
                if (!reference) {
                    console.warn('Reference not found for instance:', instData.id);
                    return null;
                }
                return WineInstance.fromDict(instData, reference);
            }).filter(inst => inst !== null);

            // Populate filter dropdowns
            this.populateFilters();
            
            // Update filter labels after populating
            this.updateFilterLabels();

            // If search term provided, set it
            if (searchTerm) {
                const searchInput = document.getElementById('filter-search');
                if (searchInput) {
                    searchInput.value = searchTerm;
                }
                this.currentFilters.searchText = searchTerm;
            }
            
            // Always expand filter panel when loading wines view
            this.showFilterPanel();

            // Apply current filters and render
            this.applyFilters();
        } catch (error) {
            console.error('Error loading wines:', error);
            const winesList = document.getElementById('wines-list');
            if (winesList) {
                winesList.innerHTML = `<p style="text-align: center; color: #f44336; padding: 40px;">Failed to load wines: ${error.message || 'Unknown error'}</p>`;
            }
        }
    }

    showFilterPanel() {
        const filterPanel = document.getElementById('wines-filter-panel');
        const filterIcon = document.querySelector('.filter-icon-img.filter-icon');
        const arrowIcon = document.querySelector('.filter-arrow-icon');
        
        if (filterPanel && filterPanel.classList.contains('hidden')) {
            filterPanel.classList.remove('hidden');
            if (filterIcon) filterIcon.classList.add('hidden');
            if (arrowIcon) arrowIcon.classList.remove('hidden');
        }
    }

    populateFilters() {
        // Get unique wine types
        const wineTypesArray = Array.from(new Set(
            this.wineReferences
                .map(ref => ref.type)
                .filter(type => type)
        )).sort();

        // Get unique varietals
        const varietalsArray = Array.from(new Set(
            this.wineReferences
                .flatMap(ref => ref.varietals || [])
                .filter(v => v)
        )).sort();

        // Get unique countries
        const countriesArray = Array.from(new Set(
            this.wineReferences
                .map(ref => ref.country)
                .filter(country => country)
        )).sort();

        // Populate wine type dropdown
        const wineTypeMenu = document.getElementById('wine-type-menu');
        if (wineTypeMenu) {
            wineTypeMenu.innerHTML = '';
            
            // Add "Select all" checkbox at the top
            const selectAllItem = document.createElement('div');
            selectAllItem.className = 'filter-checkbox-item filter-select-all';
            selectAllItem.innerHTML = `
                <input type="checkbox" id="filter-type-select-all" data-filter="wineType-select-all" checked>
                <label for="filter-type-select-all">Select all</label>
            `;
            wineTypeMenu.appendChild(selectAllItem);
            
            // Add all wine types with checked=true
            wineTypesArray.forEach(type => {
                const item = document.createElement('div');
                item.className = 'filter-checkbox-item';
                item.innerHTML = `
                    <input type="checkbox" id="filter-type-${type}" value="${this.escapeHtml(type)}" data-filter="wineType" checked>
                    <label for="filter-type-${type}">${this.escapeHtml(type)}</label>
                `;
                wineTypeMenu.appendChild(item);
            });
        }

        // Populate varietal dropdown
        const varietalMenu = document.getElementById('varietal-menu');
        if (varietalMenu) {
            varietalMenu.innerHTML = '';
            
            // Add "Select all" checkbox at the top
            const selectAllItem = document.createElement('div');
            selectAllItem.className = 'filter-checkbox-item filter-select-all';
            selectAllItem.innerHTML = `
                <input type="checkbox" id="filter-varietal-select-all" data-filter="varietal-select-all" checked>
                <label for="filter-varietal-select-all">Select all</label>
            `;
            varietalMenu.appendChild(selectAllItem);
            
            // Add all varietals with checked=true
            varietalsArray.forEach(varietal => {
                const item = document.createElement('div');
                item.className = 'filter-checkbox-item';
                item.innerHTML = `
                    <input type="checkbox" id="filter-varietal-${varietal}" value="${this.escapeHtml(varietal)}" data-filter="varietal" checked>
                    <label for="filter-varietal-${varietal}">${this.escapeHtml(varietal)}</label>
                `;
                varietalMenu.appendChild(item);
            });
        }

        // Populate country dropdown
        const countryMenu = document.getElementById('country-menu');
        if (countryMenu) {
            countryMenu.innerHTML = '';
            
            // Add "Select all" checkbox at the top
            const selectAllItem = document.createElement('div');
            selectAllItem.className = 'filter-checkbox-item filter-select-all';
            selectAllItem.innerHTML = `
                <input type="checkbox" id="filter-country-select-all" data-filter="country-select-all" checked>
                <label for="filter-country-select-all">Select all</label>
            `;
            countryMenu.appendChild(selectAllItem);
            
            // Add all countries with checked=true
            countriesArray.forEach(country => {
                const item = document.createElement('div');
                item.className = 'filter-checkbox-item';
                item.innerHTML = `
                    <input type="checkbox" id="filter-country-${country}" value="${this.escapeHtml(country)}" data-filter="country" checked>
                    <label for="filter-country-${country}">${this.escapeHtml(country)}</label>
                `;
                countryMenu.appendChild(item);
            });
        }
    }

    updateSelectAllState(filterType) {
        if (filterType === 'wine-type') {
            const allCheckboxes = Array.from(document.querySelectorAll('#wine-type-menu input[type="checkbox"][data-filter="wineType"]'));
            const selectAllCheckbox = document.getElementById('filter-type-select-all');
            if (selectAllCheckbox && allCheckboxes.length > 0) {
                const allChecked = allCheckboxes.every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
            }
        } else if (filterType === 'varietal') {
            const allCheckboxes = Array.from(document.querySelectorAll('#varietal-menu input[type="checkbox"][data-filter="varietal"]'));
            const selectAllCheckbox = document.getElementById('filter-varietal-select-all');
            if (selectAllCheckbox && allCheckboxes.length > 0) {
                const allChecked = allCheckboxes.every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
            }
        } else if (filterType === 'country') {
            const allCheckboxes = Array.from(document.querySelectorAll('#country-menu input[type="checkbox"][data-filter="country"]'));
            const selectAllCheckbox = document.getElementById('filter-country-select-all');
            if (selectAllCheckbox && allCheckboxes.length > 0) {
                const allChecked = allCheckboxes.every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
            }
        }
    }

    toggleFilterPanel() {
        const filterPanel = document.getElementById('wines-filter-panel');
        const filterIcon = document.querySelector('.filter-icon-img.filter-icon');
        const arrowIcon = document.querySelector('.filter-arrow-icon');
        
        if (filterPanel) {
            const isHidden = filterPanel.classList.contains('hidden');
            
            if (isHidden) {
                // Opening panel - show arrow, hide filter icon
                filterPanel.classList.remove('hidden');
                if (filterIcon) filterIcon.classList.add('hidden');
                if (arrowIcon) arrowIcon.classList.remove('hidden');
            } else {
                // Closing panel - show filter icon, hide arrow
                filterPanel.classList.add('hidden');
                if (filterIcon) filterIcon.classList.remove('hidden');
                if (arrowIcon) arrowIcon.classList.add('hidden');
            }
        }
    }

    hideFilterPanel() {
        const filterPanel = document.getElementById('wines-filter-panel');
        const filterIcon = document.querySelector('.filter-icon-img.filter-icon');
        const arrowIcon = document.querySelector('.filter-arrow-icon');
        
        if (filterPanel) {
            filterPanel.classList.add('hidden');
            if (filterIcon) filterIcon.classList.remove('hidden');
            if (arrowIcon) arrowIcon.classList.add('hidden');
        }
    }

    applyFilters() {
        // Collect filter values (exclude "Select all" checkboxes)
        const selectedTypes = Array.from(document.querySelectorAll('#wine-type-menu input[type="checkbox"][data-filter="wineType"]:checked'))
            .map(cb => cb.value);
        const selectedVarietals = Array.from(document.querySelectorAll('#varietal-menu input[type="checkbox"][data-filter="varietal"]:checked'))
            .map(cb => cb.value);
        const selectedCountries = Array.from(document.querySelectorAll('#country-menu input[type="checkbox"][data-filter="country"]:checked'))
            .map(cb => cb.value);
        const showConsumed = document.getElementById('filter-consumed')?.checked || false;
        const showUnshelved = document.getElementById('filter-unshelved')?.checked || false;
        const showShelved = document.getElementById('filter-shelved')?.checked || false;
        const showCoravined = document.getElementById('filter-coravined')?.checked || false;
        const searchText = (document.getElementById('filter-search')?.value || '').toLowerCase().trim();
        
        // Get sort values
        const sortSelect = document.getElementById('sort-select');
        const sortBy = sortSelect ? sortSelect.value : 'name';
        const sortOrderBtn = document.getElementById('sort-order-btn');
        const sortOrder = sortOrderBtn && sortOrderBtn.classList.contains('descending') ? 'desc' : 'asc';

        // Update current filters
        this.currentFilters = {
            wineTypes: selectedTypes,
            varietals: selectedVarietals,
            countries: selectedCountries,
            showConsumed,
            showUnshelved,
            showShelved,
            showCoravined,
            searchText,
            sortBy,
            sortOrder
        };

        // Filter instances using current selections
        this.filteredInstances = this.wineInstances.filter(instance => {
            // Filter by consumed/unshelved/shelved/coravined (OR logic)
            // If all checkboxes are unchecked, show no wines
            if (!showConsumed && !showUnshelved && !showShelved && !showCoravined) {
                return false;
            }
            
            let matchesAnyStatus = false;
            
            if (showConsumed && instance.consumed) {
                matchesAnyStatus = true;
            }
            
            if (showUnshelved && instance.isUnshelved(this.cellars)) {
                matchesAnyStatus = true;
            }
            
            if (showShelved && !instance.isUnshelved(this.cellars)) {
                matchesAnyStatus = true;
            }

            if (showCoravined && instance.coravined) {
                matchesAnyStatus = true;
            }
            
            // If wine doesn't match any checked status filter, exclude it
            if (!matchesAnyStatus) {
                return false;
            }

            const ref = instance.reference;

            // Filter by wine type
            // If no types selected, exclude all wines
            if (selectedTypes.length === 0) {
                return false;
            }
            // If types selected, only show matching wines
            if (!selectedTypes.includes(ref.type)) {
                return false;
            }

            // Filter by varietal
            // If no varietals selected, exclude all wines
            if (selectedVarietals.length === 0) {
                return false;
            }
            // If varietals selected, only show matching wines
            const instanceVarietals = ref.varietals || [];
            const hasMatchingVarietal = selectedVarietals.some(v => 
                instanceVarietals.includes(v)
            );
            if (!hasMatchingVarietal) {
                return false;
            }

            // Filter by country
            // If no countries selected, exclude all wines
            if (selectedCountries.length === 0) {
                return false;
            }
            // If countries selected, only show matching wines
            if (!selectedCountries.includes(ref.country)) {
                return false;
            }

            // Filter by search text (case insensitive and accent insensitive)
            if (searchText) {
                const searchableText = [
                    ref.name,
                    ref.producer,
                    ref.region,
                    ref.country,
                    ref.type,
                    ...(ref.varietals || [])
                ].join(' ').toLowerCase();
                const normalizedSearchableText = this.normalizeText(searchableText);
                const normalizedSearchText = this.normalizeText(searchText);
                if (!normalizedSearchableText.includes(normalizedSearchText)) {
                    return false;
                }
            }

            return true;
        });

        // Apply sorting
        this.filteredInstances.sort((a, b) => {
            const refA = a.reference;
            const refB = b.reference;
            let compareValue = 0;

            switch (sortBy) {
                case 'name':
                    compareValue = (refA.name || '').localeCompare(refB.name || '');
                    break;
                case 'type':
                    compareValue = (refA.type || '').localeCompare(refB.type || '');
                    break;
                case 'vintage':
                    const vintageA = refA.vintage || 0;
                    const vintageB = refB.vintage || 0;
                    compareValue = vintageA - vintageB;
                    break;
                case 'stored':
                    const storedA = a.storedDate ? new Date(a.storedDate).getTime() : 0;
                    const storedB = b.storedDate ? new Date(b.storedDate).getTime() : 0;
                    compareValue = storedA - storedB;
                    break;
                case 'drinkby':
                    const drinkByA = a.drinkByDate ? new Date(a.drinkByDate).getTime() : 0;
                    const drinkByB = b.drinkByDate ? new Date(b.drinkByDate).getTime() : 0;
                    compareValue = drinkByA - drinkByB;
                    break;
                case 'rating':
                    const ratingA = refA.rating || 0;
                    const ratingB = refB.rating || 0;
                    compareValue = ratingA - ratingB;
                    break;
                default:
                    compareValue = 0;
            }

            return sortOrder === 'desc' ? -compareValue : compareValue;
        });

        // Update filter labels
        this.updateFilterLabels();

        // Render filtered list
        this.renderWines();
    }

    updateFilterLabels() {
        // Get all available options
        const allWineTypes = Array.from(document.querySelectorAll('#wine-type-menu input[type="checkbox"][data-filter="wineType"]')).map(cb => cb.value);
        const allVarietals = Array.from(document.querySelectorAll('#varietal-menu input[type="checkbox"][data-filter="varietal"]')).map(cb => cb.value);
        const allCountries = Array.from(document.querySelectorAll('#country-menu input[type="checkbox"][data-filter="country"]')).map(cb => cb.value);
        
        // Get selected counts from current filters
        const selectedTypesCount = this.currentFilters.wineTypes.length;
        const selectedVarietalsCount = this.currentFilters.varietals.length;
        const selectedCountriesCount = this.currentFilters.countries.length;
        
        // Update wine type label
        const wineTypeSelected = document.getElementById('wine-type-selected');
        if (wineTypeSelected) {
            if (selectedTypesCount === 0) {
                wineTypeSelected.textContent = '0 selected';
            } else if (selectedTypesCount === allWineTypes.length) {
                wineTypeSelected.textContent = 'All Types';
            } else {
                wineTypeSelected.textContent = `${selectedTypesCount} selected`;
            }
        }

        // Update country label
        const countrySelected = document.getElementById('country-selected');
        if (countrySelected) {
            if (selectedCountriesCount === 0) {
                countrySelected.textContent = '0 selected';
            } else if (selectedCountriesCount === allCountries.length) {
                countrySelected.textContent = 'All Countries';
            } else {
                countrySelected.textContent = `${selectedCountriesCount} selected`;
            }
        }

        // Update varietal label
        const varietalSelected = document.getElementById('varietal-selected');
        if (varietalSelected) {
            if (selectedVarietalsCount === 0) {
                varietalSelected.textContent = '0 selected';
            } else if (selectedVarietalsCount === allVarietals.length) {
                varietalSelected.textContent = 'All Varietals';
            } else {
                varietalSelected.textContent = `${selectedVarietalsCount} selected`;
            }
        }
    }

    uncheckInvalidSelections() {
        // Removed - filters are now independent and don't uncheck each other
        // Wine Type and Varietal selections don't impact each other
        // Status filters (Shelved/Unshelved/Consumed) don't impact Wine Type or Varietal
    }

    resetFilters() {
        // Reset wine type checkboxes - check all
        document.querySelectorAll('#wine-type-menu input[type="checkbox"][data-filter="wineType"]').forEach(cb => {
            cb.checked = true;
        });
        const wineTypeSelectAll = document.getElementById('filter-type-select-all');
        if (wineTypeSelectAll) {
            wineTypeSelectAll.checked = true;
        }
        
        // Reset country checkboxes - check all
        document.querySelectorAll('#country-menu input[type="checkbox"][data-filter="country"]').forEach(cb => {
            cb.checked = true;
        });
        const countrySelectAll = document.getElementById('filter-country-select-all');
        if (countrySelectAll) {
            countrySelectAll.checked = true;
        }
        
        // Reset varietal checkboxes - check all
        document.querySelectorAll('#varietal-menu input[type="checkbox"][data-filter="varietal"]').forEach(cb => {
            cb.checked = true;
        });
        const varietalSelectAll = document.getElementById('filter-varietal-select-all');
        if (varietalSelectAll) {
            varietalSelectAll.checked = true;
        }
        
        // Reset sort to Name
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.value = 'name';
        }
        
        // Reset sort order to ascending
        const sortOrderBtn = document.getElementById('sort-order-btn');
        const sortOrderIcon = sortOrderBtn ? sortOrderBtn.querySelector('.sort-order-icon') : null;
        if (sortOrderBtn) {
            sortOrderBtn.classList.remove('descending');
            sortOrderBtn.classList.add('ascending');
            if (sortOrderIcon) {
                sortOrderIcon.textContent = '▲';
            }
        }
        
        // Update filter labels
        this.updateFilterLabels();
        
        // Reset consumed checkbox - uncheck
        const consumedCheckbox = document.getElementById('filter-consumed');
        if (consumedCheckbox) {
            consumedCheckbox.checked = false;
        }
        
        // Reset unshelved checkbox - check (default on)
        const unshelvedCheckbox = document.getElementById('filter-unshelved');
        if (unshelvedCheckbox) {
            unshelvedCheckbox.checked = true;
        }
        
        // Reset shelved checkbox - check (default on)
        const shelvedCheckbox = document.getElementById('filter-shelved');
        if (shelvedCheckbox) {
            shelvedCheckbox.checked = true;
        }

        // Reset coravined checkbox - unchecked (default off)
        const coravinedCheckbox = document.getElementById('filter-coravined');
        if (coravinedCheckbox) {
            coravinedCheckbox.checked = false;
        }
        
        // Clear search text
        const searchInput = document.getElementById('filter-search');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Apply the reset filters
        this.applyFilters();
    }


    updateSelectAllState(filterType) {
        if (filterType === 'wine-type') {
            const allCheckboxes = Array.from(document.querySelectorAll('#wine-type-menu input[type="checkbox"][data-filter="wineType"]'));
            const selectAllCheckbox = document.getElementById('filter-type-select-all');
            if (selectAllCheckbox && allCheckboxes.length > 0) {
                const allChecked = allCheckboxes.every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                // Ensure "Select all" is never disabled or grayed out
                selectAllCheckbox.disabled = false;
                const selectAllLabel = selectAllCheckbox.nextElementSibling;
                if (selectAllLabel) {
                    selectAllLabel.classList.remove('filter-disabled');
                }
            }
        } else if (filterType === 'varietal') {
            const allCheckboxes = Array.from(document.querySelectorAll('#varietal-menu input[type="checkbox"][data-filter="varietal"]'));
            const selectAllCheckbox = document.getElementById('filter-varietal-select-all');
            if (selectAllCheckbox && allCheckboxes.length > 0) {
                const allChecked = allCheckboxes.every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                // Ensure "Select all" is never disabled or grayed out
                selectAllCheckbox.disabled = false;
                const selectAllLabel = selectAllCheckbox.nextElementSibling;
                if (selectAllLabel) {
                    selectAllLabel.classList.remove('filter-disabled');
                }
            }
        } else if (filterType === 'country') {
            const allCheckboxes = Array.from(document.querySelectorAll('#country-menu input[type="checkbox"][data-filter="country"]'));
            const selectAllCheckbox = document.getElementById('filter-country-select-all');
            if (selectAllCheckbox && allCheckboxes.length > 0) {
                const allChecked = allCheckboxes.every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                // Ensure "Select all" is never disabled or grayed out
                selectAllCheckbox.disabled = false;
                const selectAllLabel = selectAllCheckbox.nextElementSibling;
                if (selectAllLabel) {
                    selectAllLabel.classList.remove('filter-disabled');
                }
            }
        }
    }

    renderWines() {
        const winesList = document.getElementById('wines-list');
        if (!winesList) return;

        if (this.filteredInstances.length === 0) {
            winesList.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">No wines matching filters</p>';
            return;
        }
        
        winesList.innerHTML = this.filteredInstances.map(instance => {
            const ref = instance.reference;
            
            // Find location
            const locationInfo = findInstanceLocation(instance, this.cellars);
            
            // Count bottles stored for this reference
            const bottlesStored = this.countBottlesStored(ref.id);
            
            // Count other bottles (excluding this instance if not consumed)
            const otherBottlesCount = bottlesStored > 0 && !instance.consumed ? bottlesStored - 1 : bottlesStored;
            
            // Format location string
            let locationStr = 'Unshelved';
            if (locationInfo) {
                const { cellar, shelfIndex, side, position } = locationInfo;
                const sideDisplay = side === 'single' ? '' : side === 'front' ? 'Front' : 'Back';
                const sideText = sideDisplay ? `, ${sideDisplay}` : '';
                locationStr = `${cellar.name}, Shelf ${shelfIndex + 1}${sideText}, Position ${position + 1}`;
            }
            
            // Get country flag
            const flag = this.getCountryFlag(ref.country);
            
            // Format wine type
            const wineTypeDisplay = ref.type ? `${ref.type} Wine` : '';
            
            // Format region and country
            const regionText = ref.region ? `${ref.region}, ` : '';
            const countryText = ref.country ? `${this.escapeHtml(ref.country)}` : '';

            return `
                <div class="wine-item" data-instance-id="${instance.id}">
                    <div class="wine-item-image">
                        ${ref.labelImageUrl ? 
                            `<img src="${this.escapeHtml(ref.labelImageUrl)}" alt="${this.escapeHtml(ref.name)}" />` :
                            '<div class="wine-item-placeholder">🍷</div>'
                        }
                    </div>
                    <div class="wine-item-details">
                        <div class="wine-item-meta">
                            ${ref.vintage ? `<span class="wine-item-vintage">${ref.vintage}</span>` : ''}
                            <span class="wine-item-title">${this.escapeHtml(ref.name)}</span>
                        </div>
                        ${ref.producer ? `<div class="wine-item-producer">${this.escapeHtml(ref.producer)}</div>` : ''}
                        <div class="wine-item-country-info">
                            ${flag ? `<span class="wine-item-flag">${flag}</span> ` : ''}
                            ${wineTypeDisplay ? `${this.escapeHtml(wineTypeDisplay)}` : ''}
                            ${(ref.region || ref.country) ? ` • ${regionText}${countryText}` : ''}
                        </div>
                        <div class="wine-item-storage">
                            <span class="wine-item-storage-label">Stored: </span><span>${instance.storedDate ? this.formatStoredDate(instance.storedDate) : 'N/A'}${otherBottlesCount > 0 ? ',' : ''}</span>
                            ${otherBottlesCount > 0 ? `<span>${otherBottlesCount} additional bottle${otherBottlesCount !== 1 ? 's' : ''} owned</span>` : ''}
                        </div>
                        ${instance.coravined && instance.coravinedDate ? `<div class="wine-item-coravined"><span class="wine-item-storage-label">Coravined: </span><span>${this.formatStoredDate(instance.coravinedDate)}</span></div>` : ''}
                        ${instance.consumed && instance.consumedDate ? `<div class="wine-item-consumed"><span class="wine-item-storage-label">Consumed: </span><span>${this.formatStoredDate(instance.consumedDate)}</span></div>` : ''}
                        ${!instance.consumed ? `<div class="wine-item-location">
                            <span class="wine-item-location-label">Location: </span>${this.escapeHtml(locationStr)}
                        </div>` : ''}
                        <div class="wine-item-rating" data-reference-id="${ref.id}">
                            <span class="wine-item-rating-label">Rating: </span>
                            <span class="wine-item-rating-stars">
                                ${[1, 2, 3, 4, 5].map(star => 
                                    `<span class="rating-star ${star <= (ref.rating || 0) ? 'filled' : ''}" 
                                          data-rating="${star}" 
                                          data-reference-id="${ref.id}"
                                          title="Rate ${star} star${star !== 1 ? 's' : ''}">★</span>`
                                ).join('')}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Set up click handlers to open wine detail modal
        this.setupWineItemClickHandlers();
        
        // Set up rating star click handlers AFTER wine item handlers
        // (setupWineItemClickHandlers clones nodes, so we need to attach handlers after)
        this.setupRatingStarHandlers();
    }
    
    setupWineItemClickHandlers() {
        const wineItems = document.querySelectorAll('.wine-item');
        wineItems.forEach(item => {
            // Remove existing listeners by cloning
            const newItem = item.cloneNode(true);
            item.parentNode.replaceChild(newItem, item);
            
            newItem.addEventListener('click', (e) => {
                // Don't open modal if clicking on rating stars
                if (e.target.closest('.rating-star')) {
                    return;
                }
                
                const instanceId = newItem.getAttribute('data-instance-id');
                if (!instanceId) return;
                
                const instance = this.wineInstances.find(inst => inst.id === instanceId);
                if (instance && instance.reference) {
                    // Dynamically import and show wine detail view
                    import('./wineDetailView.js').then(({ getWineDetailView }) => {
                        const wineDetailView = getWineDetailView();
                        wineDetailView.show(instance.reference, instance);
                    }).catch(error => {
                        console.error('Error loading wine detail view:', error);
                    });
                }
            });
        });
    }
    
    setupRatingStarHandlers() {
        const winesList = document.getElementById('wines-list');
        if (!winesList) return;
        
        const ratingStars = winesList.querySelectorAll('.rating-star');
        ratingStars.forEach(star => {
            star.addEventListener('click', async (e) => {
                e.stopPropagation();
                const rating = parseInt(star.getAttribute('data-rating'));
                const referenceId = star.getAttribute('data-reference-id');
                
                if (!referenceId || !rating) return;
                
                try {
                    // Find reference to get userReferenceId for API call
                    const reference = this.wineReferences.find(ref => ref.id === referenceId);
                    if (!reference || !reference.userReferenceId) return;

                    // Update rating via UserWineReference API
                    await API.updateUserWineReference(reference.userReferenceId, { rating });

                    // Update local reference object
                    reference.rating = rating;

                    // Update all instances that use this reference
                    this.wineInstances.forEach(inst => {
                        if (inst.reference && inst.reference.id === referenceId) {
                            inst.reference.rating = rating;
                        }
                    });
                    
                    // Re-render to show updated stars
                    this.renderWines();
                } catch (error) {
                    console.error('Error updating rating:', error);
                    alert(`Failed to update rating: ${error.message || 'Unknown error'}`);
                }
            });
        });
    }

    normalizeText(text) {
        /**
         * Normalize text by removing diacritics/accents and converting to lowercase
         * e.g., "Café" becomes "cafe", "Résumé" becomes "resume"
         */
        return text
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase();
    }

    getCountryFlag(country) {
        /**
         * Get country flag emoji from country name
         * Uses a mapping of common country names to flag emojis
         */
        if (!country) return '';
        
        const countryMap = {
            'United States': '🇺🇸',
            'US': '🇺🇸',
            'USA': '🇺🇸',
            'U.S.A.': '🇺🇸',
            'France': '🇫🇷',
            'Italy': '🇮🇹',
            'Spain': '🇪🇸',
            'Australia': '🇦🇺',
            'Chile': '🇨🇱',
            'Argentina': '🇦🇷',
            'Germany': '🇩🇪',
            'Portugal': '🇵🇹',
            'South Africa': '🇿🇦',
            'New Zealand': '🇳🇿',
            'Canada': '🇨🇦',
            'Greece': '🇬🇷',
            'Austria': '🇦🇹',
            'Hungary': '🇭🇺',
            'Romania': '🇷🇴',
            'Bulgaria': '🇧🇬',
            'Croatia': '🇭🇷',
            'Slovenia': '🇸🇮',
            'Georgia': '🇬🇪',
            'Lebanon': '🇱🇧',
            'Israel': '🇮🇱',
            'Turkey': '🇹🇷',
            'Brazil': '🇧🇷',
            'Uruguay': '🇺🇾',
            'Mexico': '🇲🇽',
            'Japan': '🇯🇵',
            'China': '🇨🇳',
            'India': '🇮🇳',
            'United Kingdom': '🇬🇧',
            'UK': '🇬🇧',
            'England': '🇬🇧'
        };
        
        const normalizedCountry = country.trim();
        return countryMap[normalizedCountry] || '';
    }


    countBottlesStored(referenceId) {
        /**
         * Count how many instances of a wine reference are stored (not consumed)
         */
        return this.wineInstances.filter(inst => 
            inst.reference.id === referenceId && !inst.consumed
        ).length;
    }

    formatStoredDate(storedDate) {
        /**
         * Format stored date to readable format
         */
        if (!storedDate) return 'N/A';
        try {
            const date = new Date(storedDate);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch (e) {
            return storedDate;
        }
    }

    escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

export { WineManager };
