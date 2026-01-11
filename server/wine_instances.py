"""Wine instance management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional, Tuple
from server.utils import generate_id, get_current_timestamp
from server.models import WineInstance, WineReference
from server.data.storage_serializers import serialize_wine_instance, deserialize_wine_instance
from server.cellars import find_cellar_by_id, save_cellars, load_cellars, update_and_save_cellar
from server.dynamo.storage import (
    load_wine_instances as dynamodb_load_wine_instances,
    save_wine_instances as dynamodb_save_wine_instances,
    get_wine_instance_by_id as dynamodb_get_wine_instance_by_id,
    update_wine_instance as dynamodb_update_wine_instance,
    delete_wine_instance as dynamodb_delete_wine_instance
)

wine_instances_bp = Blueprint('wine_instances', __name__)


# Helper functions
def load_wine_instances(cellars: Optional[List] = None) -> List[WineInstance]:
    """Load wine instances from DynamoDB as WineInstance model objects
    
    Args:
        cellars: Optional list of Cellar objects for resolving location tuples.
                 If None, location will be None for all instances.
    """
    data = dynamodb_load_wine_instances()
    return [deserialize_wine_instance(i, cellars) for i in data]


def save_wine_instances(instances: List[WineInstance]):
    """Save wine instances to DynamoDB (accepts WineInstance model objects)"""
    data = [serialize_wine_instance(i) for i in instances if i is not None]
    dynamodb_save_wine_instances(data)


def find_wine_instance_by_id(instance_id: str) -> Optional[WineInstance]:
    """Find a wine instance by ID (returns WineInstance model object)"""
    cellars = load_cellars()
    data = dynamodb_get_wine_instance_by_id(instance_id)
    if not data:
        return None
    return deserialize_wine_instance(data, cellars)


def _update_and_save_wine_instance(instance: WineInstance):
    """Helper function to update and save a wine instance in DynamoDB"""
    data = serialize_wine_instance(instance)
    dynamodb_update_wine_instance(data)


def _location_dict_to_tuple(location_dict: Dict, cellars: List) -> Optional[Tuple]:
    """Convert API request location dictionary to tuple (Cellar, Shelf, int, bool) or None
    
    Handles API request format: {type: "cellar", cellarId, shelfIndex, side: "front"|"back"|"single", position}
    Converts side string to isFront boolean for internal tuple format.
    """
    if not location_dict or location_dict.get('type') == 'unshelved':
        return None
    
    # Handle API request format with side
    if location_dict.get('type') == 'cellar':
        cellar_id = location_dict.get('cellarId')
        shelf_index = location_dict.get('shelfIndex')
        side = location_dict.get('side')
        position = location_dict.get('position')
        
        if cellar_id and shelf_index is not None and side and position is not None:
            cellar = find_cellar_by_id(cellar_id)
            if cellar and 0 <= shelf_index < len(cellar.shelves):
                shelf = cellar.shelves[shelf_index]
                # Convert side to isFront boolean
                if shelf.is_double:
                    is_front = (side == 'front')
                else:
                    is_front = True  # For single shelves, always front
                return (cellar, shelf, position, is_front)
    
    return None


# Endpoints
"""
Get all wine instances

Response Format: Array of wine instance objects, each containing:
- id (str): Unique identifier for the wine instance
- referenceId (str): ID of the wine reference this instance belongs to
- location (dict, optional): Location object with:
  - cellarId (str): ID of the cellar where instance is located
  - shelfIndex (int): Index of the shelf in the cellar
  - position (int): Position number on the shelf
  - isFront (bool): True if on front side (or single shelf), False if on back side
  - null if instance is unshelved
