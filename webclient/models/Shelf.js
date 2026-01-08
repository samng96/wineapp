/**
 * Shelf model - represents a shelf in a cellar
 * 
 * @property {number} positions - Number of bottle positions per side (immutable)
 * @property {boolean} isDouble - True if shelf has front/back, False if single-sided (immutable)
 * @property {Array<Array<WineInstance|null>>} winePositions - 2D array: rows x positions (mutable)
 *   - For isDouble=false: 1 row (single side)
 *   - For isDouble=true: 2 rows (front=row 0, back=row 1)
 */
export class Shelf {
    constructor(positions, isDouble, winePositions = null) {
        if (positions <= 0 || !Number.isInteger(positions)) {
            throw new Error('Positions must be a positive integer');
        }
        if (typeof isDouble !== 'boolean') {
            throw new Error('isDouble must be a boolean');
        }

        // Make positions and isDouble immutable
        Object.defineProperty(this, 'positions', {
            value: positions,
            writable: false,
            enumerable: true,
            configurable: false
        });

        Object.defineProperty(this, 'isDouble', {
            value: isDouble,
            writable: false,
            enumerable: true,
            configurable: false
        });

        // Initialize wine_positions if not provided
        if (!winePositions) {
            if (isDouble) {
                // 2 rows (front and back), each with 'positions' columns
                this.winePositions = Array(2).fill(null).map(() => Array(positions).fill(null));
            } else {
                // 1 row (single), with 'positions' columns
                this.winePositions = [Array(positions).fill(null)];
            }
        } else {
            this.winePositions = winePositions;
        }
    }

    /**
     * Convert side string to row index
     * @private
     */
    _getRowIndex(side) {
        if (this.isDouble) {
            if (side === 'front') return 0;
            if (side === 'back') return 1;
            throw new Error(`Invalid side '${side}' for double shelf. Must be 'front' or 'back'`);
        } else {
            if (side === 'single') return 0;
            throw new Error(`Invalid side '${side}' for single shelf. Must be 'single'`);
        }
    }

    /**
     * Get wine instance at position
     * @param {string} side - 'front', 'back', or 'single'
     * @param {number} position - Position index (0-based)
     * @returns {WineInstance|null} Wine instance or null if empty
     */
    getWineAt(side, position) {
        if (position < 0 || position >= this.positions) {
            throw new Error(`Position ${position} out of range [0, ${this.positions})`);
        }
        const rowIndex = this._getRowIndex(side);
        return this.winePositions[rowIndex][position];
    }

    /**
     * Set wine instance at position
     * @param {string} side - 'front', 'back', or 'single'
     * @param {number} position - Position index (0-based)
     * @param {WineInstance|null} instance - Wine instance to set, or null to clear
     */
    setWineAt(side, position, instance) {
        if (position < 0 || position >= this.positions) {
            throw new Error(`Position ${position} out of range [0, ${this.positions})`);
        }
        const rowIndex = this._getRowIndex(side);
        this.winePositions[rowIndex][position] = instance;
    }
}
