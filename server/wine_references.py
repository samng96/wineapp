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

wine_references_bp = Blueprint('wine_references', __name__)

# Helper functions
def load_wine_references() -> List[Dict]:
    """Load wine references from JSON file"""
    if os.path.exists(WINE_REFERENCES_FILE):
        with open(WINE_REFERENCES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_wine_references(references: List[Dict]):
    """Save wine references to JSON file"""
    with open(WINE_REFERENCES_FILE, 'w') as f:
        json.dump(references, f, indent=2)

def find_wine_reference_by_id(reference_id: str) -> Optional[Dict]:
    """Find a wine reference by ID"""
    references = load_wine_references()
    return next((r for r in references if r['id'] == reference_id), None)

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
    
    # Check if reference already exists (name + vintage + producer)
    references = load_wine_references()
    existing = next((r for r in references 
                    if (r.get('name') == data.get('name') and
                        r.get('vintage') == data.get('vintage') and
                        r.get('producer') == data.get('producer'))), None)
    
    if existing:
        return jsonify({'error': 'Wine reference already exists', 'reference': existing}), 409
    
    reference = {
        'id': generate_id(),
        'name': data.get('name'),
        'type': data.get('type'),
        'vintage': data.get('vintage'),
        'producer': data.get('producer'),
        'varietals': data.get('varietals', []),
        'region': data.get('region'),
        'country': data.get('country'),
        'rating': data.get('rating'),
        'tastingNotes': data.get('tastingNotes'),
        'labelImageUrl': data.get('labelImageUrl'),
        'instanceCount': 0
    }
    
    reference = add_version_and_timestamps(reference, is_new=True)
    
    references.append(reference)
    save_wine_references(references)
    
    return jsonify(reference), 201

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
