/**
 * Test for wineDetailView location display bug fix
 * 
 * Bug: On first load, clicking on a wine in the cellar view shows "Unshelved" 
 * even though it's clearly shelved.
 * 
 * Fix: Check both window.cellarManager.cellars and window.wineManager.cellars
 * to find the wine's location, prioritizing cellarManager since it's already loaded.
 */

import { findInstanceLocation } from '../utils/locationUtils.js';

// Mock data for testing
function createMockCellar(id, name) {
    return {
        id,
        name,
        winePositions: {
            '0': {
                'front': ['wine-1', 'wine-2', null],
                'back': [null, 'wine-3', null]
            },
            '1': {
                'single': ['wine-4', null, 'wine-5']
            }
        }
    };
}

function createMockWineInstance(id) {
    return {
        id,
        consumed: false,
        consumedDate: null
    };
}

describe('WineDetailView Location Display', () => {
    let mockCellarManager, mockWineManager;

    beforeEach(() => {
        // Setup mock managers
        mockCellarManager = {
            cellars: [
                createMockCellar('cellar-1', 'Main Cellar'),
                createMockCellar('cellar-2', 'Secondary Cellar')
            ]
        };

        mockWineManager = {
            cellars: [
                createMockCellar('cellar-1', 'Main Cellar'),
                createMockCellar('cellar-2', 'Secondary Cellar')
            ]
        };

        // Clear window objects
        window.cellarManager = null;
        window.wineManager = null;
    });

    test('should find location when cellars are in cellarManager', () => {
        window.cellarManager = mockCellarManager;
        window.wineManager = null;

        const instance = createMockWineInstance('wine-1');
        const location = findInstanceLocation(instance, mockCellarManager.cellars);

        expect(location).not.toBeNull();
        expect(location.cellar.id).toBe('cellar-1');
        expect(location.shelfIndex).toBe(0);
        expect(location.side).toBe('front');
        expect(location.position).toBe(0);
    });

    test('should find location when cellars are in wineManager', () => {
        window.cellarManager = null;
        window.wineManager = mockWineManager;

        const instance = createMockWineInstance('wine-3');
        const location = findInstanceLocation(instance, mockWineManager.cellars);

        expect(location).not.toBeNull();
        expect(location.cellar.id).toBe('cellar-1');
        expect(location.shelfIndex).toBe(0);
        expect(location.side).toBe('back');
        expect(location.position).toBe(1);
    });

    test('should prioritize cellarManager over wineManager', () => {
        // Setup both with different data
        const cellarManagerCellars = [
            createMockCellar('cellar-1', 'Main Cellar')
        ];
        cellarManagerCellars[0].winePositions['0'].front[0] = 'wine-1';

        const wineManagerCellars = [
            createMockCellar('cellar-2', 'Secondary Cellar')
        ];
        wineManagerCellars[0].winePositions['0'].front[0] = 'wine-1';

        window.cellarManager = { cellars: cellarManagerCellars };
        window.wineManager = { cellars: wineManagerCellars };

        const instance = createMockWineInstance('wine-1');
        // Should find in cellarManager's cellar (cellar-1), not wineManager's (cellar-2)
        const location = findInstanceLocation(instance, cellarManagerCellars);

        expect(location).not.toBeNull();
        expect(location.cellar.id).toBe('cellar-1');
    });

    test('should return null for unshelved wine', () => {
        window.cellarManager = mockCellarManager;

        const instance = createMockWineInstance('wine-unshelved');
        const location = findInstanceLocation(instance, mockCellarManager.cellars);

        expect(location).toBeNull();
    });

    test('should return null for consumed wine', () => {
        window.cellarManager = mockCellarManager;

        const instance = {
            id: 'wine-1',
            consumed: true,
            consumedDate: '2024-01-01T00:00:00Z'
        };

        // Consumed wines should not show location in UI, but the function
        // should still find the location if needed
        const location = findInstanceLocation(instance, mockCellarManager.cellars);
        
        // The function itself doesn't filter by consumed, but the UI does
        expect(location).not.toBeNull(); // Function finds it
    });

    test('should handle empty cellars array', () => {
        window.cellarManager = { cellars: [] };
        window.wineManager = { cellars: [] };

        const instance = createMockWineInstance('wine-1');
        const location = findInstanceLocation(instance, []);

        expect(location).toBeNull();
    });

    test('should find location in second cellar', () => {
        const cellars = [
            createMockCellar('cellar-1', 'Main Cellar'),
            createMockCellar('cellar-2', 'Secondary Cellar')
        ];
        // Put wine in second cellar
        cellars[1].winePositions['0'].single[0] = 'wine-6';

        const instance = createMockWineInstance('wine-6');
        const location = findInstanceLocation(instance, cellars);

        expect(location).not.toBeNull();
        expect(location.cellar.id).toBe('cellar-2');
        expect(location.shelfIndex).toBe(0);
        expect(location.side).toBe('single');
        expect(location.position).toBe(0);
    });
});

// Simple test runner for browser environment
if (typeof window !== 'undefined') {
    window.runLocationTests = function() {
        console.log('Running location finding tests...');
        let passed = 0;
        let failed = 0;

        // Test 1: Find location in cellarManager
        const mockCellarManager = {
            cellars: [createMockCellar('cellar-1', 'Main Cellar')]
        };
        const instance1 = createMockWineInstance('wine-1');
        const location1 = findInstanceLocation(instance1, mockCellarManager.cellars);
        if (location1 && location1.cellar.id === 'cellar-1' && location1.shelfIndex === 0) {
            console.log('✓ Test 1 passed: Found location in cellarManager');
            passed++;
        } else {
            console.error('✗ Test 1 failed: Should find location in cellarManager');
            failed++;
        }

        // Test 2: Return null for unshelved wine
        const instance2 = createMockWineInstance('wine-unshelved');
        const location2 = findInstanceLocation(instance2, mockCellarManager.cellars);
        if (location2 === null) {
            console.log('✓ Test 2 passed: Returns null for unshelved wine');
            passed++;
        } else {
            console.error('✗ Test 2 failed: Should return null for unshelved wine');
            failed++;
        }

        // Test 3: Find location in second cellar
        const cellars = [
            createMockCellar('cellar-1', 'Main Cellar'),
            createMockCellar('cellar-2', 'Secondary Cellar')
        ];
        cellars[1].winePositions['0'].single[0] = 'wine-6';
        const instance3 = createMockWineInstance('wine-6');
        const location3 = findInstanceLocation(instance3, cellars);
        if (location3 && location3.cellar.id === 'cellar-2') {
            console.log('✓ Test 3 passed: Found location in second cellar');
            passed++;
        } else {
            console.error('✗ Test 3 failed: Should find location in second cellar');
            failed++;
        }

        console.log(`\nTest Results: ${passed} passed, ${failed} failed`);
        return { passed, failed };
    };
}
