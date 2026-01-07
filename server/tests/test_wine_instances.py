"""Tests for wine instance endpoints"""
import pytest
import json

@pytest.fixture
def created_wine_reference(client, sample_wine_reference):
    """Create a wine reference for use in instance tests"""
    response = client.post('/wine-references',
                          json=sample_wine_reference,
                          content_type='application/json')
    return json.loads(response.data)

def test_get_wine_instances_empty(client):
    """Test getting all wine instances when none exist"""
    response = client.get('/wine-instances')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == []

def test_create_wine_instance(client, sample_wine_instance, created_wine_reference):
    """Test creating a new wine instance"""
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    
    response = client.post('/wine-instances',
                          json=sample_wine_instance,
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['referenceId'] == created_wine_reference['id']
    assert data['price'] == sample_wine_instance['price']
    assert data['consumed'] == False
    assert 'id' in data
    assert 'version' in data
    assert 'storedDate' in data
    
    # Verify instance count was updated
    ref_response = client.get(f"/wine-references/{created_wine_reference['id']}")
    ref_data = json.loads(ref_response.data)
    assert ref_data['instanceCount'] == 1

def test_create_wine_instance_invalid_reference(client, sample_wine_instance):
    """Test creating a wine instance with invalid reference ID"""
    sample_wine_instance['referenceId'] = 'non-existent-id'
    
    response = client.post('/wine-instances',
                          json=sample_wine_instance,
                          content_type='application/json')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_get_wine_instance_by_id(client, sample_wine_instance, created_wine_reference):
    """Test getting a specific wine instance by ID"""
    # Create an instance first
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    create_response = client.post('/wine-instances',
                                 json=sample_wine_instance,
                                 content_type='application/json')
    instance_id = json.loads(create_response.data)['id']
    
    # Get the instance
    response = client.get(f'/wine-instances/{instance_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == instance_id

def test_get_wine_instance_not_found(client):
    """Test getting a wine instance that doesn't exist"""
    response = client.get('/wine-instances/non-existent-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_update_wine_instance(client, sample_wine_instance, created_wine_reference):
    """Test updating a wine instance"""
    # Create an instance first
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    create_response = client.post('/wine-instances',
                                 json=sample_wine_instance,
                                 content_type='application/json')
    instance_id = json.loads(create_response.data)['id']
    original_version = json.loads(create_response.data)['version']
    
    # Update the instance
    update_data = {'price': 30.99, 'drinkByDate': '2026-12-31'}
    response = client.put(f'/wine-instances/{instance_id}',
                         json=update_data,
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['price'] == 30.99
    assert data['drinkByDate'] == '2026-12-31'
    assert data['version'] == original_version + 1

def test_delete_wine_instance(client, sample_wine_instance, created_wine_reference):
    """Test deleting a wine instance"""
    # Create an instance first
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    create_response = client.post('/wine-instances',
                                 json=sample_wine_instance,
                                 content_type='application/json')
    instance_id = json.loads(create_response.data)['id']
    
    # Delete the instance
    response = client.delete(f'/wine-instances/{instance_id}')
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f'/wine-instances/{instance_id}')
    assert get_response.status_code == 404
    
    # Verify instance count was updated
    ref_response = client.get(f"/wine-references/{created_wine_reference['id']}")
    ref_data = json.loads(ref_response.data)
    assert ref_data['instanceCount'] == 0

def test_consume_wine_instance(client, sample_wine_instance, created_wine_reference):
    """Test consuming a wine instance"""
    # Create an instance first
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    create_response = client.post('/wine-instances',
                                 json=sample_wine_instance,
                                 content_type='application/json')
    instance_id = json.loads(create_response.data)['id']
    
    # Consume the instance
    response = client.post(f'/wine-instances/{instance_id}/consume')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['consumed'] == True
    assert data['consumedDate'] is not None
    assert data['location']['type'] == 'unshelved'
    
    # Verify instance count was updated
    ref_response = client.get(f"/wine-references/{created_wine_reference['id']}")
    ref_data = json.loads(ref_response.data)
    assert ref_data['instanceCount'] == 0

def test_update_wine_instance_location(client, sample_wine_instance, created_wine_reference, sample_cellar):
    """Test updating wine instance location"""
    # Create a cellar first
    cellar_response = client.post('/cellars',
                                 json=sample_cellar,
                                 content_type='application/json')
    cellar_id = json.loads(cellar_response.data)['id']
    
    # Create an instance first
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    create_response = client.post('/wine-instances',
                                 json=sample_wine_instance,
                                 content_type='application/json')
    instance_id = json.loads(create_response.data)['id']
    
    # Update location
    new_location = {
        'type': 'cellar',
        'cellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'front',
        'position': 5
    }
    response = client.put(f'/wine-instances/{instance_id}/location',
                         json={'location': new_location},
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['location'] == new_location

def test_get_unshelved(client, sample_wine_instance, created_wine_reference):
    """Test getting unshelved wine instances"""
    # Create an unshelved instance
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    sample_wine_instance['location'] = {'type': 'unshelved'}
    client.post('/wine-instances',
               json=sample_wine_instance,
               content_type='application/json')
    
    # Get unshelved instances
    response = client.get('/unshelved')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['location']['type'] == 'unshelved'

def test_assign_unshelved_to_cellar(client, sample_wine_instance, created_wine_reference, sample_cellar):
    """Test assigning unshelved wine to a cellar"""
    # Create a cellar first
    cellar_response = client.post('/cellars',
                                 json=sample_cellar,
                                 content_type='application/json')
    cellar_id = json.loads(cellar_response.data)['id']
    
    # Create an unshelved instance
    sample_wine_instance['referenceId'] = created_wine_reference['id']
    sample_wine_instance['location'] = {'type': 'unshelved'}
    create_response = client.post('/wine-instances',
                                 json=sample_wine_instance,
                                 content_type='application/json')
    instance_id = json.loads(create_response.data)['id']
    
    # Assign to cellar
    new_location = {
        'type': 'cellar',
        'cellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'front',
        'position': 5
    }
    response = client.post(f'/unshelved/{instance_id}/assign',
                          json={'location': new_location},
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['location'] == new_location
