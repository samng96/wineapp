"""Pytest configuration and shared fixtures"""
import pytest
import os
import tempfile
import shutil
from flask import Flask
from flask_cors import CORS
from server.cellars import cellars_bp
from server.wine_references import wine_references_bp
from server.wine_instances import wine_instances_bp
from server.models import clear_wine_references_registry


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def app(temp_data_dir, monkeypatch):
    """Create Flask app with test configuration"""
    # Set environment variable to use temp directory
    monkeypatch.setenv('FLASK_ENV', 'testing')
    
    # Patch the data directory paths
    import server.utils as utils_module
    original_data_dir = utils_module.DATA_DIR
    utils_module.DATA_DIR = temp_data_dir
    utils_module.CELLARS_FILE = os.path.join(temp_data_dir, 'cellars.json')
    utils_module.WINE_REFERENCES_FILE = os.path.join(temp_data_dir, 'wine-references.json')
    utils_module.WINE_INSTANCES_FILE = os.path.join(temp_data_dir, 'wine-instances.json')
    
    # Create empty JSON files
    for filepath in [utils_module.CELLARS_FILE, utils_module.WINE_REFERENCES_FILE, utils_module.WINE_INSTANCES_FILE]:
        with open(filepath, 'w') as f:
            import json
            json.dump([], f)
    
    # Clear wine references registry before each test
    clear_wine_references_registry()
    
    # Create Flask app
    app = Flask(__name__)
    CORS(app)
    app.config['TESTING'] = True
    
    # Register blueprints
    app.register_blueprint(cellars_bp)
    app.register_blueprint(wine_references_bp)
    app.register_blueprint(wine_instances_bp)
    
    yield app
    
    # Restore original data directory
    utils_module.DATA_DIR = original_data_dir
    utils_module.CELLARS_FILE = os.path.join(original_data_dir, 'cellars.json')
    utils_module.WINE_REFERENCES_FILE = os.path.join(original_data_dir, 'wine-references.json')
    utils_module.WINE_INSTANCES_FILE = os.path.join(original_data_dir, 'wine-instances.json')


@pytest.fixture(autouse=True)
def reset_test_data(monkeypatch):
    """Reset test data before each test"""
    # Clear wine references registry before each test
    clear_wine_references_registry()
    
    # Ensure JSON files are empty
    import server.utils as utils_module
    if hasattr(utils_module, 'CELLARS_FILE'):
        for filepath in [utils_module.CELLARS_FILE, utils_module.WINE_REFERENCES_FILE, utils_module.WINE_INSTANCES_FILE]:
            if os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    import json
                    json.dump([], f)


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def sample_cellar():
    """Sample cellar data for testing"""
    return {
        'name': 'Main Cellar',
        'shelves': [[10, False], [12, True], [8, False]],
        'temperature': 55
    }


@pytest.fixture
def sample_wine_reference():
    """Sample wine reference data for testing"""
    return {
        'name': 'Cabernet Sauvignon',
        'type': 'Red',
        'vintage': 2018,
        'producer': 'Test Winery',
        'varietals': ['Cabernet Sauvignon'],
        'region': 'Napa Valley',
        'country': 'USA',
        'rating': 4,
        'tastingNotes': 'Rich and full-bodied',
        'labelImageUrl': 'https://example.com/label.jpg'
    }


@pytest.fixture
def sample_wine_instance():
    """Sample wine instance data for testing"""
    return {
        'referenceId': None,  # Will be set by test
        'price': 45.99,
        'purchaseDate': '2024-01-15',
        'drinkByDate': '2030-01-15',
        'location': None
    }


@pytest.fixture
def created_wine_reference(client, sample_wine_reference):
    """Create a wine reference and return its ID"""
    # Make the reference unique by adding a timestamp to the name
    import time
    unique_ref = sample_wine_reference.copy()
    unique_ref['name'] = f"{sample_wine_reference['name']} {int(time.time() * 1000)}"
    response = client.post('/wine-references', json=unique_ref)
    assert response.status_code == 201, f"Failed to create wine reference: {response.get_json()}"
    data = response.get_json()
    return data['id']
