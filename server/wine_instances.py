"""Wine instance management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
import json
import os
from utils import (
    WINE_INSTANCES_FILE,
    WINE_REFERENCES_FILE,
    generate_id,
    add_version_and_timestamps,
    get_current_timestamp
)

wine_instances_bp = Blueprint('wine_instances', __name__)

# Helper functions
def load_wine_instances() -> List[Dict]:
    """Load wine instances from JSON file"""
    if os.path.exists(WINE_INSTANCES_FILE):
        with open(WINE_INSTANCES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_wine_instances(instances: List[Dict]):
    """Save wine instances to JSON file"""
    with open(WINE_INSTANCES_FILE, 'w') as f:
        json.dump(instances, f, indent=2)

def find_wine_instance_by_id(instance_id: str) -> Optional[Dict]:
    """Find a wine instance by ID"""
    instances = load_wine_instances()
    return next((i for i in instances if i['id'] == instance_id), None)

def update_instance_count(reference_id: str):
    """Update the instance count for a wine reference"""
    # Import here to avoid circular dependency
    import json
    import os
    
    if os.path.exists(WINE_REFERENCES_FILE):
        with open(WINE_REFERENCES_FILE, 'r') as f:
            references = json.load(f)
    else:
        return
    
    instances = load_wine_instances()
    
    for ref in references:
        if ref['id'] == reference_id:
            active_instances = [i for i in instances 
                              if i['referenceId'] == reference_id and not i.get('consumed', False)]
            ref['instanceCount'] = len(active_instances)
            with open(WINE_REFERENCES_FILE, 'w') as f:
                json.dump(references, f, indent=2)
            break

# Endpoints
@wine_instances_bp.route('/wine-instances', methods=['GET'])
def get_wine_instances():
    """Get all wine instances"""
    instances = load_wine_instances()
    return jsonify(instances)

@wine_instances_bp.route('/wine-instances', methods=['POST'])
def create_wine_instance():
    """Create a new wine instance"""
    from wine_references import find_wine_reference_by_id
    
    data = request.json
    
    # Verify reference exists
    reference = find_wine_reference_by_id(data.get('referenceId'))
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    instance = {
        'id': generate_id(),
        'referenceId': data.get('referenceId'),
        'location': data.get('location', {'type': 'unshelved'}),
        'price': data.get('price'),
        'purchaseDate': data.get('purchaseDate'),
        'drinkByDate': data.get('drinkByDate'),
        'consumed': False,
        'consumedDate': None,
        'storedDate': get_current_timestamp()
    }
    
    instance = add_version_and_timestamps(instance, is_new=True)
    
    instances = load_wine_instances()
    instances.append(instance)
    save_wine_instances(instances)
    
    # Update instance count
    update_instance_count(data.get('referenceId'))
    
    return jsonify(instance), 201

@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['GET'])
def get_wine_instance(instance_id: str):
    """Get a specific wine instance"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    return jsonify(instance)

@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['PUT'])
def update_wine_instance(instance_id: str):
    """Update a wine instance"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    
    # Update fields
    for field in ['location', 'price', 'purchaseDate', 'drinkByDate']:
        if field in data:
            instance[field] = data[field]
    
    instance = add_version_and_timestamps(instance, is_new=False)
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance
            break
    save_wine_instances(instances)
    
    return jsonify(instance)

@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['DELETE'])
def delete_wine_instance(instance_id: str):
    """Hard delete a wine instance"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    reference_id = instance['referenceId']
    
    instances = load_wine_instances()
    instances = [i for i in instances if i['id'] != instance_id]
    save_wine_instances(instances)
    
    # Update instance count
    update_instance_count(reference_id)
    
    return jsonify({'message': 'Wine instance deleted'}), 200

