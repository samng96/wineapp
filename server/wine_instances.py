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
    
    instance['location'] = data['location']
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
    """Assign unshelved wine to a cellar location"""
    instance = find_wine_instance_by_id(instance_id)
    if not instance:
        return jsonify({'error': 'Wine instance not found'}), 404
    
    data = request.json
    if 'location' not in data:
        return jsonify({'error': 'Location is required'}), 400
    
    instance['location'] = data['location']
    instance = add_version_and_timestamps(instance, is_new=False)
    
    instances = load_wine_instances()
    for i, inst in enumerate(instances):
        if inst['id'] == instance_id:
            instances[i] = instance
            break
    save_wine_instances(instances)
    
    return jsonify(instance)
