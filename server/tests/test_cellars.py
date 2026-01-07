"""Tests for cellar endpoints"""
import pytest
import json

def test_get_cellars_empty(client):
    """Test getting all cellars when none exist"""
    response = client.get('/cellars')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == []

def test_create_cellar(client, sample_cellar):
    """Test creating a new cellar"""
    response = client.post('/cellars', 
                          json=sample_cellar,
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == sample_cellar['name']
    assert data['temperature'] == sample_cellar['temperature']
    assert data['capacity'] == sample_cellar['capacity']
    assert 'id' in data
    assert 'version' in data
    assert 'createdAt' in data
    assert 'updatedAt' in data

def test_get_cellar_by_id(client, sample_cellar):
    """Test getting a specific cellar by ID"""
    # Create a cellar first
    create_response = client.post('/cellars', 
                                 json=sample_cellar,
                                 content_type='application/json')
    cellar_id = json.loads(create_response.data)['id']
    
    # Get the cellar
    response = client.get(f'/cellars/{cellar_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == cellar_id
    assert data['name'] == sample_cellar['name']

def test_get_cellar_not_found(client):
    """Test getting a cellar that doesn't exist"""
    response = client.get('/cellars/non-existent-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_update_cellar(client, sample_cellar):
    """Test updating a cellar"""
    # Create a cellar first
    create_response = client.post('/cellars', 
                                 json=sample_cellar,
                                 content_type='application/json')
    cellar_id = json.loads(create_response.data)['id']
    original_version = json.loads(create_response.data)['version']
    
    # Update the cellar
    update_data = {'name': 'Updated Cellar Name', 'temperature': 60}
    response = client.put(f'/cellars/{cellar_id}',
                         json=update_data,
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Updated Cellar Name'
    assert data['temperature'] == 60
    assert data['version'] == original_version + 1

def test_delete_cellar(client, sample_cellar):
    """Test deleting a cellar"""
    # Create a cellar first
    create_response = client.post('/cellars', 
                                 json=sample_cellar,
                                 content_type='application/json')
    cellar_id = json.loads(create_response.data)['id']
    
    # Delete the cellar
    response = client.delete(f'/cellars/{cellar_id}')
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f'/cellars/{cellar_id}')
    assert get_response.status_code == 404

def test_get_cellar_layout(client, sample_cellar):
    """Test getting cellar layout"""
    # Create a cellar first
    create_response = client.post('/cellars', 
                                 json=sample_cellar,
                                 content_type='application/json')
    cellar_id = json.loads(create_response.data)['id']
    
    # Get layout
    response = client.get(f'/cellars/{cellar_id}/layout')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'rows' in data
    assert data['id'] == cellar_id

def test_create_cellar_minimal_data(client):
    """Test creating a cellar with minimal required data"""
    minimal_data = {'name': 'Minimal Cellar'}
    response = client.post('/cellars',
                          json=minimal_data,
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Minimal Cellar'
    assert data.get('rows') == []