@wine_instances_bp.route('/wine-instances/<instance_id>/consume', methods=['POST'])
def consume_wine_instance(instance_id: str):
    """Mark a wine instance as consumed (soft delete)"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    instance['consumed'] = True
    instance['consumedDate'] = get_current_timestamp()
    
    # Remove from cellar position if it was in a cellar
    old_location = instance.get('location', {})
    if old_location.get('type') == 'cellar':
        from cellars import find_cellar_by_id, save_cellars, load_cellars
        
        cellar_id = old_location.get('cellarId')
        shelf_index = old_location.get('shelfIndex')
        side = old_location.get('side')
        position = old_location.get('position')
        
        if cellar_id and shelf_index is not None and side and position is not None:
            cellar = find_cellar_by_id(cellar_id)
            if cellar:
                wine_positions = cellar.get('winePositions', {})
                shelf_key = str(shelf_index)
                if shelf_key in wine_positions:
                    shelf_positions = wine_positions[shelf_key].get(side, [])
                    if position < len(shelf_positions) and shelf_positions[position] == instance_id:
                        shelf_positions[position] = None
                        cellar['winePositions'] = wine_positions
                        cellars = load_cellars()
                        for i, c in enumerate(cellars):
                            if c['id'] == cellar_id:
                                cellars[i] = cellar
                                break
                        save_cellars(cellars)
    
    # Clear location since it's no longer in the cellar
    instance['location'] = {'type': 'unshelved'}
    
    instance = add_version_and_timestamps(instance, is_new=False)
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance
            break
    save_wine_instances(instances)
    
    # Update instance count
    update_instance_count(instance['referenceId'])
    
    return jsonify(instance)

@wine_instances_bp.route('/wine-instances/<instance_id>/location', methods=['PUT'])
def update_wine_instance_location(instance_id: str):
    """Update wine instance location"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    if 'location' not in data:
        return jsonify({'error': 'Location is required'}), 400
    
    new_location = data['location']
    
    # If moving to a cellar, validate the position
    if new_location.get('type') == 'cellar':
        from cellars import find_cellar_by_id, save_cellars, load_cellars
        
        cellar_id = new_location.get('cellarId')
        shelf_index = new_location.get('shelfIndex')
        side = new_location.get('side')
        position = new_location.get('position')
        
        if cellar_id is None or shelf_index is None or side is None or position is None:
            return jsonify({'error': 'Cellar location requires cellarId, shelfIndex, side, and position'}), 400
        
        cellar = find_cellar_by_id(cellar_id)
        if not cellar:
            return jsonify({'error': 'Cellar not found'}), 404
        
        shelves = cellar.get('shelves', [])
        if shelf_index < 0 or shelf_index >= len(shelves):
            return jsonify({'error': 'Invalid shelf index'}), 400
        
        positions, is_double = shelves[shelf_index]
        
        # Validate side
        if is_double:
            if side not in ['front', 'back']:
                return jsonify({'error': 'Side must be "front" or "back" for double-sided shelf'}), 400
        else:
            if side != 'single':
                return jsonify({'error': 'Side must be "single" for single-sided shelf'}), 400
        
        # Validate position
        if position < 0 or position >= positions:
            return jsonify({'error': 'Position out of bounds'}), 400
        
        # Check if position is already occupied
        wine_positions = cellar.get('winePositions', {})
        shelf_key = str(shelf_index)
        if shelf_key in wine_positions:
            shelf_positions = wine_positions[shelf_key].get(side, [])
            if position < len(shelf_positions) and shelf_positions[position] is not None:
                existing_id = shelf_positions[position]
                if existing_id != instance_id:  # Allow same instance to stay in place
                    return jsonify({'error': 'Position already occupied'}), 400
        
        # Remove from old position if moving from another cellar location
        old_location = instance.get('location', {})
        if old_location.get('type') == 'cellar' and old_location.get('cellarId') == cellar_id:
            old_shelf_index = old_location.get('shelfIndex')
            old_side = old_location.get('side')
            old_position = old_location.get('position')
            
            if (old_shelf_index is not None and old_side and old_position is not None and
                str(old_shelf_index) in wine_positions):
                old_shelf_positions = wine_positions[str(old_shelf_index)].get(old_side, [])
                if old_position < len(old_shelf_positions) and old_shelf_positions[old_position] == instance_id:
                    old_shelf_positions[old_position] = None
        
        # Add to new position
        if shelf_key not in wine_positions:
            if is_double:
                wine_positions[shelf_key] = {'front': [None] * positions, 'back': [None] * positions}
            else:
                wine_positions[shelf_key] = {'single': [None] * positions}
        
        shelf_positions = wine_positions[shelf_key].get(side, [])
        # Ensure array is large enough
        while len(shelf_positions) <= position:
            shelf_positions.append(None)
        shelf_positions[position] = instance_id
        
        cellar['winePositions'] = wine_positions
        cellars = load_cellars()
        for i, c in enumerate(cellars):
            if c['id'] == cellar_id:
                cellars[i] = cellar
                break
        save_cellars(cellars)
    
    instance['location'] = new_location
    instance = add_version_and_timestamps(instance, is_new=False)
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance
            break
    save_wine_instances(instances)
    
    return jsonify(instance)

