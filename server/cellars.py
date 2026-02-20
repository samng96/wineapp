"""Cellar management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import List, Optional
from server.utils import generate_id, get_current_timestamp
from server.models import Cellar, Shelf, WineInstance
from server.data.storage_serializers import serialize_cellar, deserialize_cellar
# Import moved inside functions to avoid circular import
from server.dynamo.storage import (
    get_all_cellars as dynamodb_get_all_cellars,
    put_cellar as dynamodb_put_cellar,
    get_cellar_by_id as dynamodb_get_cellar_by_id,
    delete_cellar as dynamodb_delete_cellar
)

cellars_bp = Blueprint('cellars', __name__)

def find_cellar_by_id(cellar_id: str) -> Optional[Cellar]:
    """Get a cellar by ID (returns Cellar model object)"""
    data = dynamodb_get_cellar_by_id(cellar_id)
    if not data:
        return None

    # Load wine instances to resolve references (lazy import to avoid circular dependency)
    from server.wine_instances import get_all_wine_instances
    instances = get_all_wine_instances()
    return deserialize_cellar(data, instances)

def find_cellar_containing_wine_instance(instance: WineInstance) -> Optional[Cellar]:
    """Find a cellar containing a wine instance"""
    for cellar in _get_all_cellars():
        if cellar.is_wine_instance_in_cellar(instance):
            return cellar
    return None

def update_and_save_cellar(cellar: Cellar):
    """Update and save a cellar"""
    cellar.version += 1
    cellar.updated_at = get_current_timestamp()
    data = serialize_cellar(cellar)
    dynamodb_put_cellar(data)

def _get_all_cellars() -> List[Cellar]:
    """Get all cellars"""
    data = dynamodb_get_all_cellars()
    # Lazy import to avoid circular dependency
    from server.wine_instances import get_all_wine_instances
    instances = get_all_wine_instances()
    return [deserialize_cellar(c, instances) for c in data]

# Endpoints
"""
Get all cellars

Response Format: Array of cellar objects, each containing:
- id (str): Unique identifier for the cellar
- name (str): Name of the cellar
- shelves (list): List of shelf configurations, each as [positions, isDouble]
- temperature (float, optional): Temperature in Fahrenheit
- capacity (int): Total bottle capacity (calculated from shelves)
- winePositions (dict): Dictionary mapping shelf index (as string) to wine positions structure
  for each shelf (front/back/single with instance IDs)
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when cellar was created
- updatedAt (str): ISO 8601 timestamp when cellar was last updated
"""
@cellars_bp.route('/cellars', methods=['GET'])
def _get_cellars():
    """Get all cellars"""
    cellars = _get_all_cellars()
    return jsonify([serialize_cellar(c) for c in cellars])

"""
Create a new cellar

Expected POST Parameters:
- name (str, optional): Name of the cellar
- shelves (list, required): List of shelf configurations. Each shelf is a list of [positions, isDouble]
  where positions (int) is the number of bottle positions per side, and isDouble (bool) indicates
  if the shelf has front/back sides (True) or is single-sided (False)
- temperature (float, optional): Temperature in Fahrenheit for the cellar
"""
@cellars_bp.route('/cellars', methods=['POST'])
def _create_cellar():
    """Create a new cellar"""
    data = request.json

    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400

    if 'shelves' not in data:
        return jsonify({'error': 'shelves is required'}), 400

    shelves_data = data.get('shelves', [])

    # Validate and convert shelves to Shelf objects
    try:
        shelves = []
        for shelf_tuple in shelves_data:
            if not isinstance(shelf_tuple, list) or len(shelf_tuple) != 2:
                raise ValueError("Each shelf must be a list of [positions, isDouble]")
            if not isinstance(shelf_tuple[0], int) or shelf_tuple[0] <= 0:
                raise ValueError("Positions must be a positive integer")
            if not isinstance(shelf_tuple[1], bool):
                raise ValueError("IsDouble must be a boolean")
            shelves.append(Shelf(positions=shelf_tuple[0], is_double=shelf_tuple[1]))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # Create Cellar model object
    # Capacity will be calculated automatically in __post_init__ if not provided
    timestamp = get_current_timestamp()
    cellar = Cellar(
        id=generate_id(),
        name=data.get('name'),
        shelves=shelves,
        temperature=data.get('temperature'),
        version=1,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    # Save to DynamoDB
    data = serialize_cellar(cellar)
    dynamodb_put_cellar(data)
    
    return jsonify(data), 201


"""
Get a specific cellar by ID

