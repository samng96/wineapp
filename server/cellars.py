"""Cellar management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
import json
import os
from utils import (
    CELLARS_FILE, 
    generate_id, 
    add_version_and_timestamps,
    get_current_timestamp
)
from models import Cellar, Shelf, WineInstance
from wine_instances import load_wine_instances, save_wine_instances, load_wine_instances_as_models

cellars_bp = Blueprint('cellars', __name__)

# Helper functions
# Right now, load_cellars loads from our server's local files and then returns an in-memory list of cellars 
# so that other APIs can use it. In the future, we'll want to update this to use a database.
def load_cellars() -> List[Dict]:
    """Load cellars from JSON file as dictionaries"""
    if os.path.exists(CELLARS_FILE):
        with open(CELLARS_FILE, 'r') as f:
            return json.load(f)
    return []

def load_cellars_as_models() -> List[Cellar]:
    """Load cellars from JSON file as Cellar model objects with WineInstance objects resolved"""
    if os.path.exists(CELLARS_FILE):
        with open(CELLARS_FILE, 'r') as f:
            data = json.load(f)
            # Load wine instances to resolve IDs
            wine_instances_list = load_wine_instances_as_models()
            wine_instances_dict = {inst.id: inst for inst in wine_instances_list}
            return [Cellar.from_dict(c, wine_instances_dict) for c in data]
    return []

# Right now, save_cellars saves to the server's local files. In the future, we'll want to update this to use a database.
def save_cellars(cellars: List[Dict]):
    """Save cellars to JSON file (accepts dictionaries)"""
    with open(CELLARS_FILE, 'w') as f:
        json.dump(cellars, f, indent=2)

def save_cellars_from_models(cellars: List[Cellar]):
    """Save cellars to JSON file (accepts Cellar model objects)"""
    data = [c.to_dict() for c in cellars]
    save_cellars(data)

def find_cellar_by_id(cellar_id: str) -> Optional[Dict]:
    """Find a cellar by ID (returns dictionary)"""
    cellars = load_cellars()
    return next((c for c in cellars if c['id'] == cellar_id), None)

def find_cellar_by_id_as_model(cellar_id: str) -> Optional[Cellar]:
    """Find a cellar by ID (returns Cellar model object)"""
    cellars = load_cellars_as_models()
    return next((c for c in cellars if c.id == cellar_id), None)

# Endpoints
@cellars_bp.route('/cellars', methods=['GET'])
def get_cellars():
    """Get all cellars"""
    cellars = load_cellars()
    return jsonify(cellars)

@cellars_bp.route('/cellars', methods=['POST'])
def create_cellar():
    """Create a new cellar"""
    data = request.json
    
    shelves_data = data.get('shelves', [])
    
    # Validate and convert shelves to Shelf objects
    try:
        shelves = [Shelf.from_tuple(s) for s in shelves_data]
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # Create Cellar model object
    # Capacity will be calculated automatically in __post_init__ if not provided
    cellar = Cellar(
        id=generate_id(),
        name=data.get('name', 'Unnamed Cellar'),
        shelves=shelves,
        temperature=data.get('temperature'),
        capacity=data.get('capacity')  # Will be calculated if None
    )
    
    # Add version and timestamps
    cellar_dict = cellar.to_dict()
    cellar_dict = add_version_and_timestamps(cellar_dict, is_new=True)
    
    # Update model with timestamps
    cellar.created_at = cellar_dict['createdAt']
    cellar.updated_at = cellar_dict['updatedAt']
    cellar.version = cellar_dict['version']
    
    # Save to file
    cellars = load_cellars()
    cellars.append(cellar.to_dict())
    save_cellars(cellars)
    
    return jsonify(cellar.to_dict()), 201

@cellars_bp.route('/cellars/<cellar_id>', methods=['GET'])
def get_cellar(cellar_id: str):
    """Get a specific cellar"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    return jsonify(cellar)

