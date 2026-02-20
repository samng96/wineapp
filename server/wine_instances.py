"""Wine instance management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import List, Optional
from server.utils import generate_id, get_current_timestamp
from server.models import WineInstance
from server.data.storage_serializers import serialize_wine_instance, deserialize_wine_instance
from server.user_wine_references import get_all_user_wine_references, find_user_wine_reference_by_id
from server.cellars import find_cellar_by_id, find_cellar_containing_wine_instance, update_and_save_cellar
from server.dynamo.storage import (
    get_all_wine_instances as dynamodb_get_all_wine_instances,
    put_wine_instance as dynamodb_put_wine_instance,
    get_wine_instance_by_id as dynamodb_get_wine_instance_by_id,
    delete_wine_instance as dynamodb_delete_wine_instance,
    save_wine_instances as dynamodb_save_wine_instances
)

wine_instances_bp = Blueprint('wine_instances', __name__)

# Helper functions
def consume_wine_instance(instance: WineInstance):
    """Consume a wine instance"""
    instance.set_consumed()
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    data = serialize_wine_instance(instance)
    dynamodb_put_wine_instance(data)

def get_all_wine_instances() -> List[WineInstance]:
    """Load wine instances from DynamoDB as WineInstance model objects
    """
    data = dynamodb_get_all_wine_instances()
    user_refs_list = get_all_user_wine_references()
    # Convert to dictionary keyed by ID for lookup
    user_refs_dict = {ref.id: ref for ref in user_refs_list}
    return [deserialize_wine_instance(i, user_refs_dict[i['referenceId']]) for i in data]

def save_wine_instances(instances: List[WineInstance]):
    """Save wine instances to DynamoDB (accepts WineInstance model objects)"""
    data = [serialize_wine_instance(i) for i in instances]
    dynamodb_save_wine_instances(data)

def find_wine_instance_by_id(instance_id: str) -> Optional[WineInstance]:
    """Find a wine instance by ID (returns WineInstance model object)"""
    data = dynamodb_get_wine_instance_by_id(instance_id)
    if not data:
        return None
    user_ref = find_user_wine_reference_by_id(data['referenceId'])
    if not user_ref:
        return None
    return deserialize_wine_instance(data, user_ref)

def _update_and_save_wine_instance(instance: WineInstance):
    """Helper function to update and save a wine instance in DynamoDB"""
    data = serialize_wine_instance(instance)
    dynamodb_put_wine_instance(data)

# Endpoints
"""
Get all wine instances

Response Format: Array of wine instance objects, each containing:
- id (str): Unique identifier for the wine instance
- referenceId (str): ID of the wine reference this instance belongs to
- price (float, optional): Purchase price
- purchaseDate (str, optional): ISO 8601 date when purchased
- drinkByDate (str, optional): ISO 8601 date for recommended consumption
- consumed (bool): Whether the wine has been consumed
- consumedDate (str, optional): ISO 8601 timestamp when consumed
- coravined (bool): Whether the wine has been coravined
- coravinedDate (str, optional): ISO 8601 timestamp when coravined
- storedDate (str, optional): ISO 8601 timestamp when stored
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when instance was created
- updatedAt (str): ISO 8601 timestamp when instance was last updated
"""
@wine_instances_bp.route('/wine-instances', methods=['GET'])
def _get_wine_instances():
    """Get all wine instances"""
    instances = get_all_wine_instances()
    return jsonify([serialize_wine_instance(i) for i in instances])


"""
Create a new wine instance

Expected POST Parameters:
- referenceId (str, required): ID of the wine reference this instance belongs to
- price (float, optional): Purchase price of the wine instance
- purchaseDate (str, optional): ISO 8601 date string when the wine was purchased
- drinkByDate (str, optional): ISO 8601 date string for recommended consumption date
"""
@wine_instances_bp.route('/wine-instances', methods=['POST'])
def _create_wine_instance():
    """Create a new wine instance"""
    data = request.json
    
    # Verify user wine reference exists
    user_ref = find_user_wine_reference_by_id(data.get('referenceId'))
    if not user_ref:
        return jsonify({'error': 'User wine reference not found'}), 404

    # Create WineInstance model object
    instance = WineInstance(
        id=generate_id(),
        reference=user_ref,  # Use UserWineReference object
        price=data.get('price'),
        purchase_date=data.get('purchaseDate'),
        drink_by_date=data.get('drinkByDate'),
        consumed=False,
        consumed_date=None,
        coravined=False,
        coravined_date=None,
        stored_date=get_current_timestamp(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    
    # Save to DynamoDB
    data = serialize_wine_instance(instance)
    dynamodb_put_wine_instance(data)
    return jsonify(data), 201


"""
Get a specific wine instance by ID

Response Format: Wine instance object containing:
- id (str): Unique identifier for the wine instance
- referenceId (str): ID of the wine reference this instance belongs to
- price (float, optional): Purchase price
- purchaseDate (str, optional): ISO 8601 date when purchased
- drinkByDate (str, optional): ISO 8601 date for recommended consumption
- consumed (bool): Whether the wine has been consumed
- consumedDate (str, optional): ISO 8601 timestamp when consumed
- storedDate (str, optional): ISO 8601 timestamp when stored
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when instance was created
- updatedAt (str): ISO 8601 timestamp when instance was last updated
- coravined (bool): Whether the wine has been coravined
- coravinedDate (str, optional): ISO 8601 timestamp when coravined