Response Format: Cellar object containing:
- id (str): Unique identifier for the cellar
- name (str): Name of the cellar
- shelves (list): List of shelf configurations, each as [positions, isDouble]
- temperature (float, optional): Temperature in Fahrenheit
- capacity (int): Total bottle capacity (calculated from shelves)
- winePositions (dict): Dictionary mapping shelf index (as string) to wine positions structure
  for each shelf (front/back/single with instance IDs)
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when cellar was created
- updatedAt (str): ISO 8601 timestamp when cellar was last updated

Error Response (404): {'error': 'Cellar not found'} if cellar doesn't exist
"""
@cellars_bp.route('/cellars/<cellar_id>', methods=['GET'])
def _get_cellar(cellar_id: str):
    """Get a specific cellar by ID"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    return jsonify(serialize_cellar(cellar))


"""
Update a cellar

Expected PUT Parameters (all optional):
- name (str, optional): Updated name of the cellar
- temperature (float, optional): Updated temperature in Fahrenheit

Note: shelves cannot be updated via this endpoint (bulk updates not allowed).
"""
@cellars_bp.route('/cellars/<cellar_id>', methods=['PUT'])
def _update_cellar(cellar_id: str):
    """Update a cellar"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    data = request.json

    # We don't want to allow bulk updating the shelves, so if the user submitted shelf data, reject the request.
    if 'shelves' in data:
        return jsonify({'error': 'Cannot bulk-update shelf data on a cellar.'}), 404
    
    # Update fields if provided
    if 'name' in data:
        cellar.name = data['name']
    if 'temperature' in data:
        cellar.temperature = data['temperature']

    update_and_save_cellar(cellar)
    return jsonify(serialize_cellar(cellar))


@cellars_bp.route('/cellars/<cellar_id>', methods=['DELETE'])
def _delete_cellar(cellar_id: str):
    """Delete a cellar"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    # Remove all wine instances from this cellar before deleting
    # Find all instances in the cellar
    instances_to_remove = []
    for shelf in cellar.shelves:
        if shelf.is_double:
            sides = ['front', 'back']
        else:
            sides = ['single']
        for side in sides:
            for position in range(shelf.positions):
                instance = shelf.get_wine_at(side, position)
                if instance is not None:
                    assert instance.consumed is False, "Wine instance is consumed but still in a cellar"
                    instances_to_remove.append(instance)
                    shelf.set_wine_at(side, position, None)
    
    from server.wine_instances import save_wine_instances
    save_wine_instances(instances_to_remove)

    # Delete the cellar
    dynamodb_delete_cellar(cellar_id)
    return jsonify({'message': 'Cellar deleted'}), 200


"""
Consume a wine instance in a cellar

Expected POST Parameters:
- instance_id (str): ID of the wine instance to consume
"""
@cellars_bp.route('/cellars/<cellar_id>/consume_instance/<instance_id>', methods=['POST'])
def _consume_wine_instance(cellar_id: str, instance_id: str):
    """Consume a wine instance in a cellar"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    instance = None
    for shelf in cellar.shelves:
        for position in shelf.positions:
            if position.wine_instance.id == instance_id:
                # We found it - remove the wine from the position
                instance = position.wine_instance
                position.wine_instance = None
                position.version += 1
                position.updated_at = get_current_timestamp()
                break
        if instance is not None:
            break
    
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404

    from server.wine_instances import consume_wine_instance
    consume_wine_instance(instance)
    dynamodb_put_cellar(serialize_cellar(cellar))
    return jsonify({'message': 'Wine instance consumed'}), 200
