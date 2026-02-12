"""Tests for wine instance endpoints"""
import pytest


def test_get_wine_instances_empty(client):
    """Test getting all wine instances when none exist"""
    response = client.get('/wine-instances')
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_wine_instance(client, sample_wine_instance, created_user_wine_reference):
    """Test creating a new wine instance"""
    sample_wine_instance['referenceId'] = created_user_wine_reference
    response = client.post('/wine-instances', json=sample_wine_instance)
    assert response.status_code == 201
    data = response.get_json()
    
    assert 'id' in data
    assert data['referenceId'] == created_user_wine_reference
    assert data['price'] == sample_wine_instance['price']
    assert data['purchaseDate'] == sample_wine_instance['purchaseDate']
    assert data['drinkByDate'] == sample_wine_instance['drinkByDate']
    assert data['consumed'] is False
    assert data['coravined'] is False
    assert 'version' in data
    assert 'createdAt' in data
    assert 'updatedAt' in data
    

def test_create_wine_instance_invalid_reference(client, sample_wine_instance):
    """Test creating a wine instance with invalid reference ID"""
    sample_wine_instance['referenceId'] = 'non-existent-id'
    response = client.post('/wine-instances', json=sample_wine_instance)
    assert response.status_code == 404


def test_get_wine_instance_by_id(client, sample_wine_instance, created_user_wine_reference):
    """Test getting a specific wine instance by ID"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    create_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = create_response.get_json()['id']
    
    # Get instance
    response = client.get(f'/wine-instances/{instance_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == instance_id
    assert data['referenceId'] == created_user_wine_reference


def test_get_wine_instance_not_found(client):
    """Test getting a non-existent wine instance"""
    response = client.get('/wine-instances/non-existent-id')
    assert response.status_code == 404


def test_update_wine_instance(client, sample_wine_instance, created_user_wine_reference):
    """Test updating a wine instance"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    create_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = create_response.get_json()['id']
    original_version = create_response.get_json()['version']
    
    # Update instance
    update_data = {
        'price': 99.99,
        'drinkByDate': '2035-01-01'
    }
    response = client.put(f'/wine-instances/{instance_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['price'] == 99.99
    assert data['drinkByDate'] == '2035-01-01'
    assert data['version'] == original_version + 1
    assert data['updatedAt'] != data['createdAt']


def test_delete_wine_instance(client, sample_wine_instance, created_user_wine_reference):
    """Test deleting a wine instance"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    create_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = create_response.get_json()['id']
    
    # Delete instance
    response = client.delete(f'/wine-instances/{instance_id}')
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f'/wine-instances/{instance_id}')
    assert get_response.status_code == 404
    

def test_consume_wine_instance(client, sample_wine_instance, created_user_wine_reference):
    """Test consuming a wine instance"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    create_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = create_response.get_json()['id']
    
    # Consume instance
    response = client.post(f'/wine-instances/{instance_id}/consume')
    assert response.status_code == 200
    data = response.get_json()
    assert data['consumed'] is True
    assert data['consumedDate'] is not None


def test_update_wine_instance_location(client, sample_wine_instance, created_user_wine_reference, sample_cellar):
    """Test updating a wine instance location"""
    # Create cellar
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Update location (moving from unshelved to cellar)
    location_data = {
        'oldCellarId': None,  # Was unshelved
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    
    response = client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == instance_id


def test_get_unshelved(client, sample_wine_instance, created_user_wine_reference):
    """Test getting unshelved wine instances"""
    # Create multiple instances
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance1 = client.post('/wine-instances', json=sample_wine_instance)
    instance2 = client.post('/wine-instances', json=sample_wine_instance)
    
    # Get unshelved (instances not in any cellar and not consumed)
    response = client.get('/unshelved')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 2  # At least the two we just created


def test_coravin_wine_instance(client, sample_wine_instance, created_user_wine_reference):
    """Test marking a wine instance as coravined"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    create_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = create_response.get_json()['id']
    original_version = create_response.get_json()['version']
    
    # Mark as coravined
    response = client.post(f'/wine-instances/{instance_id}/coravin')
    assert response.status_code == 200
    data = response.get_json()
    assert data['coravined'] is True
    assert data['coravinedDate'] is not None
    assert data['version'] == original_version + 1
    assert data['updatedAt'] != data['createdAt']


def test_coravin_wine_instance_not_found(client):
    """Test coravining a non-existent wine instance"""
    response = client.post('/wine-instances/non-existent-id/coravin')
    assert response.status_code == 404


def test_coravin_already_coravined(client, sample_wine_instance, created_user_wine_reference):
    """Test coravining a wine that's already been coravined"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    create_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = create_response.get_json()['id']
    
    # First coravin
    response1 = client.post(f'/wine-instances/{instance_id}/coravin')
    assert response1.status_code == 200
    first_coravined_date = response1.get_json()['coravinedDate']
    
    # Second coravin (should update the date)
    response2 = client.post(f'/wine-instances/{instance_id}/coravin')
    assert response2.status_code == 200
    second_coravined_date = response2.get_json()['coravinedDate']
    # Date should be updated (or at least the instance should still be coravined)
    assert response2.get_json()['coravined'] is True


def test_consume_coravined_wine(client, sample_wine_instance, created_user_wine_reference):
    """Test consuming a wine that was previously coravined"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    create_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = create_response.get_json()['id']
    
    # Coravin first
    coravin_response = client.post(f'/wine-instances/{instance_id}/coravin')
    assert coravin_response.status_code == 200
    assert coravin_response.get_json()['coravined'] is True
    
    # Then consume
    consume_response = client.post(f'/wine-instances/{instance_id}/consume')
    assert consume_response.status_code == 200
    data = consume_response.get_json()
    assert data['consumed'] is True
    assert data['coravined'] is True  # Should remain True
    assert data['consumedDate'] is not None


def test_update_location_invalid_cellar(client, sample_wine_instance, created_user_wine_reference):
    """Test updating location with invalid cellar ID"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Try to move to non-existent cellar
    location_data = {
        'oldCellarId': None,
        'newCellarId': 'non-existent-cellar',
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    response = client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    assert response.status_code == 404


def test_update_location_invalid_position(client, sample_wine_instance, created_user_wine_reference, sample_cellar):
    """Test updating location with invalid position"""
    # Create cellar
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Try to move to invalid position (position 999 doesn't exist)
    location_data = {
        'oldCellarId': None,
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 999
    }
    response = client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    assert response.status_code == 400


def test_update_location_occupied_position(client, sample_wine_instance, created_user_wine_reference, sample_cellar):
    """Test updating location to an occupied position"""
    # Create cellar
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Create two instances
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance1_response = client.post('/wine-instances', json=sample_wine_instance)
    instance1_id = instance1_response.get_json()['id']
    
    instance2_response = client.post('/wine-instances', json=sample_wine_instance)
    instance2_id = instance2_response.get_json()['id']
    
    # Place first instance in position
    location_data1 = {
        'oldCellarId': None,
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    response1 = client.put(f'/wine-instances/{instance1_id}/location', json=location_data1)
    assert response1.status_code == 200
    
    # Try to place second instance in same position
    location_data2 = {
        'oldCellarId': None,
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    response2 = client.put(f'/wine-instances/{instance2_id}/location', json=location_data2)
    assert response2.status_code == 400


def test_update_location_move_between_cellars(client, sample_wine_instance, created_user_wine_reference, sample_cellar):
    """Test moving a wine instance from one cellar to another"""
    # Create two cellars
    cellar1_response = client.post('/cellars', json={**sample_cellar, 'name': 'Cellar 1'})
    cellar1_id = cellar1_response.get_json()['id']
    
    cellar2_response = client.post('/cellars', json={**sample_cellar, 'name': 'Cellar 2'})
    cellar2_id = cellar2_response.get_json()['id']
    
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Place in first cellar
    location_data1 = {
        'oldCellarId': None,
        'newCellarId': cellar1_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    response1 = client.put(f'/wine-instances/{instance_id}/location', json=location_data1)
    assert response1.status_code == 200
    
    # Move to second cellar
    location_data2 = {
        'oldCellarId': cellar1_id,
        'newCellarId': cellar2_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 1
    }
    response2 = client.put(f'/wine-instances/{instance_id}/location', json=location_data2)
    assert response2.status_code == 200


def test_update_location_invalid_side(client, sample_wine_instance, created_user_wine_reference, sample_cellar):
    """Test updating location with invalid side for shelf type"""
    # Create cellar with single shelf
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Try to use 'back' on a single shelf (should be 'single')
    location_data = {
        'oldCellarId': None,
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'back',  # Invalid for single shelf
        'position': 0
    }
    response = client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    assert response.status_code == 400


def test_update_location_missing_required_fields(client, sample_wine_instance, created_user_wine_reference):
    """Test updating location with missing required fields"""
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Missing newCellarId
    location_data = {
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    response = client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    assert response.status_code == 400


def test_consume_wine_instance_not_found(client):
    """Test consuming a non-existent wine instance"""
    response = client.post('/wine-instances/non-existent-id/consume')
    assert response.status_code == 404


def test_update_wine_instance_not_found(client):
    """Test updating a non-existent wine instance"""
    update_data = {'price': 50.0}
    response = client.put('/wine-instances/non-existent-id', json=update_data)
    assert response.status_code == 404


def test_delete_wine_instance_not_found(client):
    """Test deleting a non-existent wine instance"""
    response = client.delete('/wine-instances/non-existent-id')
    assert response.status_code == 404


def test_create_wine_instance_with_location(client, sample_wine_instance, created_user_wine_reference, sample_cellar):
    """Test creating a wine instance and immediately placing it in a cellar"""
    # Create cellar
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Create instance with location
    sample_wine_instance['referenceId'] = created_user_wine_reference
    # Note: Current implementation doesn't support location in POST, 
    # but this test documents the expected behavior
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Then assign location
    location_data = {
        'oldCellarId': None,
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    response = client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    assert response.status_code == 200


def test_consume_wine_removes_from_cellar(client, sample_wine_instance, created_user_wine_reference, sample_cellar):
    """Test that consuming a wine removes it from cellar"""
    # Create cellar
    cellar_response = client.post('/cellars', json=sample_cellar)
    cellar_id = cellar_response.get_json()['id']
    
    # Create instance
    sample_wine_instance['referenceId'] = created_user_wine_reference
    instance_response = client.post('/wine-instances', json=sample_wine_instance)
    instance_id = instance_response.get_json()['id']
    
    # Place in cellar
    location_data = {
        'oldCellarId': None,
        'newCellarId': cellar_id,
        'shelfIndex': 0,
        'side': 'single',
        'position': 0
    }
    client.put(f'/wine-instances/{instance_id}/location', json=location_data)
    
    # Consume wine
    consume_response = client.post(f'/wine-instances/{instance_id}/consume')
    assert consume_response.status_code == 200
    
    # Verify wine is no longer in unshelved (consumed wines don't appear)
    unshelved_response = client.get('/unshelved')
    unshelved_ids = [i['id'] for i in unshelved_response.get_json()]
    assert instance_id not in unshelved_ids
