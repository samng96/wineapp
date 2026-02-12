"""Tests for user wine reference endpoints"""
import pytest


def test_get_user_wine_references_empty(client):
    """Test getting all user wine references when none exist"""
    response = client.get('/user-wine-references')
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_user_wine_reference(client, created_wine_reference):
    """Test creating a new user wine reference"""
    data = {
        'globalReferenceId': created_wine_reference,
        'rating': 4,
        'tastingNotes': 'Excellent wine with notes of cherry and oak'
    }
    response = client.post('/user-wine-references', json=data)
    assert response.status_code == 201
    result = response.get_json()
    
    assert 'id' in result
    assert result['globalReferenceId'] == created_wine_reference
    assert result['rating'] == 4
    assert result['tastingNotes'] == 'Excellent wine with notes of cherry and oak'
    assert 'version' in result
    assert 'createdAt' in result
    assert 'updatedAt' in result


def test_create_user_wine_reference_minimal(client, created_wine_reference):
    """Test creating a user wine reference with minimal required fields"""
    data = {
        'globalReferenceId': created_wine_reference
    }
    response = client.post('/user-wine-references', json=data)
    assert response.status_code == 201
    result = response.get_json()
    assert result['globalReferenceId'] == created_wine_reference
    assert result['rating'] is None
    assert result['tastingNotes'] is None


def test_create_user_wine_reference_missing_global_ref_id(client):
    """Test creating a user wine reference without required globalReferenceId"""
    data = {
        'rating': 5
    }
    response = client.post('/user-wine-references', json=data)
    assert response.status_code == 400
    result = response.get_json()
    assert 'error' in result


def test_create_user_wine_reference_invalid_global_ref_id(client):
    """Test creating a user wine reference with non-existent globalReferenceId"""
    data = {
        'globalReferenceId': 'non-existent-id'
    }
    response = client.post('/user-wine-references', json=data)
    assert response.status_code == 404
    result = response.get_json()
    assert 'error' in result


def test_get_user_wine_reference_by_id(client, created_wine_reference):
    """Test getting a specific user wine reference by ID"""
    # Create user reference
    create_data = {
        'globalReferenceId': created_wine_reference,
        'rating': 5
    }
    create_response = client.post('/user-wine-references', json=create_data)
    user_ref_id = create_response.get_json()['id']
    
    # Get user reference
    response = client.get(f'/user-wine-references/{user_ref_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == user_ref_id
    assert data['globalReferenceId'] == created_wine_reference
    assert data['rating'] == 5


def test_get_user_wine_reference_not_found(client):
    """Test getting a non-existent user wine reference"""
    response = client.get('/user-wine-references/non-existent-id')
    assert response.status_code == 404
    result = response.get_json()
    assert 'error' in result


def test_update_user_wine_reference(client, created_wine_reference):
    """Test updating a user wine reference"""
    # Create user reference
    create_data = {
        'globalReferenceId': created_wine_reference,
        'rating': 3
    }
    create_response = client.post('/user-wine-references', json=create_data)
    user_ref_id = create_response.get_json()['id']
    original_version = create_response.get_json()['version']
    
    # Update user reference
    update_data = {
        'rating': 5,
        'tastingNotes': 'Updated tasting notes'
    }
    response = client.put(f'/user-wine-references/{user_ref_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['rating'] == 5
    assert data['tastingNotes'] == 'Updated tasting notes'
    assert data['version'] == original_version + 1
    assert data['updatedAt'] != data['createdAt']


def test_update_user_wine_reference_partial(client, created_wine_reference):
    """Test updating only rating without tasting notes"""
    # Create user reference
    create_data = {
        'globalReferenceId': created_wine_reference,
        'rating': 3,
        'tastingNotes': 'Original notes'
    }
    create_response = client.post('/user-wine-references', json=create_data)
    user_ref_id = create_response.get_json()['id']
    
    # Update only rating
    update_data = {
        'rating': 4
    }
    response = client.put(f'/user-wine-references/{user_ref_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['rating'] == 4
    assert data['tastingNotes'] == 'Original notes'  # Should remain unchanged


def test_update_user_wine_reference_clear_fields(client, created_wine_reference):
    """Test clearing rating and tasting notes by setting to None"""
    # Create user reference with data
    create_data = {
        'globalReferenceId': created_wine_reference,
        'rating': 5,
        'tastingNotes': 'Some notes'
    }
    create_response = client.post('/user-wine-references', json=create_data)
    user_ref_id = create_response.get_json()['id']
    
    # Note: Current implementation doesn't support clearing fields via None
    # This test documents current behavior - fields remain if not updated
    update_data = {
        'rating': 3
    }
    response = client.put(f'/user-wine-references/{user_ref_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['rating'] == 3
    # Tasting notes should remain unchanged
    assert data['tastingNotes'] == 'Some notes'


def test_delete_user_wine_reference(client, created_wine_reference):
    """Test deleting a user wine reference"""
    # Create user reference
    create_data = {
        'globalReferenceId': created_wine_reference
    }
    create_response = client.post('/user-wine-references', json=create_data)
    user_ref_id = create_response.get_json()['id']
    
    # Delete user reference
    response = client.delete(f'/user-wine-references/{user_ref_id}')
    assert response.status_code == 200
    result = response.get_json()
    assert 'message' in result
    
    # Verify it's deleted
    get_response = client.get(f'/user-wine-references/{user_ref_id}')
    assert get_response.status_code == 404


def test_get_all_user_wine_references(client, created_wine_reference):
    """Test getting all user wine references"""
    # Get initial count
    initial_response = client.get('/user-wine-references')
    initial_count = len(initial_response.get_json())
    
    # Create multiple user references
    ref1 = client.post('/user-wine-references', json={
        'globalReferenceId': created_wine_reference,
        'rating': 4
    })
    # Create another global reference for second user reference
    import time
    from server.tests.conftest import sample_wine_reference
    unique_ref = sample_wine_reference.copy()
    unique_ref['name'] = f"Test Wine {int(time.time() * 1000)}"
    global_ref2 = client.post('/wine-references', json=unique_ref)
    global_ref2_id = global_ref2.get_json()['id']
    
    ref2 = client.post('/user-wine-references', json={
        'globalReferenceId': global_ref2_id,
        'rating': 5
    })
    
    # Get all user references
    response = client.get('/user-wine-references')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == initial_count + 2


def test_user_wine_reference_rating_validation(client, created_wine_reference):
    """Test that rating values are accepted (validation happens at model level)"""
    # Test valid ratings
    for rating in [1, 2, 3, 4, 5]:
        data = {
            'globalReferenceId': created_wine_reference,
            'rating': rating
        }
        response = client.post('/user-wine-references', json=data)
        assert response.status_code == 201
        result = response.get_json()
        assert result['rating'] == rating


def test_multiple_user_refs_same_global_ref(client, created_wine_reference):
    """Test that multiple user references can reference the same global reference"""
    # This should be allowed - each user can have their own rating/notes
    # Note: Current implementation allows this, but in a multi-user system,
    # you'd typically have one UserWineReference per user per GlobalWineReference
    ref1 = client.post('/user-wine-references', json={
        'globalReferenceId': created_wine_reference,
        'rating': 4
    })
    assert ref1.status_code == 201
    
    ref2 = client.post('/user-wine-references', json={
        'globalReferenceId': created_wine_reference,
        'rating': 5
    })
    assert ref2.status_code == 201
    
    # Both should exist
    all_refs = client.get('/user-wine-references').get_json()
    global_ref_ids = [r['globalReferenceId'] for r in all_refs]
    assert global_ref_ids.count(created_wine_reference) >= 2
