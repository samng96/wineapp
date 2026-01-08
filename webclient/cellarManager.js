// Cellar Management Module
import { Cellar } from './models/Cellar.js';
import { API } from './api.js';

class CellarManager {
    constructor() {
        this.cellars = [];
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
    }

    async loadCellars() {
        try {
            const data = await API.get('/cellars');
            this.cellars = data.map(c => Cellar.fromDict(c));
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

    renderCellars() {
        const container = document.getElementById('cellar-list');
        if (!container) return;

        if (this.cellars.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">No cellars yet. Click the + button to create one.</p>';
            return;
        }

        container.innerHTML = this.cellars.map(cellar => {
            const tempText = cellar.temperature ? `${cellar.temperature}°F` : 'Not set';
            const capacityText = `${cellar.capacity} bottles`;
            const shelfCount = cellar.shelves.length;
            const shelfText = shelfCount === 1 ? '1 shelf' : `${shelfCount} shelves`;

            return `
                <div class="list-item" data-cellar-id="${cellar.id}">
                    <div class="list-item-content">
                        <div class="list-item-title">${this.escapeHtml(cellar.name || 'Unnamed Cellar')}</div>
                        <div class="list-item-subtitle">${shelfText} • ${capacityText} • ${tempText}</div>
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
}

export { CellarManager };
