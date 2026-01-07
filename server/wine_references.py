"""Wine reference management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
import json
import os
from utils import (
    WINE_REFERENCES_FILE,
    generate_id,
    add_version_and_timestamps
)
from models import WineReference, register_wine_reference

wine_references_bp = Blueprint('wine_references', __name__)

# Helper functions
def load_wine_references() -> List[Dict]:
    """Load wine references from JSON file as dictionaries"""
    if os.path.exists(WINE_REFERENCES_FILE):
        with open(WINE_REFERENCES_FILE, 'r') as f:
            return json.load(f)
    return []

def load_wine_references_as_models() -> List[WineReference]:
    """Load wine references from JSON file as WineReference model objects"""
    if os.path.exists(WINE_REFERENCES_FILE):
        with open(WINE_REFERENCES_FILE, 'r') as f:
            data = json.load(f)
            return [WineReference.from_dict(r) for r in data]
    return []

def save_wine_references(references: List[Dict]):
    """Save wine references to JSON file (accepts dictionaries)"""
    with open(WINE_REFERENCES_FILE, 'w') as f:
        json.dump(references, f, indent=2)

def save_wine_references_from_models(references: List[WineReference]):
    """Save wine references to JSON file (accepts WineReference model objects)"""
    data = [r.to_dict() for r in references]
    save_wine_references(data)

def find_wine_reference_by_id(reference_id: str) -> Optional[Dict]:
    """Find a wine reference by ID (returns dictionary)"""
    references = load_wine_references()
    return next((r for r in references if r['id'] == reference_id), None)

def find_wine_reference_by_id_as_model(reference_id: str) -> Optional[WineReference]:
    """Find a wine reference by ID (returns WineReference model object)"""
    from models import get_wine_reference
    # First try to get from global registry
    reference = get_wine_reference(reference_id)
    if reference:
        return reference
    # Fallback: load from file (which will register them)
    references = load_wine_references_as_models()
    return next((r for r in references if r.id == reference_id), None)

# Endpoints
@wine_references_bp.route('/wine-references', methods=['GET'])
def get_wine_references():
    """Get all wine references"""
    references = load_wine_references()
    return jsonify(references)

@wine_references_bp.route('/wine-references', methods=['POST'])
def create_wine_reference():
    """Create a new wine reference"""
    data = request.json
    
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
        label_image_url=data.get('labelImageUrl'),
        instance_count=0
    )
    
    # Check if reference already exists (name + vintage + producer)
    references = load_wine_references_as_models()
    existing = next((r for r in references if r.get_unique_key() == reference.get_unique_key()), None)
    
    if existing:
        return jsonify({'error': 'Wine reference already exists', 'reference': existing.to_dict()}), 409
    
    # Add version and timestamps
    reference_dict = reference.to_dict()
    reference_dict = add_version_and_timestamps(reference_dict, is_new=True)
    
    # Update model with timestamps
    reference.version = reference_dict['version']
    reference.created_at = reference_dict['createdAt']
    reference.updated_at = reference_dict['updatedAt']
    
    # Register in global registry
    register_wine_reference(reference)
    
    # Save to file
    references.append(reference)
    save_wine_references_from_models(references)
    
    return jsonify(reference.to_dict()), 201

@wine_references_bp.route('/wine-references/<reference_id>', methods=['GET'])
def get_wine_reference(reference_id: str):
    """Get a specific wine reference with all instances"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    # Get all instances for this reference
    from wine_instances import load_wine_instances
    instances = load_wine_instances()
    reference_instances = [i for i in instances if i['referenceId'] == reference_id]
    
    response = reference.copy()
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
    for field in ['name', 'type', 'vintage', 'producer', 'varietals', 'region', 
                  'country', 'rating', 'tastingNotes', 'labelImageUrl']:
        if field in data:
            reference[field] = data[field]
    
    reference = add_version_and_timestamps(reference, is_new=False)
    
    references = load_wine_references()
    for i, r in enumerate(references):
        if r['id'] == reference_id:
            references[i] = reference
            break
    save_wine_references(references)
    
    return jsonify(reference)

@wine_references_bp.route('/wine-references/<reference_id>', methods=['DELETE'])
def delete_wine_reference(reference_id: str):
    """Hard delete a wine reference and all its instances"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    
    # Delete all instances
    from wine_instances import load_wine_instances, save_wine_instances
    instances = load_wine_instances()
    instances = [i for i in instances if i['referenceId'] != reference_id]
    save_wine_instances(instances)
    
    # Delete the reference
    references = load_wine_references()
    references = [r for r in references if r['id'] != reference_id]
    save_wine_references(references)
    
    return jsonify({'message': 'Wine reference and all instances deleted'}), 200
