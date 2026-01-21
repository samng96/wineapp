import { Shelf } from './Shelf.js';
import { findInstanceLocationInCellar } from '../utils/locationUtils.js';

/**
 * Cellar model - represents a wine cellar
 * 
 * @property {string} id - Unique identifier
 * @property {string} name - Name of the cellar
 * @property {Array<Shelf>} shelves - List of shelves in the cellar
 * @property {number|null} temperature - Temperature in Fahrenheit
 * @property {number} capacity - Total bottle capacity (calculated from shelves)
 * @property {number} version - Version number for conflict resolution
 * @property {string|null} createdAt - ISO 8601 timestamp when created
 * @property {string|null} updatedAt - ISO 8601 timestamp when last updated
 */
export class Cellar {
    constructor(id, name, shelves, temperature = null, capacity = null, version = 1, createdAt = null, updatedAt = null) {
        this.id = id;
        this.name = name;
        this.shelves = shelves;
        this.temperature = temperature;
        this.version = version;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;

        // Calculate capacity if not provided
        if (capacity === null) {
            this.capacity = shelves.reduce((sum, shelf) => {
                return sum + shelf.positions * (shelf.isDouble ? 2 : 1);
            }, 0);
        } else {
            this.capacity = capacity;
        }
    }

    /**
     * Create a Cellar instance from API response dictionary
     * @param {Object} dict - Dictionary from API response
     * @returns {Cellar} Cellar instance
     */
    static fromDict(dict) {
        // Convert shelves from [positions, isDouble] format to Shelf objects
        const shelves = dict.shelves.map(shelfData => {
            const [positions, isDouble] = shelfData;
            return new Shelf(positions, isDouble);
        });

        // If winePositions are provided, populate them (for now we'll skip this as we need WineInstance objects)
        // This will be handled when we load full cellar details with wine instances

        const cellar = new Cellar(
            dict.id,
            dict.name,
            shelves,
            dict.temperature,
            dict.capacity,
            dict.version,
            dict.createdAt,
            dict.updatedAt
        );

        // Store winePositions for calculating used slots
        cellar.winePositions = dict.winePositions || {};

        return cellar;
    }

    /**
     * Calculate the number of used slots (positions with wine instances)
     * @returns {number} Number of used slots
     */
    getUsedSlots() {
        if (!this.winePositions || Object.keys(this.winePositions).length === 0) {
            return 0;
        }

        let used = 0;
        for (const shelfIndex in this.winePositions) {
            const shelfPositions = this.winePositions[shelfIndex];
            // Count non-null values in front, back, or single arrays
            if (shelfPositions.front) {
                used += shelfPositions.front.filter(id => id !== null && id !== undefined).length;
            }
            if (shelfPositions.back) {
                used += shelfPositions.back.filter(id => id !== null && id !== undefined).length;
            }
            if (shelfPositions.single) {
                used += shelfPositions.single.filter(id => id !== null && id !== undefined).length;
            }
        }
        return used;
    }

    /**
     * Calculate the number of free slots
     * @returns {number} Number of free slots
     */
    getFreeSlots() {
        return this.capacity - this.getUsedSlots();
    }

    /**
     * Get shelf by index
     * @private
     */
    _getShelf(shelfIndex) {
        if (shelfIndex >= 0 && shelfIndex < this.shelves.length) {
            return this.shelves[shelfIndex];
        }
        return null;
    }

    /**
     * Check if a position is valid for this cellar
     * @param {number} shelfIndex - Index of the shelf
     * @param {string} side - 'front', 'back', or 'single'
     * @param {number} position - Position index (0-based)
     * @returns {boolean} True if position is valid
     */
    isPositionValid(shelfIndex, side, position) {
        const shelf = this._getShelf(shelfIndex);
        if (!shelf) return false;

        if (shelf.isDouble) {
            if (side !== 'front' && side !== 'back') return false;
        } else {
            if (side !== 'single') return false;
        }

        if (position < 0 || position >= shelf.positions) return false;

        return true;
    }

    /**
     * Check if a position is available (not occupied)
     * @param {number} shelfIndex - Index of the shelf
     * @param {string} side - 'front', 'back', or 'single'
     * @param {number} position - Position index (0-based)
     * @returns {boolean} True if position is available
     */
    isPositionAvailable(shelfIndex, side, position) {
        if (!this.isPositionValid(shelfIndex, side, position)) {
            return false;
        }

        const shelf = this._getShelf(shelfIndex);
        const wine = shelf.getWineAt(side, position);
        return wine === null;
    }

    /**
     * Assign wine instance to a position
     * @param {number} shelfIndex - Index of the shelf
     * @param {string} side - 'front', 'back', or 'single'
     * @param {number} position - Position index (0-based)
     * @param {WineInstance} instance - Wine instance to assign
     * @throws {Error} If position is invalid or not available
     */
    assignWineToPosition(shelfIndex, side, position, instance) {
        if (!this.isPositionValid(shelfIndex, side, position)) {
            throw new Error(`Invalid position: shelfIndex=${shelfIndex}, side=${side}, position=${position}`);
        }
        if (!this.isPositionAvailable(shelfIndex, side, position)) {
            throw new Error(`Position is not available: shelfIndex=${shelfIndex}, side=${side}, position=${position}`);
        }

        const shelf = this._getShelf(shelfIndex);
        shelf.setWineAt(side, position, instance);
    }

    /**
     * Remove wine from a position
     * @param {number} shelfIndex - Index of the shelf
     * @param {string} side - 'front', 'back', or 'single'
     * @param {number} position - Position index (0-based)
     * @throws {Error} If position is invalid or empty
     */
    removeWineFromPosition(shelfIndex, side, position) {
        if (!this.isPositionValid(shelfIndex, side, position)) {
            throw new Error(`Invalid position: shelfIndex=${shelfIndex}, side=${side}, position=${position}`);
        }
        if (this.isPositionAvailable(shelfIndex, side, position)) {
            throw new Error(`Position is empty: shelfIndex=${shelfIndex}, side=${side}, position=${position}`);
        }

        const shelf = this._getShelf(shelfIndex);
        shelf.setWineAt(side, position, null);
    }

    /**
     * Check if a wine instance is in this cellar
     * @param {WineInstance} instance - Wine instance to check
     * @returns {boolean} True if instance is in this cellar
     */
    isWineInstanceInCellar(instance) {
        // Check winePositions data structure using utility function
        const location = findInstanceLocationInCellar(instance, this);
        if (location) {
            return true;
        }
        
        // Also check shelves if they have WineInstance objects
        for (const shelf of this.shelves) {
            if (shelf.winePositions) {
                for (const row of shelf.winePositions) {
                    for (const wine of row) {
                        if (wine && wine.id === instance.id) {
                            return true;
                        }
                    }
                }
            }
        }
        
        return false;
    }
}