# Unshelved endpoints
@wine_instances_bp.route('/unshelved', methods=['GET'])
def get_unshelved():
    """Get all unshelved wine instances"""
    instances = load_wine_instances()
    unshelved = [i for i in instances 
                 if i.get('location', {}).get('type') == 'unshelved' and not i.get('consumed', False)]
    return jsonify(unshelved)

@wine_instances_bp.route('/unshelved/<instance_id>/assign', methods=['POST'])
def assign_unshelved_to_cellar(instance_id: str):
    """Assign unshelved wine to a cellar shelf location"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    if 'location' not in data:
        return jsonify({'error': 'Location is required'}), 400
    
    new_location = data['location']
    
    # Validate cellar location
    if new_location.get('type') != 'cellar':
        return jsonify({'error': 'Location type must be "cellar" for assignment'}), 400
    
    from cellars import find_cellar_by_id, save_cellars, load_cellars
    
    cellar_id = new_location.get('cellarId')
    shelf_index = new_location.get('shelfIndex')
    side = new_location.get('side')
    position = new_location.get('position')
    
    if cellar_id is None or shelf_index is None or side is None or position is None:
        return jsonify({'error': 'Cellar location requires cellarId, shelfIndex, side, and position'}), 400
    
    cellar = find_cellar_by_id(cellar_id)
    if not cellar:
        return jsonify({'error': 'Cellar not found'}), 404
    
    shelves = cellar.get('shelves', [])
    if shelf_index < 0 or shelf_index >= len(shelves):
        return jsonify({'error': 'Invalid shelf index'}), 400
    
    positions, is_double = shelves[shelf_index]
    
    # Validate side
    if is_double:
        if side not in ['front', 'back']:
            return jsonify({'error': 'Side must be "front" or "back" for double-sided shelf'}), 400
    else:
        if side != 'single':
            return jsonify({'error': 'Side must be "single" for single-sided shelf'}), 400
    
    # Validate position
    if position < 0 or position >= positions:
        return jsonify({'error': 'Position out of bounds'}), 400
    
    # Check if position is available
    wine_positions = cellar.get('winePositions', {})
    shelf_key = str(shelf_index)
    
    if shelf_key not in wine_positions:
        if is_double:
            wine_positions[shelf_key] = {'front': [None] * positions, 'back': [None] * positions}
        else:
            wine_positions[shelf_key] = {'single': [None] * positions}
    
    shelf_positions = wine_positions[shelf_key].get(side, [])
    # Ensure array is large enough
    while len(shelf_positions) <= position:
        shelf_positions.append(None)
    
    if shelf_positions[position] is not None:
        return jsonify({'error': 'Position already occupied'}), 400
    
    # Assign to position
    shelf_positions[position] = instance_id
    
    cellar['winePositions'] = wine_positions
    cellars = load_cellars()
    for i, c in enumerate(cellars):
        if c['id'] == cellar_id:
            cellars[i] = cellar
            break
    save_cellars(cellars)
    
    instance['location'] = new_location
    instance = add_version_and_timestamps(instance, is_new=False)
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance
            break
    save_wine_instances(instances)
    
    return jsonify(instance)
