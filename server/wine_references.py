"""Wine reference management endpoints and helper functions"""
from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
from server.utils import generate_id, get_current_timestamp
from server.models import WineReference, register_wine_reference
from server.data.storage_serializers import serialize_wine_reference, deserialize_wine_reference, serialize_wine_instance
from server.dynamo.storage import (
    load_wine_references as dynamodb_load_wine_references,
    save_wine_references as dynamodb_save_wine_references,
    get_wine_reference_by_id as dynamodb_get_wine_reference_by_id,
    update_wine_reference as dynamodb_update_wine_reference,
    delete_wine_reference as dynamodb_delete_wine_reference
)

wine_references_bp = Blueprint('wine_references', __name__)


# Helper functions
def load_wine_references() -> List[WineReference]:
    """Load wine references from DynamoDB as WineReference model objects"""
    data = dynamodb_load_wine_references()
    return [deserialize_wine_reference(r) for r in data]


def save_wine_references(references: List[WineReference]):
    """Save wine references to DynamoDB (accepts WineReference model objects)"""
    data = [serialize_wine_reference(r) for r in references]
    dynamodb_save_wine_references(data)


def find_wine_reference_by_id(reference_id: str) -> Optional[WineReference]:
    """Find a wine reference by ID (returns WineReference model object)"""
    from server.models import get_wine_reference
    return get_wine_reference(reference_id)


# Endpoints
"""
Get all wine references

Response Format: Array of wine reference objects, each containing:
- id (str): Unique identifier for the wine reference
- name (str): Name of the wine
- type (str): Type of wine (e.g., 'Red', 'White', 'Rosé', 'Sparkling')
- vintage (int, optional): Year the wine was produced
- producer (str, optional): Name of the wine producer/winery
- varietals (list[str], optional): List of grape varietals used
- region (str, optional): Wine region
- country (str, optional): Country of origin
- rating (int, optional): Rating from 1-5
- tastingNotes (str, optional): Tasting notes or description
- labelImageUrl (str, optional): URL to the wine label image
- version (int): Version number for conflict resolution
- createdAt (str): ISO 8601 timestamp when reference was created
- updatedAt (str): ISO 8601 timestamp when reference was last updated
"""
@wine_references_bp.route('/wine-references', methods=['GET'])
def get_wine_references():
    """Get all wine references"""
    references = load_wine_references()
    return jsonify([serialize_wine_reference(r) for r in references])


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
- rating (int, optional): Rating from 1-5
- tastingNotes (str, optional): Tasting notes or description
- labelImageUrl (str, optional): URL to the wine label image in blob storage
"""
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
    
    # Save to DynamoDB
    references = load_wine_references()
    references.append(reference)
    save_wine_references(references)
    
    return jsonify(serialize_wine_reference(reference)), 201


"""
Get a specific wine reference with all instances

Response Format: Wine reference object containing all fields from GET /wine-references, plus:
- instances (array): Array of wine instance objects that reference this wine reference
  Each instance object contains:
  - id (str): Unique identifier for the wine instance
  - referenceId (str): ID of the wine reference this instance belongs to
  - location (dict, optional): Location object with cellarId, shelfIndex, position, isFront
  - price (float, optional): Purchase price
  - purchaseDate (str, optional): ISO 8601 date when purchased
  - drinkByDate (str, optional): ISO 8601 date for recommended consumption
  - consumed (bool): Whether the wine has been consumed
  - consumedDate (str, optional): ISO 8601 timestamp when consumed
  - storedDate (str, optional): ISO 8601 timestamp when stored
  - version (int): Version number for conflict resolution
  - createdAt (str): ISO 8601 timestamp when instance was created
  - updatedAt (str): ISO 8601 timestamp when instance was last updated

Error Response (404): {'error': 'Wine reference not found'} if reference doesn't exist
"""
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
- rating (int, optional): Updated rating (1-5)
- tastingNotes (str, optional): Updated tasting notes
- labelImageUrl (str, optional): Updated URL to label image
"""
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
    
    # Save to DynamoDB
    data = serialize_wine_reference(reference)
    dynamodb_update_wine_reference(data)
    
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
    
    # Remove from DynamoDB
    dynamodb_delete_wine_reference(reference_id)
    
    return jsonify({'message': 'Wine reference deleted'}), 200
