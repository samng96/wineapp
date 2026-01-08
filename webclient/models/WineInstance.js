/**
 * WineInstance model - represents a wine instance (physical bottle)
 * 
 * @property {string} id - Unique identifier
 * @property {WineReference} reference - WineReference object this instance belongs to
 * @property {Object|null} location - Location object with:
 *   - cellarId (string): ID of the cellar
 *   - shelfIndex (number): Index of the shelf in the cellar
 *   - position (number): Position number on the shelf
 *   - isFront (boolean): True if on front side (or single shelf), False if on back side
 *   - null if instance is unshelved
 * @property {number|null} price - Purchase price
 * @property {string|null} purchaseDate - ISO 8601 date when purchased
 * @property {string|null} drinkByDate - ISO 8601 date for recommended consumption
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
        this.reference = reference;
        this.location = location;
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
     * Check if instance is in a cellar
     * @returns {boolean} True if location is not null
     */
    isInCellar() {
        return this.location !== null;
    }

    /**
     * Check if instance is unshelved
     * @returns {boolean} True if location is null
     */
    isUnshelved() {
        return this.location === null;
    }
}
