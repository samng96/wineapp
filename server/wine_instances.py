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
from models import WineInstance, WineReference

wine_instances_bp = Blueprint('wine_instances', __name__)

# Helper functions
def load_wine_instances() -> List[Dict]:
    """Load wine instances from JSON file as dictionaries"""
    if os.path.exists(WINE_INSTANCES_FILE):
        with open(WINE_INSTANCES_FILE, 'r') as f:
            return json.load(f)
    return []

def load_wine_instances_as_models() -> List[WineInstance]:
    """Load wine instances from JSON file as WineInstance model objects"""
    if os.path.exists(WINE_INSTANCES_FILE):
        with open(WINE_INSTANCES_FILE, 'r') as f:
            data = json.load(f)
            return [WineInstance.from_dict(i) for i in data]
    return []

def save_wine_instances(instances: List[Dict]):
    """Save wine instances to JSON file (accepts dictionaries)"""
    with open(WINE_INSTANCES_FILE, 'w') as f:
        json.dump(instances, f, indent=2)

def save_wine_instances_from_models(instances: List[WineInstance]):
    """Save wine instances to JSON file (accepts WineInstance model objects)"""
    data = [i.to_dict() for i in instances]
    save_wine_instances(data)

def find_wine_instance_by_id(instance_id: str) -> Optional[Dict]:
    """Find a wine instance by ID (returns dictionary)"""
    instances = load_wine_instances()
    return next((i for i in instances if i['id'] == instance_id), None)

def find_wine_instance_by_id_as_model(instance_id: str) -> Optional[WineInstance]:
    """Find a wine instance by ID (returns WineInstance model object)"""
    instances = load_wine_instances_as_models()
    return next((i for i in instances if i.id == instance_id), None)

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
    from wine_references import find_wine_reference_by_id_as_model
    
    data = request.json
    
    # Verify reference exists
    reference = find_wine_reference_by_id_as_model(data.get('referenceId'))
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    # Create WineInstance model object (use reference object, not ID)
    instance = WineInstance(
        id=generate_id(),
        reference=reference,  # Use WineReference object
        location=data.get('location', {'type': 'unshelved'}),
        price=data.get('price'),
        purchase_date=data.get('purchaseDate'),
        drink_by_date=data.get('drinkByDate'),
        consumed=False,
        consumed_date=None,
        stored_date=get_current_timestamp()
    )
    
    # Add version and timestamps
    instance_dict = instance.to_dict()
    instance_dict = add_version_and_timestamps(instance_dict, is_new=True)
    
    # Update model
    instance.version = instance_dict['version']
    instance.created_at = instance_dict['createdAt']
    instance.updated_at = instance_dict['updatedAt']
    
    # Save to file
    instances = load_wine_instances()
    instances.append(instance.to_dict())
    save_wine_instances(instances)
    
    # Update instance count
    update_instance_count(data.get('referenceId'))
    
    return jsonify(instance.to_dict()), 201

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
    instance_model = find_wine_instance_by_id_as_model(instance_id)
    if not instance_model:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    
    # Update fields
    if 'location' in data:
        instance_model.location = data['location']
    if 'price' in data:
        instance_model.price = data['price']
    if 'purchaseDate' in data:
        instance_model.purchase_date = data['purchaseDate']
    if 'drinkByDate' in data:
        instance_model.drink_by_date = data['drinkByDate']
    
    instance_dict = instance_model.to_dict()
    instance_dict = add_version_and_timestamps(instance_dict, is_new=False)
    instance_model.version = instance_dict['version']
    instance_model.updated_at = instance_dict['updatedAt']
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance_model.to_dict()
            break
    save_wine_instances(instances)
    
    return jsonify(instance_model.to_dict())

@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['DELETE'])
def delete_wine_instance(instance_id: str):
    """Hard delete a wine instance"""
    instance_model = find_wine_instance_by_id_as_model(instance_id)
    if not instance_model:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    reference_id = instance_model.reference.id
    
    instances = load_wine_instances_as_models()
    instances = [i for i in instances if i.id != instance_id]
    from wine_instances import save_wine_instances_from_models
    save_wine_instances_from_models(instances)
    
    # Update instance count
    update_instance_count(reference_id)
    
    return jsonify({'message': 'Wine instance deleted'}), 200

