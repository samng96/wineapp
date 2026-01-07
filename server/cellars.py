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
from wine_instances import load_wine_instances, save_wine_instances

cellars_bp = Blueprint('cellars', __name__)

# Helper functions
# Right now, load_cellars loads from our server's local files and then returns an in-memory list of cellars 
# so that other APIs can use it. In the future, we'll want to update this to use a database.
def load_cellars() -> List[Dict]:
    """Load cellars from JSON file"""
    if os.path.exists(CELLARS_FILE):
        with open(CELLARS_FILE, 'r') as f:
            return json.load(f)
    return []

# Right now, save_cellars saves to the server's local files. In the future, we'll want to update this to use a database.
def save_cellars(cellars: List[Dict]):
    """Save cellars to JSON file"""
    with open(CELLARS_FILE, 'w') as f:
        json.dump(cellars, f, indent=2)

def find_cellar_by_id(cellar_id: str) -> Optional[Dict]:
    """Find a cellar by ID"""
    cellars = load_cellars()
    return next((c for c in cellars if c['id'] == cellar_id), None)

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
    
    shelves = data.get('shelves', [])
    
    # Validate shelves format: each shelf should be [Positions, IsDouble]
    for shelf in shelves:
        if not isinstance(shelf, list) or len(shelf) != 2:
            return jsonify({'error': 'Invalid shelf format. Each shelf must be [Positions, IsDouble]'}), 400
        if not isinstance(shelf[0], int) or shelf[0] <= 0:
            return jsonify({'error': 'Positions must be a positive integer'}), 400
        if not isinstance(shelf[1], bool):
            return jsonify({'error': 'IsDouble must be a boolean'}), 400
    
    # Initialize winePositions object for each shelf
    wine_positions = {}
    for i, shelf in enumerate(shelves):
        positions, is_double = shelf
        if is_double:
            wine_positions[str(i)] = {
                'front': [None] * positions,
                'back': [None] * positions
            }
        else:
            wine_positions[str(i)] = {
                'single': [None] * positions
            }
    
    cellar = {
        'id': generate_id(),
        'name': data.get('name', 'Unnamed Cellar'),
        'temperature': data.get('temperature'),
        'capacity': data.get('capacity'),
        'shelves': shelves,
        'winePositions': wine_positions
    }
    
    cellar = add_version_and_timestamps(cellar, is_new=True)
    
    cellars = load_cellars()
    cellars.append(cellar)
    save_cellars(cellars)
    
    return jsonify(cellar), 201

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
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    data = request.json
    
    # Update fields
    if 'name' in data:
        cellar['name'] = data['name']
    if 'temperature' in data:
        cellar['temperature'] = data['temperature']
    if 'capacity' in data:
        cellar['capacity'] = data['capacity']
    if 'shelves' in data:
        shelves = data['shelves']
        
        # Validate shelves format
        for shelf in shelves:
            if not isinstance(shelf, list) or len(shelf) != 2:
                return jsonify({'error': 'Invalid shelf format. Each shelf must be [Positions, IsDouble]'}), 400
            if not isinstance(shelf[0], int) or shelf[0] <= 0:
                return jsonify({'error': 'Positions must be a positive integer'}), 400
            if not isinstance(shelf[1], bool):
                return jsonify({'error': 'IsDouble must be a boolean'}), 400
        
        # Update shelves and reinitialize winePositions if needed
        # TODO: Handle repositioning of existing wines when shelves change
        cellar['shelves'] = shelves
        
        # Reinitialize winePositions for new shelf structure
        wine_positions = {}
        for i, shelf in enumerate(shelves):
            positions, is_double = shelf
            shelf_key = str(i)
            
            # Preserve existing positions if shelf index exists and structure matches
            if shelf_key in cellar.get('winePositions', {}):
                existing = cellar['winePositions'][shelf_key]
                if is_double and 'front' in existing and 'back' in existing:
                    # Keep existing positions, pad or truncate as needed
                    front = existing['front'][:positions] + [None] * max(0, positions - len(existing['front']))
                    back = existing['back'][:positions] + [None] * max(0, positions - len(existing['back']))
                    wine_positions[shelf_key] = {'front': front, 'back': back}
                elif not is_double and 'single' in existing:
                    single = existing['single'][:positions] + [None] * max(0, positions - len(existing['single']))
                    wine_positions[shelf_key] = {'single': single}
                else:
                    # Structure changed, reinitialize
                    if is_double:
                        wine_positions[shelf_key] = {'front': [None] * positions, 'back': [None] * positions}
                    else:
                        wine_positions[shelf_key] = {'single': [None] * positions}
            else:
                # New shelf, initialize
                if is_double:
                    wine_positions[shelf_key] = {'front': [None] * positions, 'back': [None] * positions}
                else:
                    wine_positions[shelf_key] = {'single': [None] * positions}
        
        cellar['winePositions'] = wine_positions
    
    cellar = add_version_and_timestamps(cellar, is_new=False)
    
    cellars = load_cellars()
    for i, c in enumerate(cellars):
        if c['id'] == cellar_id:
            cellars[i] = cellar
            break
    save_cellars(cellars)
    
    return jsonify(cellar)

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
