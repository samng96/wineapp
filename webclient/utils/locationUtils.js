/**
 * Location utility functions for finding wine instance locations in cellars
 */

/**
 * Find the location of a wine instance within a specific cellar
 * @param {Object} instance - Wine instance object with an id property
 * @param {Object} cellar - Cellar object with winePositions property
 * @returns {Object|null} Location object with { cellar, shelfIndex, side, position } or null if not found
 */
export function findInstanceLocationInCellar(instance, cellar) {
    if (!cellar || !cellar.winePositions || !instance || !instance.id) return null;
    
    try {
        for (const shelfIndex in cellar.winePositions) {
            const shelfPositions = cellar.winePositions[shelfIndex];
            if (!shelfPositions) continue;
            
            for (const side of ['front', 'back', 'single']) {
                const positions = shelfPositions[side] || [];
                const position = positions.indexOf(instance.id);
                if (position !== -1) {
                    return {
                        cellar,
                        shelfIndex: parseInt(shelfIndex),
                        side,
                        position
                    };
                }
            }
        }
    } catch (error) {
        console.error('Error in findInstanceLocationInCellar:', error);
        return null;
    }
    return null;
}

/**
 * Find the location of a wine instance across all cellars
 * @param {Object} instance - Wine instance object with an id property
 * @param {Array<Object>} cellars - Array of cellar objects
 * @returns {Object|null} Location object with { cellar, shelfIndex, side, position } or null if unshelved
 */
export function findInstanceLocation(instance, cellars) {
    if (!instance || !instance.id || !cellars || !Array.isArray(cellars)) return null;
    
    for (const cellar of cellars) {
        const location = findInstanceLocationInCellar(instance, cellar);
        if (location) {
            return location;
        }
    }
    return null;
}
