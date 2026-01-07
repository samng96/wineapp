"""Tests for wine reference endpoints"""
import pytest


def test_get_wine_references_empty(client):
    """Test getting all wine references when none exist"""
    response = client.get('/wine-references')
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_wine_reference(client, sample_wine_reference):
    """Test creating a new wine reference"""
    response = client.post('/wine-references', json=sample_wine_reference)
    assert response.status_code == 201
    data = response.get_json()
    
    assert 'id' in data
    assert data['name'] == sample_wine_reference['name']
    assert data['type'] == sample_wine_reference['type']
    assert data['vintage'] == sample_wine_reference['vintage']
    assert data['producer'] == sample_wine_reference['producer']
    assert data['varietals'] == sample_wine_reference['varietals']
    assert data['region'] == sample_wine_reference['region']
    assert data['country'] == sample_wine_reference['country']
    assert data['rating'] == sample_wine_reference['rating']
    assert data['tastingNotes'] == sample_wine_reference['tastingNotes']
    assert data['labelImageUrl'] == sample_wine_reference['labelImageUrl']
    assert 'version' in data
    assert 'createdAt' in data
    assert 'updatedAt' in data


def test_create_wine_reference_minimal(client):
    """Test creating a wine reference with minimal required fields"""
    data = {
        'name': 'Minimal Wine',
        'type': 'Red'
    }
    response = client.post('/wine-references', json=data)
    assert response.status_code == 201
    result = response.get_json()
    assert result['name'] == 'Minimal Wine'
    assert result['type'] == 'Red'
    assert result['vintage'] is None
    assert result['producer'] is None


def test_create_wine_reference_missing_required(client):
    """Test creating a wine reference without required fields"""
    data = {
        'name': 'Missing Type'
    }
    response = client.post('/wine-references', json=data)
    assert response.status_code == 400


def test_create_duplicate_wine_reference(client, sample_wine_reference):
    """Test creating a duplicate wine reference (same name, vintage, producer)"""
    # Create first reference
    response1 = client.post('/wine-references', json=sample_wine_reference)
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = client.post('/wine-references', json=sample_wine_reference)
    assert response2.status_code == 409
    data = response2.get_json()
    assert 'error' in data
    assert 'reference' in data


def test_get_wine_reference_by_id(client, sample_wine_reference):
    """Test getting a specific wine reference by ID"""
    # Create reference
    create_response = client.post('/wine-references', json=sample_wine_reference)
    reference_id = create_response.get_json()['id']
    
    # Get reference
    response = client.get(f'/wine-references/{reference_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == reference_id
    assert data['name'] == sample_wine_reference['name']
    assert 'instances' in data  # Should include instances array


def test_get_wine_reference_not_found(client):
    """Test getting a non-existent wine reference"""
    response = client.get('/wine-references/non-existent-id')
    assert response.status_code == 404


def test_update_wine_reference(client, sample_wine_reference):
    """Test updating a wine reference"""
    # Create reference
    create_response = client.post('/wine-references', json=sample_wine_reference)
    reference_id = create_response.get_json()['id']
    original_version = create_response.get_json()['version']
    
    # Update reference
    update_data = {
        'name': 'Updated Wine Name',
        'rating': 5
    }
    response = client.put(f'/wine-references/{reference_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Wine Name'
    assert data['rating'] == 5
    assert data['version'] == original_version + 1
    assert data['updatedAt'] != data['createdAt']


def test_delete_wine_reference(client, sample_wine_reference):
    """Test deleting a wine reference"""
    # Create reference with unique name to avoid conflicts
    import time
    unique_ref = sample_wine_reference.copy()
    unique_ref['name'] = f"{sample_wine_reference['name']} Delete {int(time.time() * 1000)}"
    create_response = client.post('/wine-references', json=unique_ref)
    reference_id = create_response.get_json()['id']
    
    # Delete reference
    response = client.delete(f'/wine-references/{reference_id}')
    assert response.status_code == 200
    
    # Verify it's deleted - need to reload registry first
    from server.models import clear_wine_references_registry
    clear_wine_references_registry()
    get_response = client.get(f'/wine-references/{reference_id}')
    assert get_response.status_code == 404


def test_get_all_wine_references(client, sample_wine_reference):
    """Test getting all wine references"""
    # Get initial count
    initial_response = client.get('/wine-references')
    initial_count = len(initial_response.get_json())
    
    # Create multiple references
    ref1 = client.post('/wine-references', json={**sample_wine_reference, 'name': 'Wine 1', 'vintage': 2020})
    ref2 = client.post('/wine-references', json={**sample_wine_reference, 'name': 'Wine 2', 'vintage': 2019})
    
    # Get all references
    response = client.get('/wine-references')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == initial_count + 2
    names = [r['name'] for r in data]
    assert 'Wine 1' in names
    assert 'Wine 2' in names
