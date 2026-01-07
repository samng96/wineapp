"""Tests for wine reference endpoints"""
import pytest
import json

def test_get_wine_references_empty(client):
    """Test getting all wine references when none exist"""
    response = client.get('/wine-references')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == []

def test_create_wine_reference(client, sample_wine_reference):
    """Test creating a new wine reference"""
    response = client.post('/wine-references',
                          json=sample_wine_reference,
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == sample_wine_reference['name']
    assert data['type'] == sample_wine_reference['type']
    assert data['vintage'] == sample_wine_reference['vintage']
    assert data['producer'] == sample_wine_reference['producer']
    assert 'id' in data
    assert 'version' in data
    assert 'instanceCount' in data
    assert data['instanceCount'] == 0

def test_create_duplicate_wine_reference(client, sample_wine_reference):
    """Test creating a duplicate wine reference (should fail)"""
    # Create first reference
    response1 = client.post('/wine-references',
                           json=sample_wine_reference,
                           content_type='application/json')
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = client.post('/wine-references',
                           json=sample_wine_reference,
                           content_type='application/json')
    assert response2.status_code == 409
    data = json.loads(response2.data)
    assert 'error' in data

def test_get_wine_reference_by_id(client, sample_wine_reference):
    """Test getting a specific wine reference by ID"""
    # Create a reference first
    create_response = client.post('/wine-references',
                                 json=sample_wine_reference,
                                 content_type='application/json')
    reference_id = json.loads(create_response.data)['id']
    
    # Get the reference
    response = client.get(f'/wine-references/{reference_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == reference_id
    assert 'instances' in data
    assert isinstance(data['instances'], list)

def test_get_wine_reference_not_found(client):
    """Test getting a wine reference that doesn't exist"""
    response = client.get('/wine-references/non-existent-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_update_wine_reference(client, sample_wine_reference):
    """Test updating a wine reference"""
    # Create a reference first
    create_response = client.post('/wine-references',
                                 json=sample_wine_reference,
                                 content_type='application/json')
    reference_id = json.loads(create_response.data)['id']
    original_version = json.loads(create_response.data)['version']
    
    # Update the reference
    update_data = {'rating': 5, 'tastingNotes': 'Updated notes'}
    response = client.put(f'/wine-references/{reference_id}',
                         json=update_data,
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['rating'] == 5
    assert data['tastingNotes'] == 'Updated notes'
    assert data['version'] == original_version + 1

def test_delete_wine_reference(client, sample_wine_reference):
    """Test deleting a wine reference"""
    # Create a reference first
    create_response = client.post('/wine-references',
                                 json=sample_wine_reference,
                                 content_type='application/json')
    reference_id = json.loads(create_response.data)['id']
    
    # Delete the reference
    response = client.delete(f'/wine-references/{reference_id}')
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f'/wine-references/{reference_id}')
    assert get_response.status_code == 404

def test_create_wine_reference_minimal_data(client):
    """Test creating a wine reference with minimal required data"""
    minimal_data = {
        'name': 'Minimal Wine',
        'type': 'Red',
        'vintage': 2020
    }
    response = client.post('/wine-references',
                          json=minimal_data,
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Minimal Wine'
    assert data['varietals'] == []
