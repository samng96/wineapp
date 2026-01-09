// Cellar Management Module
import { Cellar } from './models/Cellar.js';
import { API } from './api.js';

class CellarManager {
    constructor() {
        this.cellars = [];
        this.wineInstances = []; // Cache wine instances for breakdown calculation
        this.wineReferences = []; // Cache wine references for breakdown calculation
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

        // Cellar name click handler (delegated - will be set up after rendering)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('cellar-name-link')) {
                const cellarId = e.target.getAttribute('data-cellar-id');
                if (cellarId) {
                    this.showCellarDetail(cellarId);
                }
            }
        });
    }

    async loadCellars() {
        try {
            const data = await API.get('/cellars');
            this.cellars = data.map(c => Cellar.fromDict(c));
            
            // Load wine instances and references for breakdown calculation
            try {
                this.wineInstances = await API.get('/wine-instances');
                this.wineReferences = await API.get('/wine-references');
            } catch (err) {
                console.warn('Could not load wine data for breakdown:', err);
                // Continue without breakdown data
            }
            
            this.renderCellars();
        } catch (error) {
            console.error('Error loading cellars:', error);
            // Don't show error alert on initial load - just log it
            // The view will show an empty state or error message
            const container = document.getElementById('cellar-list');
            if (container) {
                container.innerHTML = '<p style="text-align: center; color: #f44336; padding: 40px;">Failed to load cellars. Please make sure the server is running.</p>';
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
                const wineType = referenceTypeMap[instance.referenceId] || 'Unknown';
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

        if (this.cellars.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">No cellars yet. Click the + button to create one.</p>';
            return;
        }

        container.innerHTML = this.cellars.map(cellar => {
            const tempText = cellar.temperature ? `${cellar.temperature}°F` : 'Not set';
            const shelfCount = cellar.shelves.length;
            const shelfText = shelfCount === 1 ? '1 shelf' : `${shelfCount} shelves`;
            
            // Calculate used slots and show as used/capacity
            const usedSlots = cellar.getUsedSlots();
            const capacity = cellar.capacity;
            const usageText = `${usedSlots} stored bottles ${capacity} total slots`;
            
            // Calculate wine breakdown for tooltip
            const breakdown = this.getWineBreakdown(cellar);
            const breakdownText = this.formatBreakdown(breakdown);
            const tooltipText = breakdownText ? `Breakdown: ${breakdownText}` : 'No wines in cellar';

            return `
                <div class="list-item" data-cellar-id="${cellar.id}">
                    <div class="list-item-content">
                        <div class="list-item-title cellar-name-link" data-cellar-id="${cellar.id}" style="cursor: pointer; color: #6200ea; text-decoration: underline;">${this.escapeHtml(cellar.name || 'Unnamed Cellar')}</div>
                        <div class="list-item-subtitle">
                            ${shelfText} • 
                            <span class="usage-text" title="${this.escapeHtml(tooltipText)}">${usageText}</span> • 
                            ${tempText}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="list-item-btn" onclick="window.cellarManager.showEditDialog('${cellar.id}')" title="Edit">✏️</button>
                        <button class="list-item-btn" onclick="window.cellarManager.showDeleteDialog('${cellar.id}')" title="Delete">🗑️</button>
                    </div>
                </div>
            `;
        }).join('');
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
        if (!cellar) return;

        const dialog = document.getElementById('edit-cellar-dialog');
        const form = document.getElementById('edit-cellar-form');
        if (dialog && form) {
            form.dataset.cellarId = cellarId;
            form.querySelector('#edit-cellar-name').value = cellar.name || '';
            form.querySelector('#edit-cellar-temperature').value = cellar.temperature || '';
            dialog.classList.remove('hidden');
        }
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
        if (!cellar) return;

        const dialog = document.getElementById('delete-cellar-dialog');
        const message = dialog.querySelector('.delete-message');
        if (dialog && message) {
            dialog.dataset.cellarId = cellarId;
            message.textContent = `Are you sure you want to delete "${this.escapeHtml(cellar.name || 'Unnamed Cellar')}"? This will move all wines in this cellar to unshelved.`;
            dialog.classList.remove('hidden');
        }
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

    async showCellarDetail(cellarId) {
        try {
            // Load full cellar data with wine instances
            const cellar = await API.get(`/cellars/${cellarId}`);
            
            // Load wine instances and references to get label images
            const [wineInstances, wineReferences] = await Promise.all([
                API.get('/wine-instances'),
                API.get('/wine-references')
            ]);

            // Create maps for quick lookup
            const instanceMap = {};
            wineInstances.forEach(inst => {
                instanceMap[inst.id] = inst;
            });

            const referenceMap = {};
            wineReferences.forEach(ref => {
                referenceMap[ref.id] = ref;
            });

            // Update view header
            const nameHeader = document.getElementById('cellar-detail-name');
            if (nameHeader) {
                nameHeader.textContent = cellar.name || 'Unnamed Cellar';
            }

            // Render cellar shelves
            this.renderCellarDetail(cellar, instanceMap, referenceMap);

            // Switch to cellar detail view
            if (window.app && window.app.showView) {
                window.app.showView('cellar-detail');
            }
        } catch (error) {
            console.error('Error loading cellar detail:', error);
            alert('Failed to load cellar details. Please try again.');
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

        let html = '';
        
        shelves.forEach((shelfConfig, shelfIndex) => {
            const [positions, isDouble] = shelfConfig;
            const shelfKey = String(shelfIndex);
            const shelfData = winePositions[shelfKey] || {};

            html += `<div class="shelf-row">`;
            html += `<div class="shelf-label">Shelf ${shelfIndex + 1}${isDouble ? ' (Double-sided)' : ''}</div>`;
            html += `<div class="shelf-positions-container">`;

            if (isDouble) {
                // Front side
                html += `<div class="shelf-side">`;
                html += `<div class="side-label">Front</div>`;
                html += `<div class="positions-row">`;
                for (let pos = 0; pos < positions; pos++) {
                    const frontPositions = shelfData.front || [];
                    const instanceId = frontPositions[pos] || null;
                    html += this.renderPosition(instanceId, instanceMap, referenceMap, shelfIndex, 'front', pos);
                }
                html += `</div></div>`;

                // Back side
                html += `<div class="shelf-side">`;
                html += `<div class="side-label">Back</div>`;
                html += `<div class="positions-row">`;
                for (let pos = 0; pos < positions; pos++) {
                    const backPositions = shelfData.back || [];
                    const instanceId = backPositions[pos] || null;
                    html += this.renderPosition(instanceId, instanceMap, referenceMap, shelfIndex, 'back', pos);
                }
                html += `</div></div>`;
            } else {
                // Single side
                html += `<div class="shelf-side">`;
                html += `<div class="positions-row">`;
                const singlePositions = shelfData.single || [];
                for (let pos = 0; pos < positions; pos++) {
                    const instanceId = singlePositions[pos] || null;
                    html += this.renderPosition(instanceId, instanceMap, referenceMap, shelfIndex, 'single', pos);
                }
                html += `</div></div>`;
            }

            html += `</div></div>`;
        });

        container.innerHTML = html;
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
                return `<div class="wine-position empty" title="Wine (no image)"><div class="empty-circle"></div></div>`;
            }
        } else {
            // Empty position
            return `<div class="wine-position empty" title="Empty position"><div class="empty-circle"></div></div>`;
        }
    }
}

export { CellarManager };
