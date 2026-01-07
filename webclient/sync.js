/**
 * Synchronization manager for offline/online sync
 */
class SyncManager {
    constructor(api, storage) {
        this.api = api;
        this.storage = storage;
        this.isOnline = navigator.onLine;
        this.syncing = false;
        this.setupEventListeners();
    }

    setupEventListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateConnectionStatus();
            this.sync();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateConnectionStatus();
        });
    }

    updateConnectionStatus() {
        const statusEl = document.getElementById('connection-status');
        const syncBtn = document.getElementById('sync-button');
        
        if (this.isOnline) {
            statusEl.textContent = 'Online';
            statusEl.className = 'status-indicator online';
            syncBtn.disabled = false;
        } else {
            statusEl.textContent = 'Offline';
            statusEl.className = 'status-indicator offline';
            syncBtn.disabled = true;
        }
    }

    async sync() {
        if (!this.isOnline || this.syncing) {
            return;
        }

        this.syncing = true;
        const syncBtn = document.getElementById('sync-button');
        syncBtn.disabled = true;
        syncBtn.textContent = 'Syncing...';

        try {
            // Process sync queue (local changes to push)
            await this.pushLocalChanges();

            // Pull server changes
            await this.pullServerChanges();

            // Update last sync timestamp
            await this.storage.setLastSyncTimestamp(new Date().toISOString());

            console.log('Sync completed successfully');
        } catch (error) {
            console.error('Sync failed:', error);
            alert('Sync failed. Please try again.');
        } finally {
            this.syncing = false;
            syncBtn.disabled = false;
            syncBtn.textContent = 'Sync';
        }
    }

    async pushLocalChanges() {
        const queue = await this.storage.getSyncQueue();
        
        for (const operation of queue) {
            try {
                switch (operation.type) {
                    case 'create':
                        await this.executeCreate(operation);
                        break;
                    case 'update':
                        await this.executeUpdate(operation);
                        break;
                    case 'delete':
                        await this.executeDelete(operation);
                        break;
                }
                // Remove from queue on success
                await this.storage.removeFromSyncQueue(operation.id);
            } catch (error) {
                console.error(`Failed to sync operation ${operation.id}:`, error);
                // Keep in queue for retry
            }
        }
    }

    async executeCreate(operation) {
        switch (operation.entityType) {
            case 'cellar':
                const cellar = await this.api.createCellar(operation.data);
                await this.storage.saveCellar(cellar);
                break;
            case 'wineReference':
                const reference = await this.api.createWineReference(operation.data);
                await this.storage.saveWineReference(reference);
                break;
            case 'wineInstance':
                const instance = await this.api.createWineInstance(operation.data);
                await this.storage.saveWineInstance(instance);
                break;
        }
    }

    async executeUpdate(operation) {
        switch (operation.entityType) {
            case 'cellar':
                const cellar = await this.api.updateCellar(operation.entityId, operation.data);
                await this.storage.saveCellar(cellar);
                break;
            case 'wineReference':
                const reference = await this.api.updateWineReference(operation.entityId, operation.data);
                await this.storage.saveWineReference(reference);
                break;
            case 'wineInstance':
                const instance = await this.api.updateWineInstance(operation.entityId, operation.data);
                await this.storage.saveWineInstance(instance);
                break;
        }
    }

    async executeDelete(operation) {
        switch (operation.entityType) {
            case 'cellar':
                await this.api.deleteCellar(operation.entityId);
                await this.storage.deleteCellar(operation.entityId);
                break;
            case 'wineReference':
                await this.api.deleteWineReference(operation.entityId);
                await this.storage.deleteWineReference(operation.entityId);
                break;
            case 'wineInstance':
                await this.api.deleteWineInstance(operation.entityId);
                await this.storage.deleteWineInstance(operation.entityId);
                break;
        }
    }

    async pullServerChanges() {
        const lastSync = await this.storage.getLastSyncTimestamp();
        
        // For now, pull all data (we'll implement incremental sync later)
        const [cellars, references, instances] = await Promise.all([
            this.api.getCellars(),
            this.api.getWineReferences(),
            this.api.getWineInstances()
        ]);

        // Save to local storage
        for (const cellar of cellars) {
            await this.storage.saveCellar(cellar);
        }
        for (const reference of references) {
            await this.storage.saveWineReference(reference);
        }
        for (const instance of instances) {
            await this.storage.saveWineInstance(instance);
        }
    }

    async queueOperation(type, entityType, entityId, data) {
        await this.storage.addToSyncQueue({
            type,
            entityType,
            entityId,
            data
        });

        // If online, try to sync immediately
        if (this.isOnline) {
            this.sync();
        }
    }
}

// Export singleton instance (will be initialized in app.js)
let syncManager = null;