- price (float, optional): Purchase price
- purchaseDate (str, optional): ISO 8601 date when purchased
- drinkByDate (str, optional): ISO 8601 date for recommended consumption
- consumed (bool): Whether the wine has been consumed
- consumedDate (str, optional): ISO 8601 timestamp when consumed
- storedDate (str, optional): ISO 8601 timestamp when stored
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when instance was created
- updatedAt (str): ISO 8601 timestamp when instance was last updated
"""
@wine_instances_bp.route('/wine-instances', methods=['GET'])
def get_wine_instances():
    """Get all wine instances"""
    cellars = load_cellars()
    instances = load_wine_instances(cellars=cellars)
    return jsonify([serialize_wine_instance(i) for i in instances])


"""
Create a new wine instance

Expected POST Parameters:
- referenceId (str, required): ID of the wine reference this instance belongs to
- price (float, optional): Purchase price of the wine instance
- purchaseDate (str, optional): ISO 8601 date string when the wine was purchased
- drinkByDate (str, optional): ISO 8601 date string for recommended consumption date
- location (dict, optional): Location object. If provided, must be:
  {
    'type': 'cellar',
    'cellarId': str,
    'shelfIndex': int,
    'side': 'front'|'back'|'single',
    'position': int
  }
  If not provided, instance will be created as unshelved (location: null)
"""
@wine_instances_bp.route('/wine-instances', methods=['POST'])
def create_wine_instance():
    """Create a new wine instance"""
    from server.wine_references import find_wine_reference_by_id
    
    data = request.json
    
    # Verify reference exists
    reference = find_wine_reference_by_id(data.get('referenceId'))
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    # Convert location dict to tuple if provided
    location_tuple = None
    location_data = data.get('location')
    if location_data:
        cellars = load_cellars()
        location_tuple = _location_dict_to_tuple(location_data, cellars)
    
    # Create WineInstance model object
    instance = WineInstance(
        id=generate_id(),
        reference=reference,  # Use WineReference object
        location=location_tuple,  # Use tuple or None
        price=data.get('price'),
        purchase_date=data.get('purchaseDate'),
        drink_by_date=data.get('drinkByDate'),
        consumed=False,
        consumed_date=None,
        stored_date=get_current_timestamp()
    )
    
    # If location is provided, assign to cellar position
    if location_tuple is not None:
        cellar, shelf, position, is_front = location_tuple
        # Convert is_front to side string
        if shelf.is_double:
            side = 'front' if is_front else 'back'
        else:
            side = 'single'
        
        # Find shelf index
        shelf_index = None
        for i, s in enumerate(cellar.shelves):
            if s is shelf:
                shelf_index = i
                break
        
        if shelf_index is not None:
            try:
                cellar.assign_wine_to_position(shelf_index, side, position, instance)
                # Save cellar
                update_and_save_cellar(cellar)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
    
    # Add version and timestamps
    timestamp = get_current_timestamp()
    instance.version = 1
    instance.created_at = timestamp
    instance.updated_at = timestamp
    
    # Save to DynamoDB
    cellars = load_cellars()
    instances = load_wine_instances(cellars=cellars)
    instances.append(instance)
    save_wine_instances(instances)
    
    return jsonify(serialize_wine_instance(instance)), 201


"""
Get a specific wine instance by ID

Response Format: Wine instance object containing:
- id (str): Unique identifier for the wine instance
- referenceId (str): ID of the wine reference this instance belongs to
- location (dict, optional): Location object with cellarId, shelfIndex, position, isFront (or null if unshelved)
- price (float, optional): Purchase price
- purchaseDate (str, optional): ISO 8601 date when purchased
- drinkByDate (str, optional): ISO 8601 date for recommended consumption
- consumed (bool): Whether the wine has been consumed
- consumedDate (str, optional): ISO 8601 timestamp when consumed
- storedDate (str, optional): ISO 8601 timestamp when stored
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when instance was created
- updatedAt (str): ISO 8601 timestamp when instance was last updated

Error Response (404): {'error': 'Wine instance not found'} if instance doesn't exist
"""
@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['GET'])
def get_wine_instance(instance_id: str):
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

Note: referenceId and location cannot be updated via this endpoint.
Use PUT /wine-instances/<instance_id>/location to update location.
"""
@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['PUT'])
def update_wine_instance(instance_id: str):
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
    
    # Save to file
    _update_and_save_wine_instance(instance)
    
    return jsonify(serialize_wine_instance(instance))


