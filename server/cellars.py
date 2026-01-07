"""Cellar management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
import json
import os
from server.utils import (
    CELLARS_FILE,
    WINE_INSTANCES_FILE,
    generate_id,
    get_current_timestamp
)
from server.models import Cellar, Shelf
from server.storage import serialize_cellar, deserialize_cellar

cellars_bp = Blueprint('cellars', __name__)


# Helper functions
def load_cellars() -> List[Cellar]:
    """Load cellars from JSON file as Cellar model objects with WineInstance objects resolved"""
    if os.path.exists(CELLARS_FILE):
        with open(CELLARS_FILE, 'r') as f:
            data = json.load(f)
            # Load cellars first without wine instances to break circular dependency
            cellars_temp = [deserialize_cellar(c, {}) for c in data]  # Empty dict for now
            
            # Load wine instances with cellars for location resolution
            from server.wine_instances import load_wine_instances_as_models
            wine_instances_list = load_wine_instances_as_models(cellars=cellars_temp)
            wine_instances_dict = {inst.id: inst for inst in wine_instances_list}
            
            # Now reload cellars with resolved wine instances
            return [deserialize_cellar(c, wine_instances_dict) for c in data]
    return []


def save_cellars(cellars: List[Cellar]):
    """Save cellars to JSON file (accepts Cellar model objects)"""
    data = [serialize_cellar(c) for c in cellars]
    with open(CELLARS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def find_cellar_by_id(cellar_id: str) -> Optional[Cellar]:
    """Find a cellar by ID (returns Cellar model object)"""
    cellars = load_cellars()
    return next((c for c in cellars if c.id == cellar_id), None)


# Endpoints
@cellars_bp.route('/cellars', methods=['GET'])
def get_cellars():
    """Get all cellars"""
    cellars = load_cellars()
    return jsonify([serialize_cellar(c) for c in cellars])


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


@cellars_bp.route('/cellars/<cellar_id>', methods=['GET'])
def get_cellar(cellar_id: str):
    """Get a specific cellar by ID"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    return jsonify(serialize_cellar(cellar))


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
    cellars = load_cellars()
    for i, c in enumerate(cellars):
        if c.id == cellar_id:
            cellars[i] = cellar
            break
    save_cellars(cellars)
    
    return jsonify(serialize_cellar(cellar))


@cellars_bp.route('/cellars/<cellar_id>', methods=['DELETE'])
def delete_cellar(cellar_id: str):
    """Delete a cellar"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    # Move all wine instances in this cellar to unshelved
    from server.wine_instances import load_wine_instances_as_models, save_wine_instances_from_models
    
    all_instances = load_wine_instances_as_models(cellars=[cellar])
    for instance in all_instances:
        if instance.location is not None:
            cellar_obj, shelf, position, is_front = instance.location
            if cellar_obj.id == cellar_id:
                instance.location = None  # Set to None for unshelved
                instance.version += 1
                instance.updated_at = get_current_timestamp()
    
    # Save instances
    save_wine_instances_from_models(all_instances)
    
    # Delete the cellar
    cellars = load_cellars()
    cellars = [c for c in cellars if c.id != cellar_id]
    save_cellars(cellars)
    
    return jsonify({'message': 'Cellar deleted'}), 200