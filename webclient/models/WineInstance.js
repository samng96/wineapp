import { WineReference } from './WineReference.js';

/**
 * WineInstance model - represents a wine instance (physical bottle)
 * 
 * @property {string} id - Unique identifier
 * @property {WineReference} reference - WineReference object (not ID)
 * @property {Object|null} location - Location object with {cellar, shelf, position, isFront} or null for unshelved
 * @property {number|null} price - Purchase price
 * @property {string|null} purchaseDate - ISO 8601 date when purchased
 * @property {string|null} drinkByDate - ISO 8601 date when wine should be consumed by
 * @property {boolean} consumed - Whether the wine has been consumed
 * @property {string|null} consumedDate - ISO 8601 timestamp when consumed
 * @property {string|null} storedDate - ISO 8601 timestamp when stored
 * @property {number} version - Version number for conflict resolution
 * @property {string|null} createdAt - ISO 8601 timestamp when created
 * @property {string|null} updatedAt - ISO 8601 timestamp when last updated
 */
export class WineInstance {
    constructor(id, reference, location = null, price = null, purchaseDate = null, 
                drinkByDate = null, consumed = false, consumedDate = null, 
                storedDate = null, version = 1, createdAt = null, updatedAt = null) {
        this.id = id;
        this.reference = reference; // WineReference object
        this.location = location; // {cellar, shelf, position, isFront} or null
        this.price = price;
        this.purchaseDate = purchaseDate;
        this.drinkByDate = drinkByDate;
        this.consumed = consumed;
        this.consumedDate = consumedDate;
        this.storedDate = storedDate;
        this.version = version;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    /**
     * Check if the wine instance is unshelved (not in a cellar)
     * @returns {boolean} True if unshelved
     */
    isUnshelved() {
        return this.location === null;
    }

    /**
     * Create a WineInstance instance from API response dictionary
     * Note: This requires the reference to be resolved separately
     * @param {Object} dict - Dictionary from API response
     * @param {WineReference} reference - WineReference object (must be resolved separately)
     * @returns {WineInstance} WineInstance instance
     */
    static fromDict(dict, reference) {
        // Parse location if present
        let location = null;
        if (dict.location) {
            // Location format from API: {cellarId, shelfIndex, position, isFront}
            // We'll store it as-is for now, and resolve cellar/shelf objects when needed
            location = dict.location;
        }

        return new WineInstance(
            dict.id,
            reference, // Must be provided as WineReference object
            location,
            dict.price,
            dict.purchaseDate,
            dict.drinkByDate,
            dict.consumed || false,
            dict.consumedDate,
            dict.storedDate,
            dict.version,
            dict.createdAt,
            dict.updatedAt
        );
    }
}
