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
    # Note: GET /wine-references/<id> does not include instances array
    # Use GET /wine-references/<id>/instances to get instances


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
        'producer': 'Updated Producer'
    }
    response = client.put(f'/wine-references/{reference_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Wine Name'
    assert data['producer'] == 'Updated Producer'
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


def test_get_wine_reference_with_instances(client, sample_wine_reference, sample_wine_instance):
    """Test getting a wine reference with all its instances"""
    # Create global reference
    ref_response = client.post('/wine-references', json=sample_wine_reference)
    global_ref_id = ref_response.get_json()['id']
    
    # Create user reference
    user_ref_response = client.post('/user-wine-references', json={
        'globalReferenceId': global_ref_id
    })
    user_ref_id = user_ref_response.get_json()['id']
    
    # Create instances
    sample_wine_instance['referenceId'] = user_ref_id
    instance1_response = client.post('/wine-instances', json=sample_wine_instance)
    instance1_id = instance1_response.get_json()['id']
    
    instance2_response = client.post('/wine-instances', json=sample_wine_instance)
    instance2_id = instance2_response.get_json()['id']
    
    # Get reference with instances
    response = client.get(f'/wine-references/{global_ref_id}/instances')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == global_ref_id
    assert 'instances' in data
    instance_ids = [i['id'] for i in data['instances']]
    assert instance1_id in instance_ids
    assert instance2_id in instance_ids


def test_get_wine_reference_with_instances_no_instances(client, sample_wine_reference):
    """Test getting a wine reference with no instances"""
    # Create global reference
    ref_response = client.post('/wine-references', json=sample_wine_reference)
    global_ref_id = ref_response.get_json()['id']
    
    # Get reference with instances (should return empty array)
    response = client.get(f'/wine-references/{global_ref_id}/instances')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == global_ref_id
    assert 'instances' in data
    assert data['instances'] == []


def test_get_wine_reference_with_instances_not_found(client):
    """Test getting instances for non-existent wine reference"""
    response = client.get('/wine-references/non-existent-id/instances')
    assert response.status_code == 404


def test_update_wine_reference_partial_fields(client, sample_wine_reference):
    """Test updating only some fields of a wine reference"""
    # Create reference
    create_response = client.post('/wine-references', json=sample_wine_reference)
    reference_id = create_response.get_json()['id']
    original_producer = create_response.get_json()['producer']
    
    # Update only name
    update_data = {
        'name': 'Updated Name Only'
    }
    response = client.put(f'/wine-references/{reference_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Name Only'
    assert data['producer'] == original_producer  # Should remain unchanged


def test_update_wine_reference_not_found(client):
    """Test updating a non-existent wine reference"""
    update_data = {'name': 'Updated Name'}
    response = client.put('/wine-references/non-existent-id', json=update_data)
    assert response.status_code == 404


def test_create_wine_reference_with_vintage_zero(client):
    """Test creating a wine reference with vintage 0 (edge case)"""
    data = {
        'name': 'Non-Vintage Wine',
        'type': 'Red',
        'vintage': 0
    }
    response = client.post('/wine-references', json=data)
    assert response.status_code == 201
    result = response.get_json()
    assert result['vintage'] == 0


def test_create_wine_reference_empty_varietals(client):
    """Test creating a wine reference with empty varietals array"""
    data = {
        'name': 'Test Wine',
        'type': 'Red',
        'varietals': []
    }
    response = client.post('/wine-references', json=data)
    assert response.status_code == 201
    result = response.get_json()
    assert result['varietals'] == []


def test_update_wine_reference_varietals(client, sample_wine_reference):
    """Test updating varietals list"""
    # Create reference
    create_response = client.post('/wine-references', json=sample_wine_reference)
    reference_id = create_response.get_json()['id']
    
    # Update varietals
    update_data = {
        'varietals': ['Cabernet Sauvignon', 'Merlot']
    }
    response = client.put(f'/wine-references/{reference_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['varietals'] == ['Cabernet Sauvignon', 'Merlot']
