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
