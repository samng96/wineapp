/**
 * API client for communicating with the Flask backend
 */
const API_BASE_URL = 'http://localhost:5001';

class API {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Cellar endpoints
    async getCellars() {
        return this.request('/cellars');
    }

    async getCellar(id) {
        return this.request(`/cellars/${id}`);
    }

    async createCellar(cellar) {
        return this.request('/cellars', {
            method: 'POST',
            body: cellar
        });
    }

    async updateCellar(id, cellar) {
        return this.request(`/cellars/${id}`, {
            method: 'PUT',
            body: cellar
        });
    }

    async deleteCellar(id) {
        return this.request(`/cellars/${id}`, {
            method: 'DELETE'
        });
    }

    async getCellarLayout(id) {
        return this.request(`/cellars/${id}/layout`);
    }

    // Wine Reference endpoints
    async getWineReferences() {
        return this.request('/wine-references');
    }

    async getWineReference(id) {
        return this.request(`/wine-references/${id}`);
    }

    async createWineReference(reference) {
        return this.request('/wine-references', {
            method: 'POST',
            body: reference
        });
    }

    async updateWineReference(id, reference) {
        return this.request(`/wine-references/${id}`, {
            method: 'PUT',
            body: reference
        });
    }

    async deleteWineReference(id) {
        return this.request(`/wine-references/${id}`, {
            method: 'DELETE'
        });
    }

    // Wine Instance endpoints
    async getWineInstances() {
        return this.request('/wine-instances');
    }

    async getWineInstance(id) {
        return this.request(`/wine-instances/${id}`);
    }

    async createWineInstance(instance) {
        return this.request('/wine-instances', {
            method: 'POST',
            body: instance
        });
    }

    async updateWineInstance(id, instance) {
        return this.request(`/wine-instances/${id}`, {
            method: 'PUT',
            body: instance
        });
    }

    async deleteWineInstance(id) {
        return this.request(`/wine-instances/${id}`, {
            method: 'DELETE'
        });
    }

    async consumeWineInstance(id) {
        return this.request(`/wine-instances/${id}/consume`, {
            method: 'POST'
        });
    }

    async updateWineInstanceLocation(id, location) {
        return this.request(`/wine-instances/${id}/location`, {
            method: 'PUT',
            body: { location }
        });
    }

    // Unshelved endpoints
    async getUnshelved() {
        return this.request('/unshelved');
    }

    async assignUnshelvedToCellar(instanceId, location) {
        return this.request(`/unshelved/${instanceId}/assign`, {
            method: 'POST',
            body: { location }
        });
    }
}

// Export singleton instance
const api = new API();
