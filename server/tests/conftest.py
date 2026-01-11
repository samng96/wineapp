"""Pytest configuration and shared fixtures"""
import pytest
import os
import boto3
from flask import Flask
from flask_cors import CORS
from server.cellars import cellars_bp
from server.wine_references import wine_references_bp
from server.wine_instances import wine_instances_bp
from server.models import clear_wine_references_registry
from server.dynamo.storage import CELLARS_TABLE, WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE
from server.dynamo.setup_tables import get_dynamodb_client


@pytest.fixture(scope="session")
def dynamodb_tables():
    """Set up DynamoDB Local tables for testing (session scope)"""
    # Use DynamoDB Local endpoint
    endpoint = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
    os.environ['DYNAMODB_ENDPOINT'] = endpoint
    os.environ['DYNAMODB_REGION'] = 'us-east-1'
    
    client = get_dynamodb_client()
    
    # Create tables if they don't exist
    tables = client.list_tables().get('TableNames', [])
    
    def create_table_if_not_exists(table_name):
        """Helper to create a table if it doesn't exist"""
        if table_name not in tables:
            try:
                client.create_table(
                    TableName=table_name,
                    KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                    AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                    BillingMode='PAY_PER_REQUEST'
                )
                waiter = client.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
            except Exception as e:
                if 'ResourceInUseException' not in str(e):
                    raise
    
    create_table_if_not_exists(CELLARS_TABLE)
    create_table_if_not_exists(WINE_REFERENCES_TABLE)
    create_table_if_not_exists(WINE_INSTANCES_TABLE)
    
    yield
    
    # Cleanup is done by clear_tables fixture before each test


@pytest.fixture
def app(dynamodb_tables, monkeypatch):
    """Create Flask app with test configuration"""
    # Set environment variable for testing
    monkeypatch.setenv('FLASK_ENV', 'testing')
    
    # Ensure DynamoDB Local endpoint is set
    endpoint = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
    monkeypatch.setenv('DYNAMODB_ENDPOINT', endpoint)
    monkeypatch.setenv('DYNAMODB_REGION', 'us-east-1')
    
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


@pytest.fixture(autouse=True)
def clear_tables(dynamodb_tables):
    """Clear all DynamoDB tables before each test"""
    endpoint = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=endpoint,
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    # Clear all items from all tables
    for table_name in [CELLARS_TABLE, WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE]:
        table = dynamodb.Table(table_name)
        try:
            response = table.scan()
            with table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(Key={'id': item['id']})
        except Exception:
            pass  # Table might not exist yet
    
    # Clear wine references registry
    clear_wine_references_registry()


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