@cellars_bp.route('/cellars/<cellar_id>', methods=['PUT'])
def update_cellar(cellar_id: str):
    """Update a cellar"""
    cellar_model = find_cellar_by_id_as_model(cellar_id)
    if not cellar_model:
        return jsonify({'error': 'Cellar not found'}), 404
    
    data = request.json
    
    # Update fields
    if 'name' in data:
        cellar_model.name = data['name']
    if 'temperature' in data:
        cellar_model.temperature = data['temperature']
    if 'capacity' in data:
        cellar_model.capacity = data['capacity']
    if 'shelves' in data:
        shelves_data = data['shelves']
        
        # Validate and convert shelves
        try:
            # Preserve wine positions from existing shelves
            old_shelves = cellar_model.shelves
            new_shelves = []
            
            # Load wine instances for resolving IDs if needed
            wine_instances_list = load_wine_instances_as_models()
            wine_instances_dict = {inst.id: inst for inst in wine_instances_list}
            
            for i, shelf_tuple in enumerate(shelves_data):
                # Try to preserve wine positions from old shelf at same index
                positions, is_double = shelf_tuple[0], shelf_tuple[1]
                
                # Get old shelf's wine positions as dict format for serialization
                old_wine_positions_ids = {}
                if i < len(old_shelves):
                    old_shelf = old_shelves[i]
                    old_wine_positions_ids = old_shelf.get_wine_positions_dict()
                
                # Create new shelf with preserved wine positions if compatible
                # Convert old positions to match new shelf structure
                if is_double:
                    # Need front/back structure
                    if 'front' in old_wine_positions_ids and 'back' in old_wine_positions_ids:
                        # Preserve and adjust size
                        front_ids = old_wine_positions_ids['front'][:positions]
                        back_ids = old_wine_positions_ids['back'][:positions]
                        while len(front_ids) < positions:
                            front_ids.append(None)
                        while len(back_ids) < positions:
                            back_ids.append(None)
                        wine_positions_ids = {'front': front_ids[:positions], 'back': back_ids[:positions]}
                    else:
                        # Reinitialize - structure changed
                        wine_positions_ids = {}
                else:
                    # Need single structure
                    if 'single' in old_wine_positions_ids:
                        # Preserve and adjust size
                        single_ids = old_wine_positions_ids['single'][:positions]
                        while len(single_ids) < positions:
                            single_ids.append(None)
                        wine_positions_ids = {'single': single_ids[:positions]}
                    else:
                        # Reinitialize - structure changed
                        wine_positions_ids = {}
                
                new_shelf = Shelf.from_tuple(shelf_tuple, wine_positions_ids, wine_instances_dict)
                new_shelves.append(new_shelf)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        cellar_model.shelves = new_shelves
        # Capacity will be recalculated automatically in __post_init__, but we need to trigger it
        # Since __post_init__ only runs on creation, we'll recalculate manually
        cellar_model.capacity = sum(shelf.positions * (2 if shelf.is_double else 1) for shelf in new_shelves)
    
    # Add version and timestamps
    cellar_dict = cellar_model.to_dict()
    cellar_dict = add_version_and_timestamps(cellar_dict, is_new=False)
    
    # Update model
    cellar_model.version = cellar_dict['version']
    cellar_model.updated_at = cellar_dict['updatedAt']
    
    # Save to file
    cellars = load_cellars()
    for i, c in enumerate(cellars):
        if c['id'] == cellar_id:
            cellars[i] = cellar_model.to_dict()
            break
    save_cellars(cellars)
    
    return jsonify(cellar_model.to_dict())

@cellars_bp.route('/cellars/<cellar_id>', methods=['DELETE'])
def delete_cellar(cellar_id: str):
    """Delete a cellar and move wines to unshelved"""
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    # Move all wine instances in this cellar to unshelved
    instances = load_wine_instances()
    for instance in instances:
        if (instance.get('location', {}).get('type') == 'cellar' and 
            instance.get('location', {}).get('cellarId') == cellar_id):
            instance['location'] = {'type': 'unshelved'}
            instance = add_version_and_timestamps(instance, is_new=False)
    
    save_wine_instances(instances)
    
    # Delete the cellar
    cellars = load_cellars()
    cellars = [c for c in cellars if c['id'] != cellar_id]
    save_cellars(cellars)
    
    return jsonify({'message': 'Cellar deleted'}), 200

@cellars_bp.route('/cellars/<cellar_id>/layout', methods=['GET'])
def get_cellar_layout(cellar_id: str):
    """Get graphical layout of cellar shelves and wine positions"""
    from wine_references import load_wine_references
    from wine_instances import find_wine_instance_by_id
    
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    # Load instances to populate positions with wine data
    instances = load_wine_instances()
    references = load_wine_references()
    
    # Create a reference lookup
    ref_lookup = {r['id']: r for r in references}
    
    # Enhance layout with wine information
    layout = cellar.copy()
    wine_positions = layout.get('winePositions', {})
    
    for shelf_index, positions_dict in wine_positions.items():
        for side, positions in positions_dict.items():
            for i, instance_id in enumerate(positions):
                if instance_id:
                    instance = find_wine_instance_by_id(instance_id)
                    if instance:
                        ref = ref_lookup.get(instance['referenceId'])
                        positions[i] = {
                            'instanceId': instance_id,
                            'wineReference': ref,
                            'instance': instance
                        }
    
    return jsonify(layout)
