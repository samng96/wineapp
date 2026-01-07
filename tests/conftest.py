"""Pytest configuration and fixtures"""
import pytest
import os
import json
import tempfile
import shutil
import sys

# Add server directory to path so we can import server modules
server_dir = os.path.join(os.path.dirname(__file__), '..', 'server')
sys.path.insert(0, server_dir)

from app import app

@pytest.fixture
def client():
    """Create a test client"""
    # Create temporary directory for test data files
    test_dir = tempfile.mkdtemp()
    
    # Change to test directory and create test data files
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    # Initialize empty data files
    for filename in ['cellars.json', 'wine-references.json', 'wine-instances.json']:
        with open(filename, 'w') as f:
            json.dump([], f)
    
    # Create Flask test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    
    # Cleanup: restore original directory and remove test directory
    os.chdir(original_dir)
    shutil.rmtree(test_dir)

@pytest.fixture
def sample_cellar():
    """Sample cellar data for testing"""
    return {
        'name': 'Test Cellar',
        'temperature': 55,
        'capacity': 100,
        'rows': [
            {
                'id': 'row-1',
                'bottlesPerSide': 50,
                'sides': 'front-back',
                'winePositions': {
                    'front': [None] * 50,
                    'back': [None] * 50
                }
            }
        ]
    }

@pytest.fixture
def sample_wine_reference():
    """Sample wine reference data for testing"""
    return {
        'name': 'Test Wine',
        'type': 'Red',
        'vintage': 2020,
        'producer': 'Test Winery',
        'varietals': ['Cabernet Sauvignon'],
        'region': 'Napa Valley',
        'country': 'USA',
        'rating': 4,
        'tastingNotes': 'Full-bodied with notes of blackberry'
    }

@pytest.fixture
def sample_wine_instance():
    """Sample wine instance data for testing"""
    return {
        'referenceId': None,  # Will be set in tests
        'location': {'type': 'unshelved'},
        'price': 25.99,
        'purchaseDate': '2024-01-15',
        'drinkByDate': '2025-12-31'
    }
