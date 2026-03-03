// Cellar Management Module
import { Cellar } from './models/Cellar.js';
import { API } from './api.js';
import { getWineCard } from './WineCard.js';
import { findInstanceLocationInCellar } from './utils/locationUtils.js';

class CellarManager {
    constructor() {
        this.cellars = [];
        this.wineInstances = []; // Cache wine instances for breakdown calculation
        this.wineReferences = []; // Cache wine references for breakdown calculation
        this.userRefToGlobalRefId = {}; // Map user wine reference IDs to global reference IDs
        this.showLabels = true; // Toggle state for labels vs vintage view
        this.currentCellar = null; // Store current cellar data for re-rendering
        this.currentInstanceMap = null;
        this.currentReferenceMap = null;
        this.panelClickHandler = null; // Store handler reference for cleanup
        this.init();
    }

    init() {
        this.setupEventListeners();
        // Don't load cellars immediately - wait until the view is shown
        // this.loadCellars();
    }

    setupEventListeners() {
        // Add cellar button
        const addBtn = document.getElementById('add-cellar-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showCreateDialog());
        }

        // Add shelf button
        const addShelfBtn = document.getElementById('add-shelf-btn');
        if (addShelfBtn) {
            addShelfBtn.addEventListener('click', () => this.addShelfInput());
        }

        // Labels toggle switch - set up when view is shown
        this.setupLabelsToggle();

        // Create dialog
        const createDialog = document.getElementById('create-cellar-dialog');
        const createForm = document.getElementById('create-cellar-form');
        const createCancelBtn = document.getElementById('create-cellar-cancel');

        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleCreate();
            });
        }

        if (createCancelBtn) {
            createCancelBtn.addEventListener('click', () => {
                this.hideCreateDialog();
            });
        }

        // Edit dialog
        const editDialog = document.getElementById('edit-cellar-dialog');
        const editForm = document.getElementById('edit-cellar-form');
        const editCancelBtn = document.getElementById('edit-cellar-cancel');

        if (editForm) {
            editForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleEdit();
            });
        }

        if (editCancelBtn) {
            editCancelBtn.addEventListener('click', () => {
                this.hideEditDialog();
            });
        }

        // Delete confirmation dialog
        const deleteDialog = document.getElementById('delete-cellar-dialog');
        const deleteConfirmBtn = document.getElementById('delete-cellar-confirm');
        const deleteCancelBtn = document.getElementById('delete-cellar-cancel');

        if (deleteConfirmBtn) {
            deleteConfirmBtn.addEventListener('click', () => {
                this.handleDelete();
            });
        }

        if (deleteCancelBtn) {
            deleteCancelBtn.addEventListener('click', () => {
                this.hideDeleteDialog();
            });
        }

        // Close dialogs when clicking overlay
        [createDialog, editDialog, deleteDialog].forEach(dialog => {
            if (dialog) {
                dialog.addEventListener('click', (e) => {
                    if (e.target === dialog) {
                        this.hideCreateDialog();
                        this.hideEditDialog();
                        this.hideDeleteDialog();
                    }
                });
            }
        });

        // Back to cellars button
        const backBtn = document.getElementById('back-to-cellars-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                if (window.app && window.app.showView) {
                    window.app.showView('cellar');
                }
            });
        }

        // Close cellar menus when clicking outside (only add once)
        // Use a timeout to ensure this runs after the button click handler
        if (!this.menuCloseListenerAttached) {
            this.menuCloseHandler = (e) => {
                // Use setTimeout to run after other click handlers
                setTimeout(() => {
                    // Don't close if clicking on menu toggle button (it will toggle itself)
                    if (e.target.closest('.cellar-menu-toggle')) {
                        return;
                    }
                    // Don't close if clicking on menu item
                    if (e.target.closest('.cellar-menu-item')) {
                        return;
                    }
                    // Don't close if clicking inside the dropdown menu
                    if (e.target.closest('.cellar-menu-dropdown')) {
                        return;
                    }
                    // Close all menus if clicking outside the menu area
                    if (!e.target.closest('.cellar-panel-menu')) {
                        document.querySelectorAll('.cellar-menu-dropdown').forEach(menu => {
                            menu.style.display = 'none';
                        });
                    }
                }, 10);
            };
            document.addEventListener('click', this.menuCloseHandler);
            this.menuCloseListenerAttached = true;
        }
    }

    setupCellarPanelListeners() {
        const container = document.getElementById('cellar-list');
        if (!container) {
            console.error('Cellar list container not found!');
            return;
        }

        // Remove old listener if it exists
        if (this.panelClickHandler) {
            container.removeEventListener('click', this.panelClickHandler);
        }

        // Create new handler using event delegation
        this.panelClickHandler = (e) => {
            // Check if clicking on menu toggle button or inside it
            let menuToggle = e.target.closest('.cellar-menu-toggle');
            // Also check if the target itself is the button
            if (!menuToggle && e.target.classList && e.target.classList.contains('cellar-menu-toggle')) {
                menuToggle = e.target;
            }
            
            if (menuToggle) {
                e.stopPropagation();
                e.preventDefault();
                const cellarId = menuToggle.getAttribute('data-cellar-id');
                if (cellarId) {
                    this.toggleCellarMenu(cellarId);
                }
                return;
            }

            // Check if clicking on menu item (Edit or Delete)
            const menuItem = e.target.closest('.cellar-menu-item');
            if (menuItem) {
                e.stopPropagation();
                e.preventDefault();
                const action = menuItem.getAttribute('data-action');
                const cellarId = menuItem.getAttribute('data-cellar-id');
                if (action && cellarId) {
                    this.hideCellarMenu(cellarId);
                    if (action === 'edit') {
                        this.showEditDialog(cellarId);
                    } else if (action === 'delete') {
                        this.showDeleteDialog(cellarId);
                    }
                }
                return;
            }

            // Check if clicking inside menu dropdown
            if (e.target.closest('.cellar-menu-dropdown')) {
                e.stopPropagation();
                return;
            }

            // Check if clicking inside menu container but not on buttons
            if (e.target.closest('.cellar-panel-menu')) {
                e.stopPropagation();
                return;
            }

            // Navigate to cellar detail when clicking on panel
            const panel = e.target.closest('.cellar-panel');
            if (panel) {
                const cellarId = panel.getAttribute('data-cellar-id');
                // Skip navigation for the unshelved wines panel
                if (cellarId && cellarId !== 'unshelved') {
                    this.showCellarDetail(cellarId);
                }
            }
        };

        // Attach new listener
        container.addEventListener('click', this.panelClickHandler);
    }

    async loadCellars() {
        try {
            console.log('Loading cellars...');
            const data = await API.get('/cellars');
            console.log('Received cellars data:', data);
            
            if (!Array.isArray(data)) {
                throw new Error(`Expected array but got ${typeof data}: ${JSON.stringify(data).substring(0, 100)}`);
            }
            
            this.cellars = data.map(c => {
                try {
                    return Cellar.fromDict(c);
                } catch (e) {
                    console.error('Error parsing cellar:', c, e);
                    throw e;
                }
            });
            console.log('Parsed cellars:', this.cellars.length);
            
            // Load wine instances, global references, and user references for breakdown calculation and preview rendering
            try {
                const [wineInstances, wineReferences, userWineReferences] = await Promise.all([
                    API.get('/wine-instances'),
                    API.get('/wine-references'),
                    API.get('/user-wine-references')
                ]);
                this.wineInstances = wineInstances;
                this.wineReferences = wineReferences;
                // Build mapping from UserWineReference ID → GlobalWineReference ID
                this.userRefToGlobalRefId = {};
                userWineReferences.forEach(userRef => {
                    this.userRefToGlobalRefId[userRef.id] = userRef.globalReferenceId;
                });
                console.log('Loaded wine instances:', wineInstances?.length, 'references:', wineReferences?.length, 'user refs:', userWineReferences?.length);
            } catch (err) {
                console.warn('Could not load wine data for breakdown:', err);
                this.wineInstances = [];
                this.wineReferences = [];
                this.userRefToGlobalRefId = {};
            }
            
            console.log('Rendering cellars...');
            this.renderCellars();
            console.log('Cellars loaded successfully');
        } catch (error) {
            console.error('Error loading cellars:', error);
            console.error('Error stack:', error.stack);
            // Don't show error alert on initial load - just log it
            // The view will show an empty state or error message
            const container = document.getElementById('cellar-list');
            if (container) {
                container.innerHTML = `<p style="text-align: center; color: #f44336; padding: 40px;">Failed to load cellars: ${error.message || 'Unknown error'}. Check console for details.</p>`;
            }
        }
    }

    /**
     * Calculate wine breakdown by type for a cellar
     * @param {Cellar} cellar - The cellar to calculate breakdown for
     * @returns {Object} Object with wine type counts, e.g. { 'Red': 10, 'White': 3 }
     */
    getWineBreakdown(cellar) {
        if (!this.wineInstances || !this.wineReferences || !cellar.winePositions) {
            return {};
        }

        // Create a map of reference ID to type for quick lookup
        const referenceTypeMap = {};
        this.wineReferences.forEach(ref => {
            referenceTypeMap[ref.id] = ref.type || 'Unknown';
        });

        // Get all wine instance IDs in this cellar
        const cellarWineIds = new Set();
        for (const shelfIndex in cellar.winePositions) {
            const shelfPositions = cellar.winePositions[shelfIndex];
            if (shelfPositions.front) {
                shelfPositions.front.forEach(id => {
                    if (id) cellarWineIds.add(id);
                });
            }
            if (shelfPositions.back) {
                shelfPositions.back.forEach(id => {
                    if (id) cellarWineIds.add(id);
                });
            }
            if (shelfPositions.single) {
                shelfPositions.single.forEach(id => {
                    if (id) cellarWineIds.add(id);
                });
            }
        }

        // Count wines by type
        const breakdown = {};
        this.wineInstances.forEach(instance => {
            // If this instance is in this cellar's winePositions
            if (cellarWineIds.has(instance.id) && instance.referenceId) {
                // instance.referenceId is a UserWineRef ID, resolve to GlobalWineRef ID
                const globalRefId = this.userRefToGlobalRefId ? this.userRefToGlobalRefId[instance.referenceId] : instance.referenceId;
                const wineType = referenceTypeMap[globalRefId] || 'Unknown';
                breakdown[wineType] = (breakdown[wineType] || 0) + 1;
            }
        });

        return breakdown;
    }

    /**
     * Format wine breakdown as a tooltip string
     * @param {Object} breakdown - Object with wine type counts
     * @returns {string} Formatted breakdown string
     */
    formatBreakdown(breakdown) {
        const entries = Object.entries(breakdown);
        if (entries.length === 0) {
            return 'No wines in cellar';
        }
        
        // Sort by count (descending) then by type name
        entries.sort((a, b) => {
            if (b[1] !== a[1]) return b[1] - a[1]; // Count descending
            return a[0].localeCompare(b[0]); // Type ascending
        });

        return entries.map(([type, count]) => {
            const plural = count === 1 ? 'bottle' : 'bottles';
            return `${count} ${type} ${plural}`;
        }).join(', ');
    }

    renderCellars() {
        const container = document.getElementById('cellar-list');
        if (!container) return;

        // Check for unshelved wines
        const unshelvedWines = this.getUnshelvedWines();
        const unshelvedHtml = this.renderUnshelvedPanel(unshelvedWines);

        if (this.cellars.length === 0 && !unshelvedHtml) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px; vertical-align: bottom;">No cellars yet. Click the + button to create one.</p>';
            return;
        }

        const cellarCardsHtml = this.cellars.map(cellar => {
            // Calculate wine breakdown for display
            const breakdown = this.getWineBreakdown(cellar);

            // Get wine label images for rotation
            const labelImages = this.getCellarLabelImages(cellar);

            // Render preview
            const previewHtml = this.renderCellarPreview(cellar, labelImages, breakdown);

            return `
                <div class="cellar-panel" data-cellar-id="${cellar.id}">
                    ${previewHtml}
                    <div class="cellar-panel-info">
                        <div class="cellar-panel-header">
                            <h3 class="cellar-panel-name">${this.escapeHtml(cellar.name || 'Unnamed Cellar')}</h3>
                            <div class="cellar-panel-menu">
                                <button class="cellar-menu-toggle" data-cellar-id="${cellar.id}" type="button" title="Menu">⋯</button>
                                <div class="cellar-menu-dropdown" id="cellar-menu-${cellar.id}" style="display: none;">
                                    <button class="cellar-menu-item" data-action="edit" data-cellar-id="${cellar.id}" type="button">
                                        <span>✏️</span>
                                        <span>Edit</span>
                                    </button>
                                    <button class="cellar-menu-item" data-action="delete" data-cellar-id="${cellar.id}" type="button">
                                        <span>🗑️</span>
                                        <span>Delete</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = unshelvedHtml + cellarCardsHtml;
        
        // Setup panel click listeners for navigation
        // Use setTimeout to ensure DOM is updated
        setTimeout(() => {
            this.setupCellarPanelListeners();
        }, 0);
        
        // Start image rotation for all previews after rendering
        setTimeout(() => {
            this.startImageRotation();
        }, 0);
    }

    getCellarLabelImages(cellar) {
        if (!this.wineInstances || !this.wineReferences || !cellar.winePositions) {
            return [];
        }

        // Create a map of reference ID to WineReference for quick lookup
        const referenceMap = {};
        this.wineReferences.forEach(ref => {
            referenceMap[ref.id] = ref;
        });

        // Collect all unique wine instance IDs in this cellar
        const cellarWineIds = new Set();
        for (const shelfIndex in cellar.winePositions) {
            const shelfPositions = cellar.winePositions[shelfIndex];
            if (shelfPositions.front) {
                shelfPositions.front.forEach(id => {
                    if (id) cellarWineIds.add(id);
                });
            }
            if (shelfPositions.back) {
                shelfPositions.back.forEach(id => {
                    if (id) cellarWineIds.add(id);
                });
            }
            if (shelfPositions.single) {
                shelfPositions.single.forEach(id => {
                    if (id) cellarWineIds.add(id);
                });
            }
        }

        // Get unique label images from wines in this cellar
        const labelImages = [];
        const seenImages = new Set();
        
        this.wineInstances.forEach(instance => {
            if (cellarWineIds.has(instance.id) && instance.referenceId) {
                // instance.referenceId is a UserWineRef ID, resolve to GlobalWineRef ID
                const globalRefId = this.userRefToGlobalRefId ? this.userRefToGlobalRefId[instance.referenceId] : instance.referenceId;
                const reference = referenceMap[globalRefId];
                if (reference && reference.labelImageUrl && !seenImages.has(reference.labelImageUrl)) {
                    labelImages.push(reference.labelImageUrl);
                    seenImages.add(reference.labelImageUrl);
                }
            }
        });

        return labelImages;
    }

    /**
     * Get all unshelved, non-consumed wine instances
     * @returns {Array} Array of unshelved wine instance objects
     */
    getUnshelvedWines() {
        if (!this.wineInstances) return [];

        // Collect all wine instance IDs that are in any cellar
        const shelvedIds = new Set();
        for (const cellar of this.cellars) {
            if (!cellar.winePositions) continue;
            for (const shelfIndex in cellar.winePositions) {
                const shelfPositions = cellar.winePositions[shelfIndex];
                for (const side of ['front', 'back', 'single']) {
                    if (shelfPositions[side]) {
                        shelfPositions[side].forEach(id => {
                            if (id) shelvedIds.add(id);
                        });
                    }
                }
            }
        }

        // Return instances that are not shelved and not consumed
        return this.wineInstances.filter(inst => !shelvedIds.has(inst.id) && !inst.consumed);
    }

    /**
     * Calculate wine breakdown by type for unshelved wines
     * @param {Array} unshelvedWines - Array of unshelved wine instances
     * @returns {Object} Object with wine type counts
     */
    getUnshelvedWineBreakdown(unshelvedWines) {
        if (!unshelvedWines || !this.wineReferences) return {};

        const referenceTypeMap = {};
        this.wineReferences.forEach(ref => {
            referenceTypeMap[ref.id] = ref.type || 'Unknown';
        });

        const breakdown = {};
        unshelvedWines.forEach(instance => {
            if (instance.referenceId) {
                const globalRefId = this.userRefToGlobalRefId ? this.userRefToGlobalRefId[instance.referenceId] : instance.referenceId;
                const wineType = referenceTypeMap[globalRefId] || 'Unknown';
                breakdown[wineType] = (breakdown[wineType] || 0) + 1;
            }
        });

        return breakdown;
    }

    /**
     * Get unique label images for unshelved wines
     * @param {Array} unshelvedWines - Array of unshelved wine instances
     * @returns {Array} Array of label image URLs
     */
    getUnshelvedLabelImages(unshelvedWines) {
        if (!unshelvedWines || !this.wineReferences) return [];

        const referenceMap = {};
        this.wineReferences.forEach(ref => {
            referenceMap[ref.id] = ref;
        });

        const labelImages = [];
        const seenImages = new Set();

        unshelvedWines.forEach(instance => {
            if (instance.referenceId) {
                const globalRefId = this.userRefToGlobalRefId ? this.userRefToGlobalRefId[instance.referenceId] : instance.referenceId;
                const reference = referenceMap[globalRefId];
                if (reference && reference.labelImageUrl && !seenImages.has(reference.labelImageUrl)) {
                    labelImages.push(reference.labelImageUrl);
                    seenImages.add(reference.labelImageUrl);
                }
            }
        });

        return labelImages;
    }

    renderCellarPreview(cellar, labelImages, breakdown) {
        // Render small bottle visualization
        const bottlePreview = this.renderBottlePreview(cellar);
        
        // Get capacity and temperature
        const usedSlots = cellar.getUsedSlots();
        const capacity = cellar.capacity || 0;
        const capacityText = `${usedSlots}/${capacity}`;
        const tempText = cellar.temperature ? `${cellar.temperature}°F` : 'Not set';

        // Create stacked image container with multiple square images
        let imagesHtml = '';
        if (labelImages.length > 0) {
            // Show exactly 3 images stacked on top of each other, rotating through all images
            // This ensures consistent card height
            const numToShow = 3;
            for (let i = 0; i < numToShow; i++) {
                const imgUrl = labelImages[i % labelImages.length];
                imagesHtml += `<div class="stacked-image-wrapper"><img src="${this.escapeHtml(imgUrl)}" alt="Wine label" class="rotating-label-image" data-image-index="${i}" /></div>`;
            }
        } else {
            imagesHtml = '<div class="no-labels-message">No wine labels</div>';
        }

        return `
            <div class="cellar-panel-preview">
                <div class="preview-image-column">
                    <div class="rotating-images-container">
                        ${imagesHtml}
                    </div>
                </div>
                <div class="preview-info-column">
                    <div class="preview-info-item">
                        <strong>Contents:</strong> ${this.formatBreakdown(breakdown) || 'Empty'}
                    </div>
                    <div class="preview-info-item">
                        <strong>Capacity:</strong> ${capacityText}
                    </div>
                    <div class="preview-info-item">
                        <strong>Temperature:</strong> ${tempText}
                    </div>
                    <div class="preview-bottles-container">
                        <div class="preview-bottles-label">Preview</div>
                        <div class="preview-bottles">
                            ${bottlePreview}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render the unshelved wines panel card
     * @param {Array} unshelvedWines - Array of unshelved wine instances
     * @returns {string} HTML string for the unshelved wines panel, or empty string if none
     */
    renderUnshelvedPanel(unshelvedWines) {
        if (!unshelvedWines || unshelvedWines.length === 0) return '';

        const breakdown = this.getUnshelvedWineBreakdown(unshelvedWines);
        const labelImages = this.getUnshelvedLabelImages(unshelvedWines);

        // Find newest unshelved wine
        const newestWine = this.getNewestUnshelvedWine(unshelvedWines);
        let lastBottleDateHtml = '';
        let lastBottleInfoHtml = '';
        
        if (newestWine) {
            const storedDate = newestWine.storedDate || newestWine.createdAt;
            if (storedDate) {
                const date = new Date(storedDate);
                const formattedDate = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
                lastBottleDateHtml = `<div class="preview-info-item"><strong>Last bottle added date:</strong> ${this.escapeHtml(formattedDate)}</div>`;
            }
            
            // Get wine reference info
            if (newestWine.referenceId && this.wineReferences) {
                const globalRefId = this.userRefToGlobalRefId ? this.userRefToGlobalRefId[newestWine.referenceId] : newestWine.referenceId;
                const reference = this.wineReferences.find(ref => ref.id === globalRefId);
                if (reference) {
                    const flag = this.getCountryFlag(reference.country);
                    const flagDisplay = flag ? `${flag} ` : '';
                    const vintage = reference.vintage ? `${flagDisplay}${reference.vintage} ` : '';
                    const name = reference.name || 'Unknown';
                    lastBottleInfoHtml = `<div class="preview-info-item"><strong>Last bottle added:</strong> ${this.escapeHtml(vintage + name)}</div>`;
                }
            }
        }

        // Build stacked image container (same as cellar cards)
        let imagesHtml = '';
        if (labelImages.length > 0) {
            const numToShow = 3;
            for (let i = 0; i < numToShow; i++) {
                const imgUrl = labelImages[i % labelImages.length];
                imagesHtml += `<div class="stacked-image-wrapper"><img src="${this.escapeHtml(imgUrl)}" alt="Wine label" class="rotating-label-image" data-image-index="${i}" /></div>`;
            }
        } else {
            imagesHtml = '<div class="no-labels-message">No wine labels</div>';
        }

        return `
            <div class="cellar-panel" data-cellar-id="unshelved">
                <div class="cellar-panel-preview">
                    <div class="preview-image-column">
                        <div class="rotating-images-container">
                            ${imagesHtml}
                        </div>
                    </div>
                    <div class="preview-info-column">
                        <div class="preview-info-item">
                            <strong>Contents:</strong> ${this.formatBreakdown(breakdown) || 'Empty'}
                        </div>
                        ${lastBottleDateHtml}
                        ${lastBottleInfoHtml}
                        <div class="unshelved-instructions">
                            <p>To move unshelved wines into a cellar, go to a cellar and tap an empty slot and select the bottle to be moved.</p>
                        </div>
                    </div>
                </div>
                <div class="cellar-panel-info">
                    <div class="cellar-panel-header">
                        <h3 class="cellar-panel-name">UNSHELVED WINES</h3>
                        <div class="cellar-panel-menu">
                            <div style="width: 28px; height: 28px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Get the newest unshelved wine instance (by storedDate or createdAt)
     * @param {Array} unshelvedWines - Array of unshelved wine instances
     * @returns {Object|null} Newest wine instance or null
     */
    getNewestUnshelvedWine(unshelvedWines) {
        if (!unshelvedWines || unshelvedWines.length === 0) return null;

        let newest = null;
        let newestTime = 0;

        unshelvedWines.forEach(instance => {
            const dateStr = instance.storedDate || instance.createdAt;
            if (dateStr) {
                const time = new Date(dateStr).getTime();
                if (time > newestTime) {
                    newestTime = time;
                    newest = instance;
                }
            }
        });

        return newest;
    }

    /**
     * Get country flag emoji from country name
     * @param {string} country - Country name
     * @returns {string} Flag emoji or empty string
     */
    getCountryFlag(country) {
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

    renderBottlePreview(cellar) {
        if (!cellar.winePositions || !this.wineInstances || !this.wineReferences) {
            return '<div class="bottle-preview-empty">No bottles</div>';
        }

        const shelves = cellar.shelves || [];
        if (shelves.length === 0) {
            return '<div class="bottle-preview-empty">No shelves</div>';
        }

        // Create maps for lookup
        const instanceMap = {};
        if (this.wineInstances) {
            this.wineInstances.forEach(inst => {
                instanceMap[inst.id] = inst;
            });
        }

        const referenceMap = {};
        if (this.wineReferences) {
            this.wineReferences.forEach(ref => {
                referenceMap[ref.id] = ref;
            });
        }

        // Scale factor for mini preview - make it much smaller
        const scale = 0.15; // 15% of original size
        const baseUnitSize = 40;
        const baseRadius = 40;
        const unitSize = baseUnitSize * scale;
        const radius = baseRadius * scale;

        let html = '<div class="bottle-preview-shelves">';
        
        shelves.forEach((shelf, shelfIndex) => {
            const positions = shelf.positions;
            const isDouble = shelf.isDouble;
            const shelfKey = String(shelfIndex);
            const shelfData = cellar.winePositions[shelfKey] || {};

            html += '<div class="bottle-preview-shelf-row">';

            if (isDouble) {
                // Double-sided: staggered circles layout
                const totalWidth = (2 * positions + 1) * unitSize;
                const containerHeight = radius * 2 * 2; // Height for staggered rows
                html += `<div class="bottle-preview-positions staggered" style="position: relative; width: ${totalWidth}px; height: ${containerHeight}px; margin: 0 auto;">`;
                const frontPositions = shelfData.front || [];
                const backPositions = shelfData.back || [];
                
                for (let pos = 0; pos < positions; pos++) {
                    const frontInstanceId = frontPositions[pos] || null;
                    const backInstanceId = backPositions[pos] || null;
                    html += this.renderMiniStaggeredPosition(frontInstanceId, backInstanceId, instanceMap, referenceMap, pos, unitSize, radius);
                }
                html += `</div>`;
            } else {
                // Single side - circles in a single row
                const totalWidth = (2 * positions) * unitSize;
                const containerHeight = radius * 2; // Height for single row
                html += `<div class="bottle-preview-positions single-row" style="position: relative; width: ${totalWidth}px; height: ${containerHeight}px; margin: 0 auto;">`;
                const singlePositions = shelfData.single || [];
                
                for (let pos = 0; pos < positions; pos++) {
                    const instanceId = singlePositions[pos] || null;
                    html += this.renderMiniSinglePosition(instanceId, instanceMap, referenceMap, pos, unitSize, radius);
                }
                html += `</div>`;
            }

            html += '</div>';
        });

        html += '</div>';
        return html;
    }

    renderMiniSinglePosition(instanceId, instanceMap, referenceMap, position, unitSize, radius) {
        const inst = instanceId && instanceMap[instanceId] ? instanceMap[instanceId] : null;
        const globalRefId = inst && inst.referenceId && this.userRefToGlobalRefId ? this.userRefToGlobalRefId[inst.referenceId] : (inst ? inst.referenceId : null);
        const wine = globalRefId ? referenceMap[globalRefId] : null;
        const wineType = wine ? (wine.type || '').toLowerCase() : '';
        const vintage = wine && wine.vintage ? wine.vintage : null;
        
        // Same positioning as full view: edges align (double spaced)
        const centerX = (2 * position + 1) * unitSize;
        const leftEdge = centerX - radius;
        
        if (wine && vintage) {
            const wineTypeClass = this.getWineTypeClass(wineType);
            return `
                <div class="bottle-preview-position circle vintage-mode ${wineTypeClass}" style="position: absolute; left: ${leftEdge}px; width: ${radius * 2}px; height: ${radius * 2}px; top: 0;"></div>
            `;
        } else {
            return `
                <div class="bottle-preview-position circle empty" style="position: absolute; left: ${leftEdge}px; width: ${radius * 2}px; height: ${radius * 2}px; top: 0;"></div>
            `;
        }
    }

    renderMiniStaggeredPosition(frontInstanceId, backInstanceId, instanceMap, referenceMap, position, unitSize, radius) {
        const frontInst = frontInstanceId && instanceMap[frontInstanceId] ? instanceMap[frontInstanceId] : null;
        const frontGlobalRefId = frontInst && frontInst.referenceId && this.userRefToGlobalRefId ? this.userRefToGlobalRefId[frontInst.referenceId] : (frontInst ? frontInst.referenceId : null);
        const frontWine = frontGlobalRefId ? referenceMap[frontGlobalRefId] : null;
        const backInst = backInstanceId && instanceMap[backInstanceId] ? instanceMap[backInstanceId] : null;
        const backGlobalRefId = backInst && backInst.referenceId && this.userRefToGlobalRefId ? this.userRefToGlobalRefId[backInst.referenceId] : (backInst ? backInst.referenceId : null);
        const backWine = backGlobalRefId ? referenceMap[backGlobalRefId] : null;
        
        const frontType = frontWine ? (frontWine.type || '').toLowerCase() : '';
        const backType = backWine ? (backWine.type || '').toLowerCase() : '';
        const frontVintage = frontWine && frontWine.vintage ? frontWine.vintage : null;
        const backVintage = backWine && backWine.vintage ? backWine.vintage : null;
        
        // Same positioning as full view: staggered layout
        const frontCenterX = (2 * position + 1) * unitSize;
        const backCenterX = (2 * position + 2) * unitSize;
        
        let html = '';
        
        // Back position (top row) - positioned at top: 0
        if (backWine && backVintage) {
            const backTypeClass = this.getWineTypeClass(backType);
            html += `<div class="bottle-preview-position circle stagger-back vintage-mode ${backTypeClass}" style="position: absolute; left: ${backCenterX - radius}px; width: ${radius * 2}px; height: ${radius * 2}px; top: 0;"></div>`;
        } else {
            html += `<div class="bottle-preview-position circle empty stagger-back" style="position: absolute; left: ${backCenterX - radius}px; width: ${radius * 2}px; height: ${radius * 2}px; top: 0;"></div>`;
        }
        
        // Front position (bottom row) - positioned at bottom: 0
        if (frontWine && frontVintage) {
            const frontTypeClass = this.getWineTypeClass(frontType);
            html += `<div class="bottle-preview-position circle stagger-front vintage-mode ${frontTypeClass}" style="position: absolute; left: ${frontCenterX - radius}px; width: ${radius * 2}px; height: ${radius * 2}px; bottom: 0;"></div>`;
        } else {
            html += `<div class="bottle-preview-position circle empty stagger-front" style="position: absolute; left: ${frontCenterX - radius}px; width: ${radius * 2}px; height: ${radius * 2}px; bottom: 0;"></div>`;
        }
        
        return html;
    }

    startImageRotation() {
        const previews = document.querySelectorAll('.rotating-images-container');
        
        previews.forEach(container => {
            const wrappers = container.querySelectorAll('.stacked-image-wrapper');
            if (wrappers.length === 0) return;
            
            // Collect all unique image URLs from all images in this container
            // (they may have duplicates initially, we'll rotate through unique ones)
            const allImages = Array.from(container.querySelectorAll('.rotating-label-image'));
            const uniqueUrls = [];
            const seenUrls = new Set();
            
            allImages.forEach(img => {
                if (img.src && !seenUrls.has(img.src)) {
                    uniqueUrls.push(img.src);
                    seenUrls.add(img.src);
                }
            });
            
            if (uniqueUrls.length === 0) return;
            
            let currentStartIndex = 0;
            
            const rotate = () => {
                // Update each visible stacked image to show the next image in sequence
                wrappers.forEach((wrapper, i) => {
                    const img = wrapper.querySelector('.rotating-label-image');
                    if (img) {
                        const imageIndex = (currentStartIndex + i) % uniqueUrls.length;
                        img.src = uniqueUrls[imageIndex];
                    }
                });
                
                // Move to next starting position
                currentStartIndex = (currentStartIndex + 1) % uniqueUrls.length;
            };
            
            // Rotate every 5 seconds
            const intervalId = setInterval(rotate, 5000);
            
            // Store interval ID on container for cleanup if needed
            container.dataset.rotationInterval = intervalId;
        });
    }

    showCreateDialog() {
        const dialog = document.getElementById('create-cellar-dialog');
        const form = document.getElementById('create-cellar-form');
        const shelvesContainer = document.getElementById('shelves-container');
        if (dialog && form && shelvesContainer) {
            form.reset();
            shelvesContainer.innerHTML = '';
            // Add one initial shelf input
            this.addShelfInput();
            dialog.classList.remove('hidden');
        }
    }

    addShelfInput() {
        const container = document.getElementById('shelves-container');
        if (!container) return;

        const shelfIndex = container.children.length;
        const shelfDiv = document.createElement('div');
        shelfDiv.className = 'shelf-input';
        shelfDiv.innerHTML = `
            <div class="shelf-input-row">
                <div class="shelf-input-field">
                    <label>Positions</label>
                    <input type="number" class="shelf-positions" min="1" value="5" required>
                </div>
                <div class="shelf-input-field">
                    <label>
                        <input type="checkbox" class="shelf-is-double"> Double-sided
                    </label>
                </div>
                <button type="button" class="btn-remove-shelf" onclick="this.closest('.shelf-input').remove()">×</button>
            </div>
        `;
        container.appendChild(shelfDiv);
    }

    hideCreateDialog() {
        const dialog = document.getElementById('create-cellar-dialog');
        if (dialog) {
            dialog.classList.add('hidden');
        }
    }

    async handleCreate() {
        const form = document.getElementById('create-cellar-form');
        if (!form) return;

        const formData = new FormData(form);
        const name = formData.get('name') || undefined;
        const temperature = formData.get('temperature') ? parseFloat(formData.get('temperature')) : undefined;

        // Parse shelves from the form
        const shelves = [];
        const shelfInputs = form.querySelectorAll('.shelf-input');
        shelfInputs.forEach(input => {
            const positions = parseInt(input.querySelector('.shelf-positions').value);
            const isDouble = input.querySelector('.shelf-is-double').checked;
            if (positions > 0) {
                shelves.push([positions, isDouble]);
            }
        });

        if (shelves.length === 0) {
            this.showError('Please add at least one shelf.');
            return;
        }

        try {
            const data = await API.post('/cellars', {
                name,
                shelves,
                temperature,
            });

            this.cellars.push(Cellar.fromDict(data));
            this.renderCellars();
            this.hideCreateDialog();
        } catch (error) {
            console.error('Error creating cellar:', error);
            this.showError(error.message || 'Failed to create cellar. Please try again.');
        }
    }

    showEditDialog(cellarId) {
        const cellar = this.cellars.find(c => c.id === cellarId);
        if (!cellar) {
            console.error(`Cellar not found: ${cellarId}`);
            return;
        }

        const dialog = document.getElementById('edit-cellar-dialog');
        const form = document.getElementById('edit-cellar-form');
        if (!dialog) {
            console.error('Edit dialog element not found');
            return;
        }
        if (!form) {
            console.error('Edit form element not found');
            return;
        }
        
        form.dataset.cellarId = cellarId;
        const nameInput = form.querySelector('#edit-cellar-name');
        const tempInput = form.querySelector('#edit-cellar-temperature');
        if (nameInput) nameInput.value = cellar.name || '';
        if (tempInput) tempInput.value = cellar.temperature || '';
        dialog.classList.remove('hidden');
    }

    hideEditDialog() {
        const dialog = document.getElementById('edit-cellar-dialog');
        if (dialog) {
            dialog.classList.add('hidden');
        }
    }

    async handleEdit() {
        const form = document.getElementById('edit-cellar-form');
        if (!form) return;

        const cellarId = form.dataset.cellarId;
        const cellar = this.cellars.find(c => c.id === cellarId);
        if (!cellar) return;

        const formData = new FormData(form);
        const name = formData.get('name') || undefined;
        const temperature = formData.get('temperature') ? parseFloat(formData.get('temperature')) : undefined;

        try {
            const data = await API.put(`/cellars/${cellarId}`, {
                name,
                temperature,
            });

            // Update local cellar
            const index = this.cellars.findIndex(c => c.id === cellarId);
            if (index !== -1) {
                this.cellars[index] = Cellar.fromDict(data);
                this.renderCellars();
            }

            this.hideEditDialog();
        } catch (error) {
            console.error('Error updating cellar:', error);
            this.showError(error.message || 'Failed to update cellar. Please try again.');
        }
    }

    showDeleteDialog(cellarId) {
        const cellar = this.cellars.find(c => c.id === cellarId);
        if (!cellar) {
            console.error(`Cellar not found: ${cellarId}`);
            return;
        }

        const dialog = document.getElementById('delete-cellar-dialog');
        if (!dialog) {
            console.error('Delete dialog element not found');
            return;
        }
        
        const message = dialog.querySelector('.delete-message');
        if (!message) {
            console.error('Delete message element not found');
            return;
        }
        
        dialog.dataset.cellarId = cellarId;
        message.textContent = `Are you sure you want to delete "${this.escapeHtml(cellar.name || 'Unnamed Cellar')}"? This will move all wines in this cellar to unshelved.`;
        dialog.classList.remove('hidden');
    }

    hideDeleteDialog() {
        const dialog = document.getElementById('delete-cellar-dialog');
        if (dialog) {
            dialog.classList.add('hidden');
        }
    }

    async handleDelete() {
        const dialog = document.getElementById('delete-cellar-dialog');
        if (!dialog) return;

        const cellarId = dialog.dataset.cellarId;
        if (!cellarId) return;

        try {
            await API.delete(`/cellars/${cellarId}`);

            // Remove from local list
            this.cellars = this.cellars.filter(c => c.id !== cellarId);
            this.renderCellars();
            this.hideDeleteDialog();
        } catch (error) {
            console.error('Error deleting cellar:', error);
            this.showError(error.message || 'Failed to delete cellar. Please try again.');
        }
    }

    showError(message) {
        // Simple error display - could be enhanced with a toast notification
        alert(message);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    toggleCellarMenu(cellarId) {
        const menu = document.getElementById(`cellar-menu-${cellarId}`);
        if (!menu) {
            console.error(`Menu not found for cellar ${cellarId}`);
            return;
        }

        // Hide all other menus first
        document.querySelectorAll('.cellar-menu-dropdown').forEach(m => {
            if (m.id !== `cellar-menu-${cellarId}`) {
                m.style.display = 'none';
            }
        });

        // Toggle this menu - check inline style first, then computed
        const inlineDisplay = menu.style.display;
        const computedDisplay = window.getComputedStyle(menu).display;
        
        // If inline style is set, use it; otherwise use computed
        if (inlineDisplay) {
            // Inline style is set - toggle it
            if (inlineDisplay === 'none') {
                menu.style.display = 'block';
            } else {
                menu.style.display = 'none';
            }
        } else {
            // No inline style - check computed style (initial state is 'none' from inline style in HTML)
            if (computedDisplay === 'none' || !inlineDisplay) {
                menu.style.display = 'block';
            } else {
                menu.style.display = 'none';
            }
        }
    }

    hideCellarMenu(cellarId) {
        const menu = document.getElementById(`cellar-menu-${cellarId}`);
        if (menu) {
            menu.style.display = 'none';
        }
    }


    async showCellarDetail(cellarId) {
        try {
            // Load full cellar data with wine instances
            const cellar = await API.get(`/cellars/${cellarId}`);
            
            // Load wine instances, global references, and user references
            const [wineInstances, wineReferences, userWineReferences] = await Promise.all([
                API.get('/wine-instances'),
                API.get('/wine-references'),
                API.get('/user-wine-references')
            ]);

            // Create maps for quick lookup
            const instanceMap = {};
            wineInstances.forEach(inst => {
                instanceMap[inst.id] = inst;
            });

            // Build global reference map
            const globalRefMap = {};
            wineReferences.forEach(ref => {
                globalRefMap[ref.id] = ref;
            });

            // Build dual-keyed referenceMap: accessible by both UserWineRef ID and GlobalWineRef ID
            // Merge user-specific data (rating, tastingNotes) into the global reference
            const referenceMap = {};
            userWineReferences.forEach(userRef => {
                const globalRef = globalRefMap[userRef.globalReferenceId];
                if (globalRef) {
                    const merged = {
                        ...globalRef,
                        userReferenceId: userRef.id,
                        rating: userRef.rating,
                        tastingNotes: userRef.tastingNotes
                    };
                    referenceMap[userRef.id] = merged;                  // Keyed by UserWineRef ID
                    referenceMap[userRef.globalReferenceId] = merged;   // Keyed by GlobalWineRef ID
                }
            });

            // Update view header
            const nameHeader = document.getElementById('cellar-detail-name');
            if (nameHeader) {
                nameHeader.textContent = cellar.name || 'Unnamed Cellar';
            }

            // Store current data for re-rendering on toggle
            this.currentCellar = cellar;
            this.currentInstanceMap = instanceMap;
            this.currentReferenceMap = referenceMap;

            // Set up labels toggle after view is shown
            this.setupLabelsToggle();

            // Render cellar shelves
            this.renderCellarDetail(cellar, instanceMap, referenceMap);

            // Switch to cellar detail view
            if (window.app && window.app.showView) {
                window.app.showView('cellar-detail');
            }
        } catch (error) {
            console.error('Error loading cellar detail:', error);
            console.error('Error stack:', error.stack);
            alert(`Failed to load cellar details: ${error.message || 'Unknown error'}. Please check the console for details.`);
        }
    }

    renderCellarDetail(cellar, instanceMap, referenceMap) {
        const container = document.getElementById('cellar-detail-content');
        if (!container) return;

        const shelves = cellar.shelves || [];
        const winePositions = cellar.winePositions || {};

        if (shelves.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">No shelves in this cellar.</p>';
            return;
        }

        let html = '<div class="fridge-container">';
        
        // Calculate available width: container width minus fridge padding (20px each side = 40px total)
        // We'll calculate this after inserting HTML, but for now use container width
        const containerWidth = container.clientWidth || (window.innerWidth || document.documentElement.clientWidth);
        const fridgePadding = 40; // 20px padding on each side
        const availableWidth = containerWidth - fridgePadding;
        const eightyPercentWidth = availableWidth * 0.8;

        shelves.forEach((shelf, shelfIndex) => {
            // Shelf can be either [positions, isDouble] array or Shelf object
            let positions, isDouble;
            if (Array.isArray(shelf)) {
                [positions, isDouble] = shelf;
            } else {
                positions = shelf.positions;
                isDouble = shelf.isDouble;
            }
            const shelfKey = String(shelfIndex);
            const shelfData = winePositions[shelfKey] || {};

            // Calculate bottle width for this shelf
            const unitSize = 40;
            let bottleWidth;
            if (isDouble) {
                // Last back position: center at (2*positions) * 40, right edge at (2*positions + 1) * 40
                bottleWidth = (2 * positions + 1) * unitSize;
            } else {
                // Last position: center at (2*positions - 1) * 40, right edge at (2*positions) * 40
                bottleWidth = (2 * positions) * unitSize;
            }

            // Bar width is max(80% available width, width of all bottles), but never exceed available width
            const barWidth = Math.min(Math.max(eightyPercentWidth, bottleWidth), availableWidth);

            html += `<div class="shelf-row">`;
            html += `<div class="shelf-positions-container">`;

            if (isDouble) {
                // Double-sided: staggered circles layout
                html += `<div class="positions-row staggered" style="position: relative; width: ${bottleWidth}px; margin: 0 auto;">`;
                const frontPositions = shelfData.front || [];
                const backPositions = shelfData.back || [];
                for (let pos = 0; pos < positions; pos++) {
                    const frontInstanceId = frontPositions[pos] || null;
                    const backInstanceId = backPositions[pos] || null;
                    html += this.renderStaggeredPosition(frontInstanceId, backInstanceId, instanceMap, referenceMap, shelfIndex, pos);
                }
                html += `</div>`;
            } else {
                // Single side - use circles in a single row
                html += `<div class="positions-row single-row" style="position: relative; width: ${bottleWidth}px; margin: 0 auto;">`;
                const singlePositions = shelfData.single || [];
                for (let pos = 0; pos < positions; pos++) {
                    const instanceId = singlePositions[pos] || null;
                    html += this.renderSinglePosition(instanceId, instanceMap, referenceMap, shelfIndex, pos);
                }
                html += `</div>`;
            }

            html += `</div>`;
            html += `<div class="shelf-separator-bar" style="width: ${barWidth}px;">`;
            html += `<div class="shelf-label">Shelf ${shelfIndex + 1}</div>`;
            html += `</div>`;
            html += `</div>`;
        });

        html += '</div>';
        container.innerHTML = html;
        
        // Recalculate bar widths after HTML is inserted to get actual fridge width
        this.recalculateBarWidths(container, cellar);
        
        // Add resize handler to recalculate bar widths when window resizes
        this.setupResizeHandler(container, cellar);
        
        // Set up wine card hover handlers
        this.setupWineCardHovers(referenceMap, instanceMap, cellar);
        
        // Set up empty position click handlers
        this.setupEmptyPositionHandlers(cellar);
    }

    setupWineCardHovers(referenceMap, instanceMap, cellar) {
        if (!referenceMap || !instanceMap || !cellar) {
            console.warn('setupWineCardHovers called with missing parameters:', { referenceMap, instanceMap, cellar });
            return;
        }
        
        const wineCard = getWineCard();
        const winePositions = document.querySelectorAll('.wine-position[data-wine-reference-id]');
        
        winePositions.forEach(position => {
            const referenceId = position.getAttribute('data-wine-reference-id');
            if (!referenceId) return;
            
            const wineReference = referenceMap[referenceId];
            if (!wineReference) return;
            
            // Get wine instance if available
            const instanceId = position.getAttribute('data-wine-instance-id');
            const instance = instanceId && instanceMap && instanceMap[instanceId] ? instanceMap[instanceId] : null;
            
            // Find location info for this instance
            let locationInfo = null;
            try {
                if (instance && cellar) {
                    locationInfo = findInstanceLocationInCellar(instance, cellar);
                }
            } catch (error) {
                console.error('Error finding location info:', error);
            }
            
            // Get all instances for counting additional bottles
            // Instances from API have referenceId, not reference object
            const allInstances = instanceMap ? Object.values(instanceMap).filter(inst => inst && (inst.referenceId || (inst.reference && inst.reference.id))) : [];
            
            position.addEventListener('mouseenter', (e) => {
                try {
                    const rect = position.getBoundingClientRect();
                    const x = rect.left + rect.width / 2;
                    const y = rect.top;
                    wineCard.show(wineReference, instance, x, y, {
                        cellars: cellar ? [cellar] : [],
                        allInstances: allInstances,
                        locationInfo: locationInfo
                    });
                } catch (error) {
                    console.error('Error showing wine card:', error);
                }
            });
            
            position.addEventListener('mouseleave', () => {
                wineCard.hide(200); // Small delay to allow moving to card
            });
            
            position.addEventListener('mousemove', (e) => {
                const rect = position.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top;
                wineCard.positionCard(x, y);
            });
            
            // Add click handler to open wine detail modal
            position.addEventListener('click', async (e) => {
                // Don't open modal if clicking on rating stars in the card
                if (e.target.closest('.rating-star')) {
                    return;
                }
                
                if (wineReference) {
                    // Dynamically import and show wine detail view
                    import('./wineDetailView.js').then(({ getWineDetailView }) => {
                        const wineDetailView = getWineDetailView();
                        wineDetailView.show(wineReference, instance);
                    }).catch(error => {
                        console.error('Error loading wine detail view:', error);
                    });
                }
            });
        });
        
        // Also handle hover on the card itself to keep it visible
        const card = document.getElementById('wine-card');
        if (card) {
            card.addEventListener('mouseenter', () => {
                if (wineCard.hideTimeout) {
                    clearTimeout(wineCard.hideTimeout);
                    wineCard.hideTimeout = null;
                }
            });
            
            card.addEventListener('mouseleave', () => {
                wineCard.hide(0);
            });
        }
    }

    setupEmptyPositionHandlers(cellar) {
        const emptyPositions = document.querySelectorAll('.wine-position.empty[data-empty="true"]');
        emptyPositions.forEach(position => {
            position.addEventListener('click', (e) => {
                e.stopPropagation();
                const shelfIndex = parseInt(position.getAttribute('data-shelf-index'));
                const side = position.getAttribute('data-side');
                const pos = parseInt(position.getAttribute('data-position'));
                this.showUnshelvedBottlesModal(cellar.id, shelfIndex, side, pos);
            });
        });
    }

    async showUnshelvedBottlesModal(cellarId, shelfIndex, side, position) {
        const modal = document.getElementById('unshelved-bottles-modal');
        if (!modal) return;

        // Load fresh wine instances, cellars, and references to get current unshelved wines
        try {
            const [wineInstances, cellars, wineReferences, userWineReferences] = await Promise.all([
                API.get('/wine-instances'),
                API.get('/cellars'),
                API.get('/wine-references'),
                API.get('/user-wine-references')
            ]);
            
            // Temporarily update for getUnshelvedWines to work
            const oldInstances = this.wineInstances;
            const oldCellars = this.cellars;
            const oldReferences = this.wineReferences;
            const oldUserRefToGlobalRefId = this.userRefToGlobalRefId;
            
            this.wineInstances = wineInstances;
            this.cellars = cellars;
            this.wineReferences = wineReferences;
            
            // Build userRefToGlobalRefId mapping
            this.userRefToGlobalRefId = {};
            userWineReferences.forEach(userRef => {
                this.userRefToGlobalRefId[userRef.id] = userRef.globalReferenceId;
            });
            
            // Get unshelved wines
            const unshelvedWines = this.getUnshelvedWines();
            
            if (unshelvedWines.length === 0) {
                // Restore old values before returning
                this.wineInstances = oldInstances;
                this.cellars = oldCellars;
                this.wineReferences = oldReferences;
                this.userRefToGlobalRefId = oldUserRefToGlobalRefId;
                alert('No unshelved wines available to place.');
                return;
            }

            // Sort by most recently added (storedDate or createdAt)
            const sortedWines = [...unshelvedWines].sort((a, b) => {
                const dateA = a.storedDate || a.createdAt || '';
                const dateB = b.storedDate || b.createdAt || '';
                return new Date(dateB).getTime() - new Date(dateA).getTime();
            });

            // Build userRefToGlobalRefId mapping for use in rendering
            const userRefToGlobalRefIdMap = {};
            userWineReferences.forEach(userRef => {
                userRefToGlobalRefIdMap[userRef.id] = userRef.globalReferenceId;
            });

            // Render the list
            const listContainer = document.getElementById('unshelved-bottles-list');
            if (!listContainer) {
                // Restore old values before returning
                this.wineInstances = oldInstances;
                this.cellars = oldCellars;
                this.wineReferences = oldReferences;
                this.userRefToGlobalRefId = oldUserRefToGlobalRefId;
                return;
            }

            let html = '';
            sortedWines.forEach(instance => {
                const globalRefId = userRefToGlobalRefIdMap[instance.referenceId] || instance.referenceId;
                const reference = wineReferences.find(ref => ref.id === globalRefId);
                
                if (reference) {
                    const flag = this.getCountryFlag(reference.country);
                    const flagDisplay = flag ? `${flag} ` : '';
                    const vintage = reference.vintage ? `${flagDisplay}${reference.vintage} ` : '';
                    const name = reference.name || 'Unknown Wine';
                    const storedDate = instance.storedDate || instance.createdAt;
                    const dateStr = storedDate ? new Date(storedDate).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '';
                    
                    html += `
                        <div class="unshelved-bottle-item" data-instance-id="${instance.id}">
                            ${reference.labelImageUrl ? `
                                <img src="${this.escapeHtml(reference.labelImageUrl)}" alt="${this.escapeHtml(name)}" class="unshelved-bottle-image" />
                            ` : `
                                <div class="unshelved-bottle-placeholder">🍷</div>
                            `}
                            <div class="unshelved-bottle-info">
                                <div class="unshelved-bottle-name">${this.escapeHtml(vintage + name)}</div>
                                ${dateStr ? `<div class="unshelved-bottle-date">Added: ${this.escapeHtml(dateStr)}</div>` : ''}
                            </div>
                        </div>
                    `;
                }
            });
            
            listContainer.innerHTML = html;

            // Set up click handlers for each bottle
            const bottleItems = listContainer.querySelectorAll('.unshelved-bottle-item');
            bottleItems.forEach(item => {
                item.addEventListener('click', () => {
                    const instanceId = item.getAttribute('data-instance-id');
                    this.placeBottleInSlot(cellarId, shelfIndex, side, position, instanceId);
                    this.hideUnshelvedBottlesModal();
                });
            });

            // Show modal
            modal.classList.remove('hidden');

            // Set up close handlers
            const closeBtn = document.getElementById('unshelved-bottles-close');
            if (closeBtn) {
                closeBtn.onclick = () => this.hideUnshelvedBottlesModal();
            }

            const overlay = modal.querySelector('.wine-detail-overlay');
            if (overlay) {
                overlay.onclick = () => this.hideUnshelvedBottlesModal();
            }
            
            // Restore old values after everything is set up
            this.wineInstances = oldInstances;
            this.cellars = oldCellars;
            this.wineReferences = oldReferences;
            this.userRefToGlobalRefId = oldUserRefToGlobalRefId;
        } catch (error) {
            console.error('Error loading unshelved bottles:', error);
            alert(`Failed to load unshelved bottles: ${error.message || 'Unknown error'}`);
            
            // Restore old values on error
            if (oldInstances !== undefined) this.wineInstances = oldInstances;
            if (oldCellars !== undefined) this.cellars = oldCellars;
            if (oldReferences !== undefined) this.wineReferences = oldReferences;
            if (oldUserRefToGlobalRefId !== undefined) this.userRefToGlobalRefId = oldUserRefToGlobalRefId;
        }
    }

    hideUnshelvedBottlesModal() {
        const modal = document.getElementById('unshelved-bottles-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    async placeBottleInSlot(cellarId, shelfIndex, side, position, instanceId) {
        try {
            // Update wine instance location
            await API.updateWineInstanceLocation(instanceId, {
                oldCellarId: null, // Was unshelved
                newCellarId: cellarId,
                shelfIndex: shelfIndex,
                side: side,
                position: position
            });

            // Reload cellar detail to show updated position
            await this.showCellarDetail(cellarId);
        } catch (error) {
            console.error('Error placing bottle:', error);
            alert(`Failed to place bottle: ${error.message || 'Unknown error'}`);
        }
    }

    recalculateBarWidths(container, cellar) {
        const fridgeContainer = container.querySelector('.fridge-container');
        if (!fridgeContainer) return;
        
        const availableWidth = fridgeContainer.clientWidth - 40; // Subtract padding (20px each side)
        const eightyPercentWidth = availableWidth * 0.8;
        const shelves = cellar.shelves || [];
        const unitSize = 40;
        
        const bars = container.querySelectorAll('.shelf-separator-bar');
        bars.forEach((bar, index) => {
            if (index >= shelves.length) return;
            
            const [positions, isDouble] = shelves[index];
            let bottleWidth;
            if (isDouble) {
                bottleWidth = (2 * positions + 1) * unitSize;
            } else {
                bottleWidth = (2 * positions) * unitSize;
            }
            
            const barWidth = Math.min(Math.max(eightyPercentWidth, bottleWidth), availableWidth);
            bar.style.width = `${barWidth}px`;
        });
    }

    setupResizeHandler(container, cellar) {
        // Remove existing handler if any
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }
        
        // Create new resize handler
        this.resizeHandler = () => {
            this.recalculateBarWidths(container, cellar);
        };
        
        window.addEventListener('resize', this.resizeHandler);
    }

    renderPosition(instanceId, instanceMap, referenceMap, shelfIndex, side, position) {
        if (instanceId && instanceMap[instanceId]) {
            const instance = instanceMap[instanceId];
            const reference = referenceMap[instance.referenceId];
            
            if (reference && reference.labelImageUrl) {
                const wineName = this.escapeHtml(reference.name || 'Unknown Wine');
                return `
                    <div class="wine-position" title="${wineName}">
                        <img src="${this.escapeHtml(reference.labelImageUrl)}" alt="${wineName}" class="wine-label-image" />
                    </div>
                `;
            } else {
                // Wine instance but no reference or image
                return `<div class="wine-position empty" title="Wine (no image)"><div class="empty-square"></div></div>`;
            }
        } else {
            // Empty position
            return `<div class="wine-position empty" title="Empty position"><div class="empty-square"></div></div>`;
        }
    }

    renderSinglePosition(instanceId, instanceMap, referenceMap, shelfIndex, position) {
        const wine = instanceId && instanceMap[instanceId] ? referenceMap[instanceMap[instanceId].referenceId] : null;
        const wineName = wine ? this.escapeHtml(wine.name || 'Unknown Wine') : '';
        const wineImage = wine && wine.labelImageUrl ? this.escapeHtml(wine.labelImageUrl) : '';
        const wineType = wine ? (wine.type || '').toLowerCase() : '';
        const vintage = wine && wine.vintage ? wine.vintage : null;
        
        // Single row: position bottles so edges align (double spaced)
        // Bottle radius = 2 units, diameter = 4 units = 80px
        // Position 0: center at x=1 unit (draws 0-2), Position 1: center at x=3 units (draws 2-4), etc.
        // Using same unit size as staggered: 40px per unit
        const unitSize = 40;
        const radius = 40; // 40px radius = 80px diameter
        // Center at (2*position + 1) * unitSize, left edge at center - radius
        const centerX = (2 * position + 1) * unitSize; // Position 0: center at 40px, Position 1: center at 120px
        const leftEdge = centerX - radius; // Position 0: left at 0px, Position 1: left at 80px
        
        const positionId = `wine-pos-${shelfIndex}-single-${position}`;
        const wineRefId = wine ? wine.id : '';
        
        if (this.showLabels) {
            // Labels mode - show wine label image
            if (wineImage) {
                return `
                    <div class="wine-position circle single" id="${positionId}" style="left: ${leftEdge}px;" title="${wineName}" 
                         data-wine-reference-id="${wineRefId}" data-wine-instance-id="${instanceId || ''}">
                        <img src="${wineImage}" alt="${wineName}" class="wine-label-image" />
                    </div>
                `;
            } else {
                return `
                    <div class="wine-position circle empty single" style="left: ${leftEdge}px;" title="Empty position"
                         data-shelf-index="${shelfIndex}" data-side="single" data-position="${position}" data-empty="true">
                        <div class="empty-circle"></div>
                    </div>
                `;
            }
        } else {
            // Vintage mode - show vintage text with wine type color
            if (wine && vintage) {
                const wineTypeClass = this.getWineTypeClass(wineType);
                return `
                    <div class="wine-position circle single vintage-mode ${wineTypeClass}" id="${positionId}" style="left: ${leftEdge}px;" title="${wineName} (${vintage})"
                         data-wine-reference-id="${wineRefId}" data-wine-instance-id="${instanceId || ''}">
                        <span class="vintage-text">${vintage}</span>
                    </div>
                `;
            } else {
                return `
                    <div class="wine-position circle empty single" style="left: ${leftEdge}px;" title="Empty position"
                         data-shelf-index="${shelfIndex}" data-side="single" data-position="${position}" data-empty="true">
                        <div class="empty-circle"></div>
                    </div>
                `;
            }
        }
    }

    getWineTypeClass(wineType) {
        const type = wineType.toLowerCase();
        if (type.includes('red')) return 'wine-type-red';
        if (type.includes('white')) return 'wine-type-white';
        if (type.includes('rosé') || type.includes('rose')) return 'wine-type-rose';
        if (type.includes('sparkling')) return 'wine-type-sparkling';
        return 'wine-type-default';
    }

    setupLabelsToggle() {
        const labelsToggle = document.getElementById('labels-toggle');
        if (labelsToggle) {
            // Remove existing listener if any
            const newToggle = labelsToggle.cloneNode(true);
            labelsToggle.parentNode.replaceChild(newToggle, labelsToggle);
            
            // Add new listener
            newToggle.addEventListener('change', (e) => {
                this.showLabels = e.target.checked;
                if (this.currentCellar && this.currentInstanceMap && this.currentReferenceMap) {
                    this.renderCellarDetail(this.currentCellar, this.currentInstanceMap, this.currentReferenceMap);
                }
            });
            
            // Set initial state
            newToggle.checked = this.showLabels;
        }
    }


    renderStaggeredPosition(frontInstanceId, backInstanceId, instanceMap, referenceMap, shelfIndex, position) {
        const frontWine = frontInstanceId && instanceMap[frontInstanceId] ? referenceMap[instanceMap[frontInstanceId].referenceId] : null;
        const backWine = backInstanceId && instanceMap[backInstanceId] ? referenceMap[instanceMap[backInstanceId].referenceId] : null;
        
        const frontName = frontWine ? this.escapeHtml(frontWine.name || 'Unknown Wine') : '';
        const backName = backWine ? this.escapeHtml(backWine.name || 'Unknown Wine') : '';
        
        const frontImage = frontWine && frontWine.labelImageUrl ? this.escapeHtml(frontWine.labelImageUrl) : '';
        const backImage = backWine && backWine.labelImageUrl ? this.escapeHtml(backWine.labelImageUrl) : '';
        
        const frontType = frontWine ? (frontWine.type || '').toLowerCase() : '';
        const backType = backWine ? (backWine.type || '').toLowerCase() : '';
        const frontVintage = frontWine && frontWine.vintage ? frontWine.vintage : null;
        const backVintage = backWine && backWine.vintage ? backWine.vintage : null;
        
        const title = `Front: ${frontName || 'Empty'} | Back: ${backName || 'Empty'}`;
        
        // Staggered layout: 
        // Bottle radius = 2 units, diameter = 4 units = 80px
        // Position 0: front center at x=1 (draws 0-2), back center at x=2 (draws 1-3)
        // Position 1: front center at x=3 (draws 2-4), back center at x=4 (draws 3-5)
        // Position i: front center at x=2*i+1, back center at x=2*i+2
        // If bottle draws from 0-2 and center is at 1, then 1 unit = 40px (half of 80px diameter)
        const unitSize = 40; // pixels per unit (so x=1 = 40px, x=2 = 80px)
        const frontCenterX = (2 * position + 1) * unitSize; // in pixels
        const backCenterX = (2 * position + 2) * unitSize; // in pixels
        const radius = 40; // 40px radius = 80px diameter
        
        const frontPositionId = `wine-pos-${shelfIndex}-front-${position}`;
        const backPositionId = `wine-pos-${shelfIndex}-back-${position}`;
        
        if (this.showLabels) {
            // Labels mode - show wine label images
            return `
                <div class="wine-position-container staggered" data-position="${position}" title="${title}">
                    ${frontImage ? `
                        <div class="wine-position circle stagger-front" id="${frontPositionId}" style="left: ${frontCenterX - radius}px;"
                             data-wine-reference-id="${frontWine ? frontWine.id : ''}" data-wine-instance-id="${frontInstanceId || ''}">
                            <img src="${frontImage}" alt="${frontName}" class="wine-label-image" />
                        </div>
                    ` : `
                        <div class="wine-position circle empty stagger-front" style="left: ${frontCenterX - radius}px;"
                             data-shelf-index="${shelfIndex}" data-side="front" data-position="${position}" data-empty="true">
                            <div class="empty-circle"></div>
                        </div>
                    `}
                    ${backImage ? `
                        <div class="wine-position circle stagger-back" id="${backPositionId}" style="left: ${backCenterX - radius}px;"
                             data-wine-reference-id="${backWine ? backWine.id : ''}" data-wine-instance-id="${backInstanceId || ''}">
                            <img src="${backImage}" alt="${backName}" class="wine-label-image" />
                        </div>
                    ` : `
                        <div class="wine-position circle empty stagger-back" style="left: ${backCenterX - radius}px;"
                             data-shelf-index="${shelfIndex}" data-side="back" data-position="${position}" data-empty="true">
                            <div class="empty-circle"></div>
                        </div>
                    `}
                </div>
            `;
        } else {
            // Vintage mode - show vintage text with wine type colors
            const frontTypeClass = frontWine ? this.getWineTypeClass(frontType) : '';
            const backTypeClass = backWine ? this.getWineTypeClass(backType) : '';
            
            return `
                <div class="wine-position-container staggered" data-position="${position}" title="${title}">
                    ${frontWine && frontVintage ? `
                        <div class="wine-position circle stagger-front vintage-mode ${frontTypeClass}" id="${frontPositionId}" style="left: ${frontCenterX - radius}px;"
                             data-wine-reference-id="${frontWine.id}" data-wine-instance-id="${frontInstanceId || ''}">
                            <span class="vintage-text">${frontVintage}</span>
                        </div>
                    ` : `
                        <div class="wine-position circle empty stagger-front" style="left: ${frontCenterX - radius}px;"
                             data-shelf-index="${shelfIndex}" data-side="front" data-position="${position}" data-empty="true">
                            <div class="empty-circle"></div>
                        </div>
                    `}
                    ${backWine && backVintage ? `
                        <div class="wine-position circle stagger-back vintage-mode ${backTypeClass}" id="${backPositionId}" style="left: ${backCenterX - radius}px;"
                             data-wine-reference-id="${backWine.id}" data-wine-instance-id="${backInstanceId || ''}">
                            <span class="vintage-text">${backVintage}</span>
                        </div>
                    ` : `
                        <div class="wine-position circle empty stagger-back" style="left: ${backCenterX - radius}px;"
                             data-shelf-index="${shelfIndex}" data-side="back" data-position="${position}" data-empty="true">
                            <div class="empty-circle"></div>
                        </div>
                    `}
                </div>
            `;
        }
    }
}

export { CellarManager };
