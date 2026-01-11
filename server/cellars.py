"""Cellar management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
from server.utils import generate_id, get_current_timestamp
from server.models import Cellar, Shelf
from server.data.storage_serializers import serialize_cellar, deserialize_cellar
from server.dynamo.storage import (
    load_cellars as dynamodb_load_cellars,
    save_cellars as dynamodb_save_cellars,
    get_cellar_by_id as dynamodb_get_cellar_by_id,
    update_cellar as dynamodb_update_cellar,
    delete_cellar as dynamodb_delete_cellar
)

cellars_bp = Blueprint('cellars', __name__)


# Helper functions
def load_cellars() -> List[Cellar]:
    """Load cellars from DynamoDB as Cellar model objects with WineInstance objects resolved"""
    data = dynamodb_load_cellars()
    # Load cellars first without wine instances to break circular dependency
    cellars_temp = [deserialize_cellar(c, {}) for c in data]  # Empty dict for now
    
    # Load wine instances with cellars for location resolution
    from server.wine_instances import load_wine_instances
    wine_instances_list = load_wine_instances(cellars=cellars_temp)
    wine_instances_dict = {inst.id: inst for inst in wine_instances_list}
    
    # Now reload cellars with resolved wine instances
    return [deserialize_cellar(c, wine_instances_dict) for c in data]


def save_cellars(cellars: List[Cellar]):
    """Save cellars to DynamoDB (accepts Cellar model objects)"""
    data = [serialize_cellar(c) for c in cellars]
    dynamodb_save_cellars(data)


def find_cellar_by_id(cellar_id: str) -> Optional[Cellar]:
    """Find a cellar by ID (returns Cellar model object)"""
    data = dynamodb_get_cellar_by_id(cellar_id)
    if not data:
        return None
    
    # Load with wine instances resolved
    cellars_temp = [deserialize_cellar(data, {})]
    from server.wine_instances import load_wine_instances
    wine_instances_list = load_wine_instances(cellars=cellars_temp)
    wine_instances_dict = {inst.id: inst for inst in wine_instances_list}
    return deserialize_cellar(data, wine_instances_dict)


def update_and_save_cellar(cellar: Cellar):
    """Helper function to update and save a cellar in DynamoDB"""
    data = serialize_cellar(cellar)
    dynamodb_update_cellar(data)


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
def get_cellars():
    """Get all cellars"""
    cellars = load_cellars()
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
def create_cellar():
    """Create a new cellar"""
    data = request.json
    
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
    
    # Save to file
    cellars = load_cellars()
    cellars.append(cellar)
    save_cellars(cellars)
    
    return jsonify(serialize_cellar(cellar)), 201


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
def get_cellar(cellar_id: str):
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
def update_cellar(cellar_id: str):
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
    
    # Update version and timestamp
    cellar.version += 1
    cellar.updated_at = get_current_timestamp()
    
    # Save to file
    update_and_save_cellar(cellar)
    
    return jsonify(serialize_cellar(cellar))


@cellars_bp.route('/cellars/<cellar_id>', methods=['DELETE'])
def delete_cellar(cellar_id: str):
    """Delete a cellar"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    # Move all wine instances in this cellar to unshelved
    from server.wine_instances import load_wine_instances, save_wine_instances
    
    all_instances = load_wine_instances(cellars=[cellar])
    for instance in all_instances:
        if instance is not None:
            if instance.location is not None and instance.consumed is False:
                cellar_obj, shelf, position, is_front = instance.location
                if cellar_obj.id == cellar_id:
                    instance.location = None  # Set to None for unshelved
                    instance.version += 1
                    instance.updated_at = get_current_timestamp()
    
    # Save instances
    save_wine_instances(all_instances)
    
    # Delete the cellar
    dynamodb_delete_cellar(cellar_id)
    
    return jsonify({'message': 'Cellar deleted'}), 200