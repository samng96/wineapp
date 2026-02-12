"""User wine reference management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import List, Optional
from server.utils import generate_id, get_current_timestamp
from server.models import UserWineReference
from server.data.storage_serializers import serialize_user_wine_reference, deserialize_user_wine_reference
from server.wine_references import find_wine_reference_by_id
from server.dynamo.storage import (
    get_all_user_wine_references as dynamodb_get_all_user_wine_references,
    put_user_wine_reference as dynamodb_put_user_wine_reference,
    get_user_wine_reference_by_id as dynamodb_get_user_wine_reference_by_id,
    delete_user_wine_reference as dynamodb_delete_user_wine_reference
)

user_wine_references_bp = Blueprint('user_wine_references', __name__)


# Helper functions
def get_all_user_wine_references() -> List[UserWineReference]:
    """Load user wine references from DynamoDB as UserWineReference model objects"""
    data = dynamodb_get_all_user_wine_references()
    return [deserialize_user_wine_reference(r) for r in data]

def find_user_wine_reference_by_id(user_ref_id: str) -> Optional[UserWineReference]:
    """Find a user wine reference by ID"""
    data = dynamodb_get_user_wine_reference_by_id(user_ref_id)
    if not data:
        return None
    return deserialize_user_wine_reference(data)


# Endpoints
"""
Get all user wine references

Response Format: Array of user wine reference objects, each containing:
- id (str): Unique identifier
- globalReferenceId (str): ID of the associated GlobalWineReference
- rating (int, optional): User's personal rating (1-5)
- tastingNotes (str, optional): User's personal tasting notes
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when created
- updatedAt (str): ISO 8601 timestamp when last updated
"""
@user_wine_references_bp.route('/user-wine-references', methods=['GET'])
def _get_user_wine_references():
    """Get all user wine references"""
    user_refs = get_all_user_wine_references()
    return jsonify([serialize_user_wine_reference(r) for r in user_refs])


"""
Create a new user wine reference

Expected POST Parameters:
- globalReferenceId (str, required): ID of the GlobalWineReference to associate with
- rating (int, optional): User's personal rating (1-5)
- tastingNotes (str, optional): User's personal tasting notes
"""
@user_wine_references_bp.route('/user-wine-references', methods=['POST'])
def _create_user_wine_reference():
    """Create a new user wine reference"""
    data = request.json

    # Validate required fields
    global_ref_id = data.get('globalReferenceId')
    if not global_ref_id:
        return jsonify({'error': 'globalReferenceId is required'}), 400

    # Verify the global reference exists
    global_ref = find_wine_reference_by_id(global_ref_id)
    if not global_ref:
        return jsonify({'error': 'Global wine reference not found'}), 404

    # Create UserWineReference model object
    timestamp = get_current_timestamp()
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=global_ref_id,
        rating=data.get('rating'),
        tasting_notes=data.get('tastingNotes'),
        version=1,
        created_at=timestamp,
        updated_at=timestamp
    )

    # Save to DynamoDB
    serialized = serialize_user_wine_reference(user_ref)
    dynamodb_put_user_wine_reference(serialized)
    return jsonify(serialized), 201


"""
Get a specific user wine reference by ID

Error Response (404): {'error': 'User wine reference not found'}
"""
@user_wine_references_bp.route('/user-wine-references/<user_ref_id>', methods=['GET'])
def _get_user_wine_reference(user_ref_id: str):
    """Get a specific user wine reference"""
    user_ref = find_user_wine_reference_by_id(user_ref_id)
    if not user_ref:
        return jsonify({'error': 'User wine reference not found'}), 404
    return jsonify(serialize_user_wine_reference(user_ref))


"""
Update a user wine reference

Expected PUT Parameters (all optional):
- rating (int, optional): Updated rating (1-5)
- tastingNotes (str, optional): Updated tasting notes
"""
@user_wine_references_bp.route('/user-wine-references/<user_ref_id>', methods=['PUT'])
def _update_user_wine_reference(user_ref_id: str):
    """Update a user wine reference"""
    user_ref = find_user_wine_reference_by_id(user_ref_id)
    if not user_ref:
        return jsonify({'error': 'User wine reference not found'}), 404

    data = request.json

    # Update fields
    if 'rating' in data:
        user_ref.rating = data['rating']
    if 'tastingNotes' in data:
        user_ref.tasting_notes = data['tastingNotes']

    # Update version and timestamp
    user_ref.version += 1
    user_ref.updated_at = get_current_timestamp()

    # Save to DynamoDB
    serialized = serialize_user_wine_reference(user_ref)
    dynamodb_put_user_wine_reference(serialized)
    return jsonify(serialized)


"""
Delete a user wine reference

Error Response (404): {'error': 'User wine reference not found'}
"""
@user_wine_references_bp.route('/user-wine-references/<user_ref_id>', methods=['DELETE'])
def _delete_user_wine_reference(user_ref_id: str):
    """Delete a user wine reference"""
    user_ref = find_user_wine_reference_by_id(user_ref_id)
    if not user_ref:
        return jsonify({'error': 'User wine reference not found'}), 404

    # Remove from DynamoDB
    dynamodb_delete_user_wine_reference(user_ref_id)
    return jsonify({'message': 'User wine reference deleted'}), 200
