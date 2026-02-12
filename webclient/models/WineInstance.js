import { WineReference } from './WineReference.js';
import { findInstanceLocation } from '../utils/locationUtils.js';

/**
 * WineInstance model - represents a wine instance (physical bottle)
 * 
 * @property {string} id - Unique identifier
 * @property {WineReference} reference - WineReference object (not ID)
 * @property {number|null} price - Purchase price
 * @property {string|null} purchaseDate - ISO 8601 date when purchased
 * @property {string|null} drinkByDate - ISO 8601 date when wine should be consumed by
 * @property {boolean} consumed - Whether the wine has been consumed
 * @property {string|null} consumedDate - ISO 8601 timestamp when consumed
 * @property {boolean} coravined - Whether the wine has been coravined
 * @property {string|null} coravinedDate - ISO 8601 timestamp when coravined
 * @property {string|null} storedDate - ISO 8601 timestamp when stored
 * @property {number} version - Version number for conflict resolution
 * @property {string|null} createdAt - ISO 8601 timestamp when created
 * @property {string|null} updatedAt - ISO 8601 timestamp when last updated
 */
export class WineInstance {
    constructor(id, reference, price = null, purchaseDate = null, 
                drinkByDate = null, consumed = false, consumedDate = null,
                coravined = false, coravinedDate = null,
                storedDate = null, version = 1, createdAt = null, updatedAt = null) {
        this.id = id;
        this.reference = reference; // WineReference object
        this.price = price;
        this.purchaseDate = purchaseDate;
        this.drinkByDate = drinkByDate;
        this.consumed = consumed;
        this.consumedDate = consumedDate;
        this.coravined = coravined;
        this.coravinedDate = coravinedDate;
        this.storedDate = storedDate;
        this.version = version;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    /**
     * Check if the wine instance is unshelved (not in any cellar)
     * Note: Location is no longer stored on the instance itself.
     * An instance is unshelved if it's not found in any cellar's shelves.
     * Consumed wines are never considered unshelved.
     * @param {Array<Cellar>} cellars - Array of all cellars to check
     * @returns {boolean} True if unshelved
     */
    isUnshelved(cellars = []) {
        // Consumed wines are not unshelved - they're consumed
        if (this.consumed) {
            return false;
        }
        
        // Check if this instance is in any cellar using utility function
        const location = findInstanceLocation(this, cellars);
        return location === null;
    }

    /**
     * Mark the wine instance as consumed
     */
    setConsumed() {
        this.consumed = true;
        this.consumedDate = new Date().toISOString();
    }

    /**
     * Mark the wine instance as coravined
     */
    setCoravined() {
        this.coravined = true;
        this.coravinedDate = new Date().toISOString();
    }

    /**
     * Convert WineInstance to dictionary format for API requests
     * Note: This extracts reference ID for API compatibility
     * Location is not included as it's tracked by cellar shelves, not the instance
     * @returns {Object} Dictionary representation
     */
    toDict() {
        return {
            id: this.id,
            referenceId: this.reference.userReferenceId || this.reference.id,
            price: this.price,
            purchaseDate: this.purchaseDate,
            drinkByDate: this.drinkByDate,
            consumed: this.consumed,
            consumedDate: this.consumedDate,
            coravined: this.coravined,
            coravinedDate: this.coravinedDate,
            storedDate: this.storedDate,
            version: this.version,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt
        };
    }

    /**
     * Create a WineInstance instance from API response dictionary
     * Note: This requires the reference to be resolved separately
     * Location is no longer stored on the instance - it's tracked by the cellar's shelves
     * @param {Object} dict - Dictionary from API response
     * @param {WineReference} reference - WineReference object (must be resolved separately)
     * @returns {WineInstance} WineInstance instance
     */
    static fromDict(dict, reference) {
        return new WineInstance(
            dict.id,
            reference, // Must be provided as WineReference object
            dict.price,
            dict.purchaseDate,
            dict.drinkByDate,
            dict.consumed || false,
            dict.consumedDate,
            dict.coravined || false,
            dict.coravinedDate,
            dict.storedDate,
            dict.version || 1,
            dict.createdAt,
            dict.updatedAt
        );
    }
}
