"""Wine reference management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
from server.utils import generate_id, get_current_timestamp
from server.models import GlobalWineReference
from server.data.storage_serializers import serialize_global_wine_reference, deserialize_global_wine_reference, serialize_wine_instance
from server.vivino_search import search_vivino
from server.dynamo.storage import (
    get_all_wine_references as dynamodb_get_all_wine_references,
    put_wine_reference as dynamodb_put_wine_reference,
    get_wine_reference_by_id as dynamodb_get_wine_reference_by_id,
    delete_wine_reference as dynamodb_delete_wine_reference
)

wine_references_bp = Blueprint('wine_references', __name__)


# Helper functions
def get_all_wine_references() -> List[GlobalWineReference]:
    """Load wine references from DynamoDB as GlobalWineReference model objects"""
    data = dynamodb_get_all_wine_references()
    return [deserialize_global_wine_reference(r) for r in data]

def find_wine_reference_by_id(reference_id: str) -> Optional[GlobalWineReference]:
    """Find a wine reference by ID (returns GlobalWineReference model object)"""
    data = dynamodb_get_wine_reference_by_id(reference_id)
    if not data:
        return None
    return deserialize_global_wine_reference(data)

# Endpoints
"""
Get all wine references

Response Format: Array of global wine reference objects, each containing:
- id (str): Unique identifier for the wine reference
- name (str): Name of the wine
- type (str): Type of wine (e.g., 'Red', 'White', 'Rosé', 'Sparkling')
- vintage (int, optional): Year the wine was produced
- producer (str, optional): Name of the wine producer/winery
- varietals (list[str], optional): List of grape varietals used
- region (str, optional): Wine region
- country (str, optional): Country of origin
- labelImageUrl (str, optional): URL to the wine label image
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when reference was created
- updatedAt (str): ISO 8601 timestamp when reference was last updated
"""
@wine_references_bp.route('/wine-references', methods=['GET'])
def _get_wine_references():
    """Get all wine references"""
    references = get_all_wine_references()
    return jsonify([serialize_global_wine_reference(r) for r in references])


"""
Create a new wine reference

Expected POST Parameters:
- name (str, required): Name of the wine
- type (str, required): Type of wine (e.g., 'Red', 'White', 'Rosé', 'Sparkling')
- vintage (int, optional): Year the wine was produced
- producer (str, optional): Name of the wine producer/winery
- varietals (list[str], optional): List of grape varietals used in the wine
- region (str, optional): Wine region (e.g., 'Napa Valley', 'Bordeaux')
- country (str, optional): Country of origin
- labelImageUrl (str, optional): URL to the wine label image in blob storage
"""
@wine_references_bp.route('/wine-references', methods=['POST'])
def _create_wine_reference():
    """Create a new wine reference"""
    data = request.json

    # Validate required fields
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'name and type are required'}), 400

    # Create GlobalWineReference model object
    reference = GlobalWineReference(
        id=generate_id(),
        name=data.get('name'),
        type=data.get('type'),
        vintage=data.get('vintage'),
        producer=data.get('producer'),
        varietals=data.get('varietals', []),
        region=data.get('region'),
        country=data.get('country'),
        label_image_url=data.get('labelImageUrl')
    )

    # Check if reference already exists (name + vintage + producer)
    references = get_all_wine_references()
    existing = next((r for r in references if r.get_unique_key() == reference.get_unique_key()), None)

    if existing:
        return jsonify({'error': 'Wine reference already exists', 'reference': serialize_global_wine_reference(existing)}), 409

    # Add version and timestamps
    timestamp = get_current_timestamp()
    reference.version = 1
    reference.created_at = timestamp
    reference.updated_at = timestamp

    # Save to DynamoDB
    data = serialize_global_wine_reference(reference)
    dynamodb_put_wine_reference(data)
    return jsonify(data), 201

"""
Search Vivino for wines by name

Query Parameters:
- name (str, required): Wine name to search for

Response Format: Array of wine data from Vivino, each containing:
- name (str): Name of the wine
- type (str): Type of wine
- producer (str, optional): Name of the wine producer/winery
- region (str, optional): Wine region
- country (str, optional): Country of origin
- rating (float, optional): Vivino community rating
- labelImageUrl (str, optional): URL to the wine label image
"""
@wine_references_bp.route('/vivino/search', methods=['GET'])
def _search_vivino():
    """Search Vivino for wines by name"""
    name = request.args.get('name')

    if not name:
        return jsonify({'error': 'name parameter is required'}), 400

    # Get optional limit parameter (default 10, max 25)
    limit = min(int(request.args.get('limit', 10)), 25)

    # Search Vivino
    results = search_vivino(name, limit=limit)

    return jsonify(results), 200


"""
Get a specific wine reference with all instances

Response Format: Wine reference object containing all fields from GET /wine-references, plus:
- instances (array): Array of wine instance objects that reference this wine reference

Error Response (404): {'error': 'Wine reference not found'} if reference doesn't exist
"""
@wine_references_bp.route('/wine-references/<reference_id>/instances', methods=['GET'])
def _get_wine_reference_instances(reference_id: str):
    """Get a specific wine reference with all instances"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404

    # Get all instances for this reference
    from server.wine_instances import get_all_wine_instances
    instances = get_all_wine_instances()
    reference_instances = [serialize_wine_instance(i) for i in instances if i.reference.global_reference_id == reference_id]

    response = serialize_global_wine_reference(reference)
    response['instances'] = reference_instances

    return jsonify(response)

@wine_references_bp.route('/wine-references/<reference_id>', methods=['GET'])
def _get_wine_reference(reference_id: str):
    """Get a specific wine reference"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404
    return jsonify(serialize_global_wine_reference(reference))

"""
Update a wine reference

Expected PUT Parameters (all optional):
- name (str, optional): Updated name of the wine
- type (str, optional): Updated type of wine
- vintage (int, optional): Updated vintage year
- producer (str, optional): Updated producer name
- varietals (list[str], optional): Updated list of grape varietals
- region (str, optional): Updated wine region
- country (str, optional): Updated country of origin
- labelImageUrl (str, optional): Updated URL to label image
"""
@wine_references_bp.route('/wine-references/<reference_id>', methods=['PUT'])
def _update_wine_reference(reference_id: str):
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
    if 'labelImageUrl' in data:
        reference.label_image_url = data['labelImageUrl']

    # Update version and timestamp
    reference.version += 1
    reference.updated_at = get_current_timestamp()

    # Save to DynamoDB
    data = serialize_global_wine_reference(reference)
    dynamodb_put_wine_reference(data)
    return jsonify(data)

@wine_references_bp.route('/wine-references/<reference_id>', methods=['DELETE'])
def _delete_wine_reference(reference_id: str):
    """Delete a wine reference"""
    reference = find_wine_reference_by_id(reference_id)
    if not reference:
        return jsonify({'error': 'Wine reference not found'}), 404

    # Remove from DynamoDB
    dynamodb_delete_wine_reference(reference_id)
    return jsonify({'message': 'Wine reference deleted'}), 200