@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['DELETE'])
def delete_wine_instance(instance_id: str):
    """Delete a wine instance"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    # Remove from cellar position if applicable
    if instance.location is not None:
        cellar, shelf, position, is_front = instance.location
        # Convert is_front to side string
        if shelf.is_double:
            side = 'front' if is_front else 'back'
        else:
            side = 'single'
        
        # Find shelf index
        shelf_index = None
        for i, s in enumerate(cellar.shelves):
            if s is shelf:
                shelf_index = i
                break
        
        if shelf_index is not None:
            cellar.remove_wine_from_position(shelf_index, side, position)
            # Save cellar
            update_and_save_cellar(cellar)
    
    # Delete from DynamoDB
    dynamodb_delete_wine_instance(instance_id)
    
    return jsonify({'message': 'Wine instance deleted'}), 200


@wine_instances_bp.route('/wine-instances/<instance_id>/consume', methods=['POST'])
def consume_wine_instance(instance_id: str):
    """Mark a wine instance as consumed (soft delete)"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    instance.consumed = True
    instance.consumed_date = get_current_timestamp()
    
    # Remove from cellar position if it was in a cellar
    if instance.location is not None:
        cellar, shelf, position, is_front = instance.location
        # Convert is_front to side string
        if shelf.is_double:
            side = 'front' if is_front else 'back'
        else:
            side = 'single'
        
        # Find shelf index
        shelf_index = None
        for i, s in enumerate(cellar.shelves):
            if s is shelf:
                shelf_index = i
                break
        
        if shelf_index is not None:
            cellar.remove_wine_from_position(shelf_index, side, position)
            # Save cellar
            update_and_save_cellar(cellar)
    
    # Clear location since it's no longer in the cellar
    instance.location = None
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    _update_and_save_wine_instance(instance)
    
    return jsonify(serialize_wine_instance(instance))


"""
Update wine instance location

Expected PUT Parameters:
- location (dict, required): Location object. Can be:
  - null or {'type': 'unshelved'} to mark as unshelved
  - {
      'type': 'cellar',
      'cellarId': str (required),
      'shelfIndex': int (required),
      'side': 'front'|'back'|'single' (required),
      'position': int (required)
    } to assign to a cellar position
"""
@wine_instances_bp.route('/wine-instances/<instance_id>/location', methods=['PUT'])
def update_wine_instance_location(instance_id: str):
    """Update wine instance location"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    if 'location' not in data:
        return jsonify({'error': 'Location is required'}), 400
    
    new_location_data = data['location']
    
    # Convert new location dict to tuple if provided
    new_location_tuple = None
    if new_location_data and new_location_data.get('type') == 'cellar':
        cellar_id = new_location_data.get('cellarId')
        shelf_index = new_location_data.get('shelfIndex')
        side = new_location_data.get('side')
        position = new_location_data.get('position')
        
        if cellar_id is None or shelf_index is None or side is None or position is None:
            return jsonify({'error': 'Cellar location requires cellarId, shelfIndex, side, and position'}), 400
        
        cellar = find_cellar_by_id(cellar_id)
        if not cellar:
            return jsonify({'error': 'Cellar not found'}), 404
        
        # Validate position using Cellar model methods
        if not cellar.is_position_valid(shelf_index, side, position):
            return jsonify({'error': 'Invalid position'}), 400
        if not cellar.is_position_available(shelf_index, side, position):
            return jsonify({'error': 'Position already occupied'}), 400
        
        # Get shelf and convert side to isFront
        shelf = cellar.shelves[shelf_index]
        if shelf.is_double:
            is_front = (side == 'front')
        else:
            is_front = True  # For single shelves
        
        # Remove from old position if moving from another cellar location
        old_location = instance.location
        if old_location is not None:
            old_cellar, old_shelf, old_position, old_is_front = old_location
            if old_cellar.id == cellar_id:
                # Convert old_is_front to side string
                if old_shelf.is_double:
                    old_side = 'front' if old_is_front else 'back'
                else:
                    old_side = 'single'
                
                # Find old shelf index
                old_shelf_index = None
                for i, s in enumerate(old_cellar.shelves):
                    if s is old_shelf:
                        old_shelf_index = i
                        break
                
                if old_shelf_index is not None:
                    cellar.remove_wine_from_position(old_shelf_index, old_side, old_position)
                else:
                    return jsonify({'error': 'Old shelf not found'}), 404 # This should never happen, but just in case.
        
        # Assign to new position (pass WineInstance object, not ID)
        cellar.assign_wine_to_position(shelf_index, side, position, instance)
        
        # Create location tuple
        new_location_tuple = (cellar, shelf, position, is_front)
        
        # Save cellar
        update_and_save_cellar(cellar)
    
    instance.location = new_location_tuple
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    _update_and_save_wine_instance(instance)
    
    return jsonify(serialize_wine_instance(instance))


# Unshelved endpoints
"""
Get all unshelved wine instances (wines not currently in a cellar and not consumed)

