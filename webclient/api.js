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

    static async post(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
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
}

export { API };
