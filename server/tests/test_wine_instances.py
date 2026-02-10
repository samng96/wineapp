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
