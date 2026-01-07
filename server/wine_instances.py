"""Wine instance management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional, Tuple
import json
import os
from server.utils import (
    WINE_INSTANCES_FILE,
    WINE_REFERENCES_FILE,
    generate_id,
    get_current_timestamp
)
from server.models import WineInstance, WineReference
from server.storage import serialize_wine_instance, deserialize_wine_instance
from server.cellars import find_cellar_by_id, save_cellars, load_cellars

wine_instances_bp = Blueprint('wine_instances', __name__)


# Helper functions
def load_wine_instances() -> List[Dict]:
    """Load wine instances from JSON file as dictionaries"""
    if os.path.exists(WINE_INSTANCES_FILE):
        with open(WINE_INSTANCES_FILE, 'r') as f:
            return json.load(f)
    return []


def load_wine_instances_as_models(cellars: Optional[List] = None) -> List[WineInstance]:
    """Load wine instances from JSON file as WineInstance model objects
    
    Args:
        cellars: Optional list of Cellar objects for resolving location tuples.
                 If None, location will be None for all instances.
    """
    if os.path.exists(WINE_INSTANCES_FILE):
        with open(WINE_INSTANCES_FILE, 'r') as f:
            data = json.load(f)
            return [deserialize_wine_instance(i, cellars) for i in data]
    return []


def save_wine_instances(instances: List[Dict]):
    """Save wine instances to JSON file (accepts dictionaries)"""
    with open(WINE_INSTANCES_FILE, 'w') as f:
        json.dump(instances, f, indent=2)


def save_wine_instances_from_models(instances: List[WineInstance]):
    """Save wine instances to JSON file (accepts WineInstance model objects)"""
    data = [serialize_wine_instance(i) for i in instances]
    save_wine_instances(data)


def find_wine_instance_by_id(instance_id: str) -> Optional[Dict]:
    """Find a wine instance by ID (returns dictionary)"""
    instances = load_wine_instances()
    return next((i for i in instances if i['id'] == instance_id), None)


def find_wine_instance_by_id_as_model(instance_id: str) -> Optional[WineInstance]:
    """Find a wine instance by ID (returns WineInstance model object)"""
    cellars = load_cellars()
    instances = load_wine_instances_as_models(cellars=cellars)
    return next((i for i in instances if i.id == instance_id), None)


def _location_dict_to_tuple(location_dict: Dict, cellars: List) -> Optional[Tuple]:
    """Convert location dictionary to tuple (Cellar, Shelf, int, bool) or None"""
    if not location_dict or location_dict.get('type') == 'unshelved':
        return None
    
    # Handle new format with isFront
    if 'cellarId' in location_dict and 'shelfIndex' in location_dict:
        cellar_id = location_dict.get('cellarId')
        shelf_index = location_dict.get('shelfIndex')
        position = location_dict.get('position')
        is_front = location_dict.get('isFront')
        
        if cellar_id and shelf_index is not None and position is not None and is_front is not None:
            cellar = find_cellar_by_id(cellar_id)
            if cellar and 0 <= shelf_index < len(cellar.shelves):
                shelf = cellar.shelves[shelf_index]
                return (cellar, shelf, position, is_front)
    
    # Handle old format with side (for backward compatibility)
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


def update_instance_count(reference_id: str):
    """Update the instance count for a wine reference"""
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
    from server.wine_references import find_wine_reference_by_id_as_model
    
    data = request.json
    
    # Verify reference exists
    reference = find_wine_reference_by_id_as_model(data.get('referenceId'))
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
                cellars = load_cellars()
                for i, c in enumerate(cellars):
                    if c.id == cellar.id:
                        cellars[i] = cellar
                        break
                save_cellars(cellars)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
    
    # Add version and timestamps
    timestamp = get_current_timestamp()
    instance.version = 1
    instance.created_at = timestamp
    instance.updated_at = timestamp
    
    # Save to file
    instances = load_wine_instances()
    instances.append(serialize_wine_instance(instance))
    save_wine_instances(instances)
    
    # Update instance count
    update_instance_count(data.get('referenceId'))
    
    return jsonify(serialize_wine_instance(instance)), 201


@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['GET'])
def get_wine_instance(instance_id: str):
    """Get a specific wine instance"""
    instance = find_wine_instance_by_id_as_model(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    return jsonify(serialize_wine_instance(instance))


@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['PUT'])
def update_wine_instance(instance_id: str):
    """Update a wine instance"""
    instance = find_wine_instance_by_id_as_model(instance_id)
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
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = serialize_wine_instance(instance)
            break
    save_wine_instances(instances)
    
    return jsonify(serialize_wine_instance(instance))


@wine_instances_bp.route('/wine-instances/<instance_id>', methods=['DELETE'])
def delete_wine_instance(instance_id: str):
    """Delete a wine instance"""
    instance = find_wine_instance_by_id_as_model(instance_id)
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
            cellars = load_cellars()
            for i, c in enumerate(cellars):
                if c.id == cellar.id:
                    cellars[i] = cellar
                    break
            save_cellars(cellars)
    
    # Delete from file
    instances = load_wine_instances()
    instances = [i for i in instances if i['id'] != instance_id]
    save_wine_instances(instances)
    
    # Update instance count (use reference.id from WineReference object)
    update_instance_count(instance.reference.id)
    
    return jsonify({'message': 'Wine instance deleted'}), 200


@wine_instances_bp.route('/wine-instances/<instance_id>/consume', methods=['POST'])
def consume_wine_instance(instance_id: str):
    """Mark a wine instance as consumed (soft delete)"""
    instance = find_wine_instance_by_id_as_model(instance_id)
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
            cellars = load_cellars()
            for i, c in enumerate(cellars):
                if c.id == cellar.id:
                    cellars[i] = cellar
                    break
            save_cellars(cellars)
    
    # Clear location since it's no longer in the cellar
    instance.location = None
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = serialize_wine_instance(instance)
            break
    save_wine_instances(instances)
    
    # Update instance count (use reference.id from WineReference object)
    update_instance_count(instance.reference.id)
    
    return jsonify(serialize_wine_instance(instance))


@wine_instances_bp.route('/wine-instances/<instance_id>/location', methods=['PUT'])
def update_wine_instance_location(instance_id: str):
    """Update wine instance location"""
    instance = find_wine_instance_by_id_as_model(instance_id)
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
        
        # Check if position is available
        if not cellar.is_position_available(shelf_index, side, position):
            # Allow same instance to stay in place
            old_location = instance.location
            if (old_location is not None and 
                old_location[0].id == cellar_id and
                old_location[2] == position):
                # Check if same shelf and side
                old_shelf = old_location[1]
                old_is_front = old_location[3]
                if shelf_index < len(cellar.shelves) and cellar.shelves[shelf_index] is old_shelf:
                    if shelf.is_double:
                        if (side == 'front' and old_is_front) or (side == 'back' and not old_is_front):
                            pass  # Same position, allow it
                        else:
                            return jsonify({'error': 'Position already occupied'}), 400
                    else:
                        if side == 'single':
                            pass  # Same position, allow it
                        else:
                            return jsonify({'error': 'Position already occupied'}), 400
                else:
                    return jsonify({'error': 'Position already occupied'}), 400
            else:
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
        
        # Assign to new position (pass WineInstance object, not ID)
        cellar.assign_wine_to_position(shelf_index, side, position, instance)
        
        # Create location tuple
        new_location_tuple = (cellar, shelf, position, is_front)
        
        # Save cellar
        cellars = load_cellars()
        for i, c in enumerate(cellars):
            if c.id == cellar_id:
                cellars[i] = cellar
                break
        save_cellars(cellars)
    
    instance.location = new_location_tuple
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = serialize_wine_instance(instance)
            break
    save_wine_instances(instances)
    
    return jsonify(serialize_wine_instance(instance))


# Unshelved endpoints
@wine_instances_bp.route('/unshelved', methods=['GET'])
def get_unshelved():
    """Get all unshelved wine instances"""
    cellars = load_cellars()
    instances = load_wine_instances_as_models(cellars=cellars)
    unshelved = [i for i in instances 
                 if i.location is None and not i.consumed]
    return jsonify([serialize_wine_instance(i) for i in unshelved])


@wine_instances_bp.route('/unshelved/<instance_id>/assign', methods=['POST'])
def assign_unshelved_to_cellar(instance_id: str):
    """Assign unshelved wine to a cellar shelf location"""
    instance = find_wine_instance_by_id_as_model(instance_id)
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
    cellars = load_cellars()
    for i, c in enumerate(cellars):
        if c.id == cellar_id:
            cellars[i] = cellar
            break
    save_cellars(cellars)
    
    instance.location = new_location_tuple
    
    # Update version and timestamp
    instance.version += 1
    instance.updated_at = get_current_timestamp()
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = serialize_wine_instance(instance)
            break
    save_wine_instances(instances)
    
    return jsonify(serialize_wine_instance(instance))
