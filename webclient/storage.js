/**
 * Local storage manager using IndexedDB for offline support
 */
class Storage {
    constructor() {
        this.dbName = 'WineAppDB';
        this.dbVersion = 1;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores
                if (!db.objectStoreNames.contains('cellars')) {
                    db.createObjectStore('cellars', { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains('wineReferences')) {
                    db.createObjectStore('wineReferences', { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains('wineInstances')) {
                    db.createObjectStore('wineInstances', { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains('syncQueue')) {
                    db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
                }
                if (!db.objectStoreNames.contains('metadata')) {
                    db.createObjectStore('metadata', { keyPath: 'key' });
                }
            };
        });
    }

    // Generic CRUD operations
    async getAll(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async get(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(id);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async put(storeName, item) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(item);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async delete(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(id);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    // Cellar operations
    async getCellars() {
        return this.getAll('cellars');
    }

    async getCellar(id) {
        return this.get('cellars', id);
    }

    async saveCellar(cellar) {
        return this.put('cellars', cellar);
    }

    async deleteCellar(id) {
        return this.delete('cellars', id);
    }

    // Wine Reference operations
    async getWineReferences() {
        return this.getAll('wineReferences');
    }

    async getWineReference(id) {
        return this.get('wineReferences', id);
    }

    async saveWineReference(reference) {
        return this.put('wineReferences', reference);
    }

    async deleteWineReference(id) {
        return this.delete('wineReferences', id);
    }

    // Wine Instance operations
    async getWineInstances() {
        return this.getAll('wineInstances');
    }

    async getWineInstance(id) {
        return this.get('wineInstances', id);
    }

    async saveWineInstance(instance) {
        return this.put('wineInstances', instance);
    }

    async deleteWineInstance(id) {
        return this.delete('wineInstances', id);
    }

    // Sync queue operations
    async addToSyncQueue(operation) {
        return this.put('syncQueue', {
            ...operation,
            timestamp: new Date().toISOString()
        });
    }

    async getSyncQueue() {
        return this.getAll('syncQueue');
    }

    async removeFromSyncQueue(id) {
        return this.delete('syncQueue', id);
    }

    // Metadata operations
    async getMetadata(key) {
        const result = await this.get('metadata', key);
        return result ? result.value : null;
    }

    async setMetadata(key, value) {
        return this.put('metadata', { key, value });
    }

    async getLastSyncTimestamp() {
        return this.getMetadata('lastSyncTimestamp');
    }

    async setLastSyncTimestamp(timestamp) {
        return this.setMetadata('lastSyncTimestamp', timestamp);
    }
}

// Export singleton instance
const storage = new Storage();