@wine_instances_bp.route('/wine-instances/<instance_id>/consume', methods=['POST'])
def consume_wine_instance(instance_id: str):
    """Mark a wine instance as consumed (soft delete)"""
    instance_model = find_wine_instance_by_id_as_model(instance_id)
    if not instance_model:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    instance_model.consumed = True
    instance_model.consumed_date = get_current_timestamp()
    
    # Remove from cellar position if it was in a cellar
    old_location = instance_model.location
    if old_location.get('type') == 'cellar':
        from cellars import find_cellar_by_id, save_cellars, load_cellars
        
        cellar_id = old_location.get('cellarId')
        shelf_index = old_location.get('shelfIndex')
        side = old_location.get('side')
        position = old_location.get('position')
        
        if cellar_id and shelf_index is not None and side and position is not None:
            cellar = find_cellar_by_id(cellar_id)
            if cellar:
                cellar.remove_wine_from_position(shelf_index, side, position)
                # Save cellar
                cellars = load_cellars()
                for i, c in enumerate(cellars):
                    if c.id == cellar_id:
                        cellars[i] = cellar
                        break
                save_cellars(cellars)
    
    # Clear location since it's no longer in the cellar
    instance_model.location = {'type': 'unshelved'}
    
    instance_dict = instance_model.to_dict()
    instance_dict = add_version_and_timestamps(instance_dict, is_new=False)
    instance_model.version = instance_dict['version']
    instance_model.updated_at = instance_dict['updatedAt']
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance_model.to_dict()
            break
    save_wine_instances(instances)
    
    # Update instance count (use reference.id from WineReference object)
    update_instance_count(instance_model.reference.id)
    
    return jsonify(instance_model.to_dict())

@wine_instances_bp.route('/wine-instances/<instance_id>/location', methods=['PUT'])
def update_wine_instance_location(instance_id: str):
    """Update wine instance location"""
    instance_model = find_wine_instance_by_id_as_model(instance_id)
    if not instance_model:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    if 'location' not in data:
        return jsonify({'error': 'Location is required'}), 400
    
    new_location = data['location']
    
    # If moving to a cellar, validate the position using Cellar model
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
        
        # Validate position using Cellar model methods
        if not cellar.is_position_valid(shelf_index, side, position):
            return jsonify({'error': 'Invalid position'}), 400
        
        # Check if position is available
        if not cellar.is_position_available(shelf_index, side, position):
            # Allow same instance to stay in place
            old_location = instance_model.location
            if (old_location.get('type') == 'cellar' and 
                old_location.get('cellarId') == cellar_id and
                old_location.get('shelfIndex') == shelf_index and
                old_location.get('side') == side and
                old_location.get('position') == position):
                pass  # Same position, allow it
            else:
                return jsonify({'error': 'Position already occupied'}), 400
        
        # Remove from old position if moving from another cellar location
        old_location = instance_model.location
        if old_location.get('type') == 'cellar' and old_location.get('cellarId') == cellar_id:
            old_shelf_index = old_location.get('shelfIndex')
            old_side = old_location.get('side')
            old_position = old_location.get('position')
            
            if (old_shelf_index is not None and old_side and old_position is not None):
                cellar.remove_wine_from_position(old_shelf_index, old_side, old_position)
        
        # Assign to new position (pass WineInstance object, not ID)
        cellar.assign_wine_to_position(shelf_index, side, position, instance_model)
        
        # Save cellar
        cellars = load_cellars()
        for i, c in enumerate(cellars):
            if c.id == cellar_id:
                cellars[i] = cellar
                break
        save_cellars(cellars)
    
    instance_model.location = new_location
    instance_dict = instance_model.to_dict()
    instance_dict = add_version_and_timestamps(instance_dict, is_new=False)
    instance_model.version = instance_dict['version']
    instance_model.updated_at = instance_dict['updatedAt']
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance_model.to_dict()
            break
    save_wine_instances(instances)
    
    return jsonify(instance_model.to_dict())

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
    instance_model = find_wine_instance_by_id_as_model(instance_id)
    if not instance_model:
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
    
    # Validate position using Cellar model methods
    if not cellar.is_position_valid(shelf_index, side, position):
        return jsonify({'error': 'Invalid position'}), 400
    
    # Check if position is available
    if not cellar.is_position_available(shelf_index, side, position):
        return jsonify({'error': 'Position already occupied'}), 400
    
    # Assign to position using Cellar model method (pass WineInstance object, not ID)
    cellar.assign_wine_to_position(shelf_index, side, position, instance_model)
    
    # Save cellar
    cellars = load_cellars()
    for i, c in enumerate(cellars):
        if c.id == cellar_id:
            cellars[i] = cellar
            break
    save_cellars(cellars)
    
    instance_model.location = new_location
    instance_dict = instance_model.to_dict()
    instance_dict = add_version_and_timestamps(instance_dict, is_new=False)
    instance_model.version = instance_dict['version']
    instance_model.updated_at = instance_dict['updatedAt']
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance_model.to_dict()
            break
    save_wine_instances(instances)
    
    return jsonify(instance_model.to_dict())
