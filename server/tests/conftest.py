"""Pytest configuration and fixtures"""
import pytest
import os
import json
import tempfile
import shutil
import sys

# Add parent directory (server/) to path so we can import server modules
server_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, server_dir)

# Set environment variable to prevent init_data_files from creating files in root
os.environ['TESTING'] = '1'

from app import app

# Get the project root directory for cleanup
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
PROJECT_ROOT = os.path.abspath(PROJECT_ROOT)
JSON_FILES_TO_CLEAN = ['cellars.json', 'wine-references.json', 'wine-instances.json']

@pytest.fixture(scope='session', autouse=True)
def cleanup_root_json_files():
    """Clean up any JSON files created in project root before and after all tests"""
    # Clean up before tests
    for filename in JSON_FILES_TO_CLEAN:
        filepath = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
    
    yield
    
    # Clean up after all tests
    for filename in JSON_FILES_TO_CLEAN:
        filepath = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

@pytest.fixture
def client():
    """Create a test client"""
    # Create temporary directory for test data files
    test_dir = tempfile.mkdtemp()
    
    # Change to test directory and create test data files
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    # Initialize empty data files
    json_files_to_clean = ['cellars.json', 'wine-references.json', 'wine-instances.json']
    for filename in json_files_to_clean:
        with open(filename, 'w') as f:
            json.dump([], f)
    
    # Create Flask test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    
    # Cleanup: restore original directory and remove test directory
    os.chdir(original_dir)
    shutil.rmtree(test_dir)
    
    # Clean up any JSON files that might have been created in project root
    for filename in json_files_to_clean:
        filepath = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

@pytest.fixture
def sample_cellar():
    """Sample cellar data for testing"""
    return {
        'name': 'Test Cellar',
        'temperature': 55,
        'capacity': 100,
        'shelves': [
            [50, True],  # 50 positions per side, double-sided (front/back)
            [30, False]  # 30 positions, single-sided
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