Error Response (404): {'error': 'Wine instance not found'} if instance doesn't exist
"""
@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['GET'])
def _get_wine_instance(instance_id: str):
    """Get a specific wine instance"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    return jsonify(serialize_wine_instance(instance))


"""
Update a wine instance

Expected PUT Parameters (all optional):
- price (float, optional): Updated purchase price
- purchaseDate (str, optional): Updated purchase date (ISO 8601 format)
- drinkByDate (str, optional): Updated recommended consumption date (ISO 8601 format)
"""
@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['PUT'])
def _update_wine_instance(instance_id: str):
    """Update a wine instance"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    
    # Update fields (only price, purchaseDate, drinkByDate can be updated here)
    if 'price' in data:
        instance.price = data['price']
    if 'purchaseDate' in data:
        instance.purchase_date = data['purchaseDate']
    if 'drinkByDate' in data:
        instance.drink_by_date = data['drinkByDate']
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    _update_and_save_wine_instance(instance)
    return jsonify(serialize_wine_instance(instance))

@wine_instances_bp.route('/wine-instances/<instance_id>/consume', methods=['POST'])
def _consume_wine_instance(instance_id: str):
    """Mark a wine instance as consumed (soft delete)"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    # If it's in a cellar, remove it from the cellar
    cellar = find_cellar_containing_wine_instance(instance)
    if cellar:
        cellar.remove_wine_from_cellar(instance)
        update_and_save_cellar(cellar)

    # Update version and timestamp
    instance.set_consumed()
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    _update_and_save_wine_instance(instance)
    return jsonify(serialize_wine_instance(instance))


@wine_instances_bp.route('/wine-instances/<instance_id>/coravin', methods=['POST'])
def _coravin_wine_instance(instance_id: str):
    """Mark a wine instance as coravined"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    # Update version and timestamp
    instance.set_coravined()
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    _update_and_save_wine_instance(instance)
    return jsonify(serialize_wine_instance(instance))


"""
Delete a wine instance

Error Response (404): {'error': 'Wine instance not found'} if instance doesn't exist
"""
@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['DELETE'])
def _delete_wine_instance(instance_id: str):
    """Delete a wine instance"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    # Delete from DynamoDB
    dynamodb_delete_wine_instance(instance_id)
    return jsonify({'message': 'Wine instance deleted'}), 200


"""
Update wine instance location

Expected PUT Parameters:
    'oldCellarId': str (optional - if not provided, this is unshelved),
    'newCellarId': str (required),
    'shelfIndex': int (required),
    'side': 'front'|'back'|'single' (required),
    'position': int (required)
"""
@wine_instances_bp.route('/wine-instances/<instance_id>/location', methods=['PUT'])
def _update_wine_instance_location(instance_id: str):
    """Update wine instance location"""
    data = request.json
    old_cellar_id = data.get('oldCellarId')
    new_cellar_id = data.get('newCellarId')
    shelf_index = data.get('shelfIndex')
    side = data.get('side')
    position = data.get('position')

    # old_cellar_id can be None if this was unshelved.
    if new_cellar_id is None:
        return jsonify({'error': 'New cellar ID is required'}), 400
    if shelf_index is None:
        return jsonify({'error': 'Shelf index is required'}), 400
    if side is None:
        return jsonify({'error': 'Side is required'}), 400
    if position is None:
        return jsonify({'error': 'Position is required'}), 400

    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    old_cellar = None
    if old_cellar_id is not None:
        old_cellar = find_cellar_by_id(old_cellar_id)
        if not old_cellar:
            return jsonify({'error': 'Old cellar not found'}), 404
        if not old_cellar.is_wine_instance_in_cellar(instance):
            return jsonify({'error': 'Wine instance is not in the old cellar'}), 400

    new_cellar = find_cellar_by_id(new_cellar_id)
    if not new_cellar:
        return jsonify({'error': 'New cellar not found'}), 404

    # Okay we've found the wine in the old cellar, so we're good to actually do the move.
    # Validate position before making changes
    if not new_cellar.is_position_valid(shelf_index, side, position):
        return jsonify({'error': f'Invalid position: shelf_index={shelf_index}, side={side}, position={position}'}), 400
    if not new_cellar.is_position_available(shelf_index, side, position):
        return jsonify({'error': f'Position is already occupied: shelf_index={shelf_index}, side={side}, position={position}'}), 400

    if old_cellar is not None:
        old_cellar.remove_wine_from_cellar(instance)
        update_and_save_cellar(old_cellar)
    new_cellar.assign_wine_to_position(shelf_index, side, position, instance)
    update_and_save_cellar(new_cellar)
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    _update_and_save_wine_instance(instance)
    
    return jsonify(serialize_wine_instance(instance))


# Unshelved endpoints
"""
Get all unshelved wine instances (wines not currently in a cellar and not consumed)
"""
@wine_instances_bp.route('/unshelved', methods=['GET'])
def _get_unshelved():
    """Get all unshelved wine instances"""

    # TODO: We need a better way to implement this. For now, just find all wines that aren't
    # in a cellar. This is n^2 right now.
    instances = get_all_wine_instances()

    unshelved = [i for i in instances 
                 if not find_cellar_containing_wine_instance(i) and not i.consumed]
    return jsonify([serialize_wine_instance(i) for i in unshelved])