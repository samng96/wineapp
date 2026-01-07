/**
 * Main application logic
 */
let currentView = 'cellars';

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Initialize storage
        await storage.init();
        console.log('Storage initialized');

        // Initialize sync manager
        syncManager = new SyncManager(api, storage);
        syncManager.updateConnectionStatus();

        // Load initial data
        await loadData();

        // Setup event listeners
        setupNavigation();
        setupButtons();
        setupModal();

        // Auto-sync if online
        if (syncManager.isOnline) {
            await syncManager.sync();
            await loadData(); // Reload after sync
        }
    } catch (error) {
        console.error('Failed to initialize app:', error);
        alert('Failed to initialize app. Please refresh the page.');
    }
});

// Load data from local storage
async function loadData() {
    try {
        const [cellars, references, instances] = await Promise.all([
            storage.getCellars(),
            storage.getWineReferences(),
            storage.getWineInstances()
        ]);

        renderCellars(cellars);
        renderWines(references, instances);
        renderUnshelved(instances);
    } catch (error) {
        console.error('Failed to load data:', error);
    }
}

// Navigation
function setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
            
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function switchView(view) {
    currentView = view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`${view}-view`).classList.add('active');
}

// Button handlers
function setupButtons() {
    document.getElementById('add-cellar-btn').addEventListener('click', () => {
        showAddCellarModal();
    });

    document.getElementById('add-wine-btn').addEventListener('click', () => {
        showAddWineModal();
    });

    document.getElementById('sync-button').addEventListener('click', async () => {
        await syncManager.sync();
        await loadData();
    });
}

// Modal handling
function setupModal() {
    const overlay = document.getElementById('modal-overlay');
    const closeBtn = overlay.querySelector('.modal-close');
    
    closeBtn.addEventListener('click', () => {
        overlay.classList.add('hidden');
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.classList.add('hidden');
        }
    });
}

function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('modal-overlay').classList.remove('hidden');
}

// Rendering functions
function renderCellars(cellars) {
    const container = document.getElementById('cellars-list');
    
    if (cellars.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No cellars yet</h3><p>Create your first cellar to get started</p></div>';
        return;
    }

    container.innerHTML = cellars.map(cellar => `
        <div class="item-card" onclick="viewCellar('${cellar.id}')">
            <h3>${escapeHtml(cellar.name)}</h3>
            <p>Capacity: ${cellar.capacity || 'N/A'}</p>
            <p>Temperature: ${cellar.temperature ? cellar.temperature + '°F' : 'N/A'}</p>
            <p>Rows: ${cellar.rows ? cellar.rows.length : 0}</p>
        </div>
    `).join('');
}

function renderWines(references, instances) {
    const container = document.getElementById('wines-list');
    
    if (references.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No wines yet</h3><p>Add your first wine to get started</p></div>';
        return;
    }

    container.innerHTML = references.map(ref => {
        const refInstances = instances.filter(i => i.referenceId === ref.id && !i.consumed);
        return `
            <div class="item-card" onclick="viewWine('${ref.id}')">
                <h3>${escapeHtml(ref.name)}</h3>
                <p>${ref.producer || 'Unknown Producer'} - ${ref.vintage || 'N/A'}</p>
                <p>Type: ${ref.type || 'N/A'}</p>
                <p>Instances: ${refInstances.length}</p>
            </div>
        `;
    }).join('');
}

function renderUnshelved(instances) {
    const container = document.getElementById('unshelved-list');
    const unshelved = instances.filter(i => 
        i.location?.type === 'unshelved' && !i.consumed
    );
    
    if (unshelved.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No unshelved wines</h3><p>All wines are properly stored</p></div>';
        return;
    }

    // Group by reference (we'd need to fetch references, simplified for now)
    container.innerHTML = unshelved.map(instance => `
        <div class="item-card">
            <h3>Wine Instance</h3>
            <p>ID: ${instance.id}</p>
            <p>Price: ${instance.price ? '$' + instance.price : 'N/A'}</p>
        </div>
    `).join('');
}

// Modal content generators
function showAddCellarModal() {
    const content = `
        <form id="add-cellar-form">
            <div class="form-group">
                <label>Name</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Temperature (°F)</label>
                <input type="number" name="temperature">
            </div>
            <div class="form-group">
                <label>Capacity</label>
                <input type="number" name="capacity">
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Create</button>
            </div>
        </form>
    `;
    
    showModal('Add Cellar', content);
    
    document.getElementById('add-cellar-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const cellar = {
            name: formData.get('name'),
            temperature: formData.get('temperature') ? parseInt(formData.get('temperature')) : null,
            capacity: formData.get('capacity') ? parseInt(formData.get('capacity')) : null,
            rows: []
        };

        try {
            if (syncManager.isOnline) {
                const created = await api.createCellar(cellar);
                await storage.saveCellar(created);
            } else {
                await storage.saveCellar({ ...cellar, id: 'temp-' + Date.now() });
                await syncManager.queueOperation('create', 'cellar', null, cellar);
            }
            closeModal();
            await loadData();
        } catch (error) {
            alert('Failed to create cellar: ' + error.message);
        }
    });
}

function showAddWineModal() {
    const content = `
        <form id="add-wine-form">
            <div class="form-group">
                <label>Name *</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Type *</label>
                <select name="type" required>
                    <option value="">Select type</option>
                    <option value="Red">Red</option>
                    <option value="White">White</option>
                    <option value="Rosé">Rosé</option>
                    <option value="Sparkling">Sparkling</option>
                </select>
            </div>
            <div class="form-group">
                <label>Vintage *</label>
                <input type="number" name="vintage" min="1900" max="2099" required>
            </div>
            <div class="form-group">
                <label>Producer</label>
                <input type="text" name="producer">
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Create</button>
            </div>
        </form>
    `;
    
    showModal('Add Wine', content);
    
    document.getElementById('add-wine-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const reference = {
            name: formData.get('name'),
            type: formData.get('type'),
            vintage: parseInt(formData.get('vintage')),
            producer: formData.get('producer') || null
        };

        try {
            if (syncManager.isOnline) {
                const created = await api.createWineReference(reference);
                await storage.saveWineReference(created);
            } else {
                await storage.saveWineReference({ ...reference, id: 'temp-' + Date.now(), instanceCount: 0 });
                await syncManager.queueOperation('create', 'wineReference', null, reference);
            }
            closeModal();
            await loadData();
        } catch (error) {
            alert('Failed to create wine: ' + error.message);
        }
    });
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

function viewCellar(id) {
    // TODO: Implement cellar detail view
    console.log('View cellar:', id);
}

function viewWine(id) {
    // TODO: Implement wine detail view
    console.log('View wine:', id);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
