// API communication module
const API_BASE_URL = 'http://localhost:5001';

class API {
    static async get(endpoint) {
        try {
            console.log(`API.get: Fetching ${API_BASE_URL}${endpoint}`);
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            console.log(`API.get: Response status ${response.status} for ${endpoint}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API.get: Error response for ${endpoint}:`, errorText);
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`API.get: Successfully parsed JSON for ${endpoint}, data length:`, Array.isArray(data) ? data.length : 'not an array');
            return data;
        } catch (error) {
            console.error(`API.get: Exception fetching ${endpoint}:`, error);
            throw error;
        }
    }

    static async post(endpoint, data = null) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: data ? JSON.stringify(data) : undefined,
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: response.statusText }));
            throw new Error(error.error || `API Error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    }

    static async put(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: response.statusText }));
            throw new Error(error.error || `API Error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    }

    static async delete(endpoint) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: response.statusText }));
            throw new Error(error.error || `API Error: ${response.status} ${response.statusText}`);
        }
        // Handle empty response or JSON response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        // If no JSON, return success message
        return { message: 'Deleted successfully' };
    }

    // Wine Instance API methods
    
    /**
     * Mark a wine instance as consumed
     * @param {string} instanceId - Wine instance ID
     * @returns {Promise<Object>} Updated wine instance
     */
    static async consumeWineInstance(instanceId) {
        return await this.post(`/wine-instances/${instanceId}/consume`);
    }

    /**
     * Mark a wine instance as coravined
     * @param {string} instanceId - Wine instance ID
     * @returns {Promise<Object>} Updated wine instance
     */
    static async coravinWineInstance(instanceId) {
        return await this.post(`/wine-instances/${instanceId}/coravin`);
    }

    /**
     * Update wine instance location
     * @param {string} instanceId - Wine instance ID
     * @param {Object} locationData - Location data with oldCellarId (optional), newCellarId, shelfIndex, side, position
     * @returns {Promise<Object>} Updated wine instance
     */
    static async updateWineInstanceLocation(instanceId, locationData) {
        return await this.put(`/wine-instances/${instanceId}/location`, locationData);
    }

    /**
     * Update wine instance properties (price, purchaseDate, drinkByDate)
     * @param {string} instanceId - Wine instance ID
     * @param {Object} updateData - Data to update (price, purchaseDate, drinkByDate)
     * @returns {Promise<Object>} Updated wine instance
     */
    static async updateWineInstance(instanceId, updateData) {
        return await this.put(`/wine-instances/${instanceId}`, updateData);
    }

    /**
     * Create a new wine instance
     * @param {Object} instanceData - Instance data with referenceId, price (optional), purchaseDate (optional), drinkByDate (optional), location (optional)
     * @returns {Promise<Object>} Created wine instance
     */
    static async createWineInstance(instanceData) {
        return await this.post('/wine-instances', instanceData);
    }

    /**
     * Delete a wine instance
     * @param {string} instanceId - Wine instance ID
     * @returns {Promise<Object>} Deletion confirmation
     */
    static async deleteWineInstance(instanceId) {
        return await this.delete(`/wine-instances/${instanceId}`);
    }

    /**
     * Get all unshelved wine instances
     * @returns {Promise<Array>} Array of unshelved wine instances
     */
    static async getUnshelvedWineInstances() {
        return await this.get('/unshelved');
    }

    /**
     * Update wine reference rating
     * @param {string} referenceId - Wine reference ID
     * @param {number} rating - Rating from 1-5
     * @returns {Promise<Object>} Updated wine reference
     */
    static async updateWineReferenceRating(referenceId, rating) {
        return await this.put(`/wine-references/${referenceId}`, { rating });
    }

    /**
     * Update wine reference
     * @param {string} referenceId - Wine reference ID
     * @param {Object} updateData - Data to update (rating, tastingNotes, etc.)
     * @returns {Promise<Object>} Updated wine reference
     */
    static async updateWineReference(referenceId, updateData) {
        return await this.put(`/wine-references/${referenceId}`, updateData);
    }
}

export { API };
