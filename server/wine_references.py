"""Wine reference management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
import json
import os
from server.utils import (
    WINE_REFERENCES_FILE,
    WINE_INSTANCES_FILE,
    generate_id,
    get_current_timestamp
)
from server.models import WineReference, register_wine_reference
from server.storage import serialize_wine_reference, deserialize_wine_reference, serialize_wine_instance

wine_references_bp = Blueprint('wine_references', __name__)


# Helper functions
def load_wine_references() -> List[WineReference]:
    """Load wine references from JSON file as WineReference model objects"""
    if os.path.exists(WINE_REFERENCES_FILE):
        with open(WINE_REFERENCES_FILE, 'r') as f:
            data = json.load(f)
            return [deserialize_wine_reference(r) for r in data]
    return []


def save_wine_references(references: List[WineReference]):
    """Save wine references to JSON file (accepts WineReference model objects)"""
    data = [serialize_wine_reference(r) for r in references]
    with open(WINE_REFERENCES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def find_wine_reference_by_id(reference_id: str) -> Optional[WineReference]:
    """Find a wine reference by ID (returns WineReference model object)"""
    from server.models import get_wine_reference
    return get_wine_reference(reference_id)


# Endpoints
@wine_references_bp.route('/wine-references', methods=['GET'])
def get_wine_references():
    """Get all wine references"""
    references = load_wine_references()
    return jsonify([serialize_wine_reference(r) for r in references])


@wine_references_bp.route('/wine-references', methods=['POST'])
def create_wine_reference():
    """Create a new wine reference"""
    data = request.json
    
    # Validate required fields
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'name and type are required'}), 400
    
    # Create WineReference model object
    reference = WineReference(
        id=generate_id(),
        name=data.get('name'),
        type=data.get('type'),
        vintage=data.get('vintage'),
        producer=data.get('producer'),
        varietals=data.get('varietals', []),
        region=data.get('region'),
        country=data.get('country'),
        rating=data.get('rating'),
        tasting_notes=data.get('tastingNotes'),
        label_image_url=data.get('labelImageUrl')
    )
    
    # Check if reference already exists (name + vintage + producer)
    references = load_wine_references()
    existing = next((r for r in references if r.get_unique_key() == reference.get_unique_key()), None)
    
    if existing:
        return jsonify({'error': 'Wine reference already exists', 'reference': serialize_wine_reference(existing)}), 409
    
    # Add version and timestamps
    timestamp = get_current_timestamp()
    reference.version = 1
    reference.created_at = timestamp
    reference.updated_at = timestamp
    
    # Register in global registry
    register_wine_reference(reference)
    
    # Save to file
    references.append(reference)
    save_wine_references(references)
    
    return jsonify(serialize_wine_reference(reference)), 201


@wine_references_bp.route('/wine-references/<reference_id>', methods=['GET'])
def get_wine_reference(reference_id: str):
    """Get a specific wine reference with all instances"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    # Get all instances for this reference
    from server.wine_instances import load_wine_instances
    from server.cellars import load_cellars
    cellars = load_cellars()
    instances = load_wine_instances(cellars=cellars)
    reference_instances = [serialize_wine_instance(i) for i in instances if i.reference.id == reference_id]
    
    response = serialize_wine_reference(reference)
    response['instances'] = reference_instances
    
    return jsonify(response)


@wine_references_bp.route('/wine-references/<reference_id>', methods=['PUT'])
def update_wine_reference(reference_id: str):
    """Update a wine reference"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    data = request.json
    
    # Update fields
    if 'name' in data:
        reference.name = data['name']
    if 'type' in data:
        reference.type = data['type']
    if 'vintage' in data:
        reference.vintage = data['vintage']
    if 'producer' in data:
        reference.producer = data['producer']
    if 'varietals' in data:
        reference.varietals = data['varietals']
    if 'region' in data:
        reference.region = data['region']
    if 'country' in data:
        reference.country = data['country']
    if 'rating' in data:
        reference.rating = data['rating']
    if 'tastingNotes' in data:
        reference.tasting_notes = data['tastingNotes']
    if 'labelImageUrl' in data:
        reference.label_image_url = data['labelImageUrl']
    
    # Update version and timestamp
    reference.version += 1
    reference.updated_at = get_current_timestamp()
    
    # Update in global registry
    register_wine_reference(reference)
    
    # Save to file
    references = load_wine_references()
    for i, r in enumerate(references):
        if r.id == reference_id:
            references[i] = reference
            break
    save_wine_references(references)
    
    return jsonify(serialize_wine_reference(reference))


@wine_references_bp.route('/wine-references/<reference_id>', methods=['DELETE'])
def delete_wine_reference(reference_id: str):
    """Delete a wine reference"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    # Remove from global registry
    from server.models import _wine_references_registry
    if reference_id in _wine_references_registry:
        del _wine_references_registry[reference_id]
    
    # Remove from file
    references = load_wine_references()
    references = [r for r in references if r.id != reference_id]
    save_wine_references(references)
    
    return jsonify({'message': 'Wine reference deleted'}), 200
