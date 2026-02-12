"""Tests for cellar endpoints"""
import pytest
from server.models import Cellar, Shelf


def test_get_cellars_empty(client):
    """Test getting all cellars when none exist"""
    response = client.get('/cellars')
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_cellar(client, sample_cellar):
    """Test creating a new cellar"""
    response = client.post('/cellars', json=sample_cellar)
    assert response.status_code == 201
    data = response.get_json()
    
    assert 'id' in data
    assert data['name'] == sample_cellar['name']
    assert data['temperature'] == sample_cellar['temperature']
    assert data['shelves'] == sample_cellar['shelves']
    assert data['capacity'] == 10 + (12 * 2) + 8  # 10 + 24 + 8 = 42
    assert 'version' in data
    assert 'createdAt' in data
    assert 'updatedAt' in data


def test_create_cellar_minimal(client):
    """Test creating a cellar with minimal data"""
    data = {
        'name': 'Minimal Cellar',
        'shelves': [[5, False]]
    }
    response = client.post('/cellars', json=data)
    assert response.status_code == 201
    result = response.get_json()
    assert result['name'] == 'Minimal Cellar'
    assert result['capacity'] == 5
    assert result['temperature'] is None


def test_create_cellar_invalid_shelf(client):
    """Test creating a cellar with invalid shelf data"""
    data = {
        'name': 'Invalid Cellar',
        'shelves': [[10]]  # Missing isDouble
    }
    response = client.post('/cellars', json=data)
    assert response.status_code == 400


def test_get_cellar_by_id(client, sample_cellar):
    """Test getting a specific cellar by ID"""
    # Create cellar
    create_response = client.post('/cellars', json=sample_cellar)
    cellar_id = create_response.get_json()['id']
    
    # Get cellar
    response = client.get(f'/cellars/{cellar_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == cellar_id
    assert data['name'] == sample_cellar['name']


def test_get_cellar_not_found(client):
    """Test getting a non-existent cellar"""
    response = client.get('/cellars/non-existent-id')
    assert response.status_code == 404


def test_update_cellar(client, sample_cellar):
    """Test updating a cellar"""
    # Create cellar
    create_response = client.post('/cellars', json=sample_cellar)
    cellar_id = create_response.get_json()['id']
    original_version = create_response.get_json()['version']
    
    # Update cellar
    update_data = {
        'name': 'Updated Cellar Name',
        'temperature': 58
    }
    response = client.put(f'/cellars/{cellar_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Cellar Name'
    assert data['temperature'] == 58
    assert data['version'] == original_version + 1
    assert data['updatedAt'] != data['createdAt']


def test_update_cellar_cannot_update_shelves(client, sample_cellar):
    """Test that bulk shelf updates are not allowed"""
    # Create cellar
    create_response = client.post('/cellars', json=sample_cellar)
    cellar_id = create_response.get_json()['id']
    
    # Try to update shelves
    update_data = {
        'shelves': [[20, False]]
    }
    response = client.put(f'/cellars/{cellar_id}', json=update_data)
    assert response.status_code == 404  # Returns 404 as per current implementation


def test_delete_cellar(client, sample_cellar):
    """Test deleting a cellar"""
    # Create cellar
    create_response = client.post('/cellars', json=sample_cellar)
    cellar_id = create_response.get_json()['id']
    
    # Delete cellar
    response = client.delete(f'/cellars/{cellar_id}')
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f'/cellars/{cellar_id}')
    assert get_response.status_code == 404


def test_get_all_cellars(client, sample_cellar):
    """Test getting all cellars"""
    # Get initial count
    initial_response = client.get('/cellars')
    initial_count = len(initial_response.get_json())
    
    # Create multiple cellars
    cellar1 = client.post('/cellars', json={**sample_cellar, 'name': 'Cellar 1'})
    cellar2 = client.post('/cellars', json={**sample_cellar, 'name': 'Cellar 2'})
    
    # Get all cellars
    response = client.get('/cellars')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == initial_count + 2
    names = [c['name'] for c in data]
    assert 'Cellar 1' in names
    assert 'Cellar 2' in names


def test_create_cellar_missing_name(client):
    """Test creating a cellar without name"""
    data = {
        'shelves': [[5, False]]
    }
    response = client.post('/cellars', json=data)
    assert response.status_code == 400


def test_create_cellar_missing_shelves(client):
    """Test creating a cellar without shelves"""
    data = {
        'name': 'No Shelves Cellar'
    }
    response = client.post('/cellars', json=data)
    assert response.status_code == 400


def test_create_cellar_empty_shelves(client):
    """Test creating a cellar with empty shelves array"""
    data = {
        'name': 'Empty Shelves Cellar',
        'shelves': []
    }
    response = client.post('/cellars', json=data)
    # Should succeed but with capacity 0
    assert response.status_code == 201
    result = response.get_json()
    assert result['capacity'] == 0


def test_create_cellar_double_shelf(client):
    """Test creating a cellar with double shelves"""
    data = {
        'name': 'Double Shelf Cellar',
        'shelves': [
            [10, True],  # Double shelf with 10 positions
            [5, False]   # Single shelf with 5 positions
        ]
    }
    response = client.post('/cellars', json=data)
    assert response.status_code == 201
    result = response.get_json()
    # Capacity: (10 * 2) + 5 = 25
    assert result['capacity'] == 25


def test_update_cellar_partial_fields(client, sample_cellar):
    """Test updating only some fields"""
    # Create cellar
    create_response = client.post('/cellars', json=sample_cellar)
    cellar_id = create_response.get_json()['id']
    original_temperature = create_response.get_json()['temperature']
    
    # Update only name
    update_data = {
        'name': 'Updated Name Only'
    }
    response = client.put(f'/cellars/{cellar_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Name Only'
    assert data['temperature'] == original_temperature  # Should remain unchanged


def test_update_cellar_not_found(client):
    """Test updating a non-existent cellar"""
    update_data = {'name': 'Updated Name'}
    response = client.put('/cellars/non-existent-id', json=update_data)
    assert response.status_code == 404


def test_delete_cellar_with_wines(client, sample_cellar, sample_wine_instance, created_user_wine_reference):
    """Test deleting a cellar that contains wines"""
    # Create cellar
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Create and place wine in cellar
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Place wine in cellar
    location_data = {
        'oldCellarId': None,
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    
    # Delete cellar (should move wines to unshelved)
    delete_response = client.delete(f'/cellars/{cellar_id}')
    assert delete_response.status_code == 200
    
    # Verify wine is now unshelved
    unshelved_response = client.get('/unshelved')
    unshelved_ids = [i['id'] for i in unshelved_response.get_json()]
    assert instance_id in unshelved_ids


def test_get_cellar_layout(client, sample_cellar):
    """Test getting cellar layout/wine positions"""
    # Create cellar
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Get cellar (should include winePositions)
    response = client.get(f'/cellars/{cellar_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'winePositions' in data
    assert isinstance(data['winePositions'], dict)