Response Format: Array of wine instance objects (same format as GET /wine-instances),
but filtered to only include instances where:
- location is null (not assigned to any cellar position)
- consumed is false (not yet consumed)

Each instance object contains the same fields as described in GET /wine-instances
"""
@wine_instances_bp.route('/unshelved', methods=['GET'])
def get_unshelved():
    """Get all unshelved wine instances"""
    cellars = load_cellars()
    instances = load_wine_instances(cellars=cellars)
    unshelved = [i for i in instances 
                 if i.location is None and not i.consumed]
    return jsonify([serialize_wine_instance(i) for i in unshelved])


"""
Assign unshelved wine to a cellar shelf location

Expected POST Parameters:
- location (dict, required): Location object with the following structure:
  {
    'type': 'cellar' (required, must be 'cellar'),
    'cellarId': str (required),
    'shelfIndex': int (required),
    'side': 'front'|'back'|'single' (required),
    'position': int (required)
  }
"""
@wine_instances_bp.route('/unshelved/<instance_id>/assign', methods=['POST'])
def assign_unshelved_to_cellar(instance_id: str):
    """Assign unshelved wine to a cellar shelf location"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    if 'location' not in data:
        return jsonify({'error': 'Location is required'}), 400
    
    new_location_data = data['location']
    
    # Validate and convert location dict to tuple
    if not new_location_data or new_location_data.get('type') != 'cellar':
        return jsonify({'error': 'Location type must be "cellar" for assignment'}), 400
    
    cellar_id = new_location_data.get('cellarId')
    shelf_index = new_location_data.get('shelfIndex')
    side = new_location_data.get('side')
    position = new_location_data.get('position')
    
    if cellar_id is None or shelf_index is None or side is None or position is None:
        return jsonify({'error': 'Cellar location requires cellarId, shelfIndex, side, and position'}), 400
    
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    # Validate position using Cellar model methods
    if not cellar.is_position_valid(shelf_index, side, position):
        return jsonify({'error': 'Invalid position'}), 400
    
    # Check if position is available
    if not cellar.is_position_available(shelf_index, side, position):
        return jsonify({'error': 'Position already occupied'}), 400
    
    # Get shelf and convert side to isFront
    shelf = cellar.shelves[shelf_index]
    if shelf.is_double:
        is_front = (side == 'front')
    else:
        is_front = True  # For single shelves
    
    # Assign to position using Cellar model method (pass WineInstance object, not ID)
    cellar.assign_wine_to_position(shelf_index, side, position, instance)
    
    # Create location tuple
    new_location_tuple = (cellar, shelf, position, is_front)
    
    # Save cellar
    update_and_save_cellar(cellar)
    
    instance.location = new_location_tuple
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    _update_and_save_wine_instance(instance)
    
    return jsonify(serialize_wine_instance(instance))
