"""Storage abstraction layer for serialization/deserialization of data models"""
from typing import List, Optional, Dict, Any
from server.models import (
    Shelf, Cellar, WineReference, WineInstance,
)


# Shelf serialization helpers
def serialize_shelf_to_tuple(shelf: Shelf) -> List:
    """Serialize Shelf to [positions, is_double] format"""
    return [shelf.positions, shelf.is_double]


def serialize_shelf_wine_positions(shelf: Shelf) -> Dict[str, List[Optional[str]]]:
    """Get wine positions as IDs for JSON serialization (extracts IDs from objects)"""
    result = {}
    if shelf.is_double:
        result['front'] = [inst.id if inst else None for inst in shelf.wine_positions[0]]
        result['back'] = [inst.id if inst else None for inst in shelf.wine_positions[1]]
    else:
        result['single'] = [inst.id if inst else None for inst in shelf.wine_positions[0]]
    return result


def deserialize_shelf_from_tuple(shelf_data: List, wine_positions_ids: Optional[Dict[str, List[Optional[str]]]] = None, 
                                  wine_instances_dict: Optional[Dict[str, WineInstance]] = None) -> Shelf:
    """
    Create Shelf from tuple format [Positions, IsDouble]
    wine_positions_ids: Dict with instance IDs (from JSON)
    wine_instances: Dict mapping instance IDs to WineInstance objects (for resolving IDs)
    """
    if not isinstance(shelf_data, list) or len(shelf_data) != 2:
        raise ValueError("Shelf must be a list of [Positions, IsDouble]")
    
    # Handle Decimal from DynamoDB - convert to int
    from decimal import Decimal
    positions_val = shelf_data[0]
    if isinstance(positions_val, Decimal):
        positions = int(positions_val)
    elif isinstance(positions_val, int):
        positions = positions_val
    else:
        raise ValueError("Positions must be a positive integer")
    
    if positions <= 0:
        raise ValueError("Positions must be a positive integer")
    if not isinstance(shelf_data[1], bool):
        raise ValueError("IsDouble must be a boolean")
    
    is_double = shelf_data[1]
    
    # Initialize empty wine_positions
    if is_double:
        wine_positions = [[None] * positions, [None] * positions]
    else:
        wine_positions = [[None] * positions]
    
    # Populate with WineInstance objects if provided
    if wine_positions_ids and wine_instances_dict:
        if is_double:
            if 'front' in wine_positions_ids:
                wine_positions[0] = [wine_instances_dict.get(id) if id else None for id in wine_positions_ids['front']]
            if 'back' in wine_positions_ids:
                wine_positions[1] = [wine_instances_dict.get(id) if id else None for id in wine_positions_ids['back']]
        else:
            if 'single' in wine_positions_ids:
                wine_positions[0] = [wine_instances_dict.get(id) if id else None for id in wine_positions_ids['single']]
    
    return Shelf(positions=positions, is_double=is_double, wine_positions=wine_positions)


# Cellar serialization
def serialize_cellar(cellar: Cellar) -> Dict[str, Any]:
    """Serialize Cellar to dictionary format for JSON (extracts IDs from objects when needed)"""
    # Build winePositions dict from shelves
    wine_positions = {}
    for i, shelf in enumerate(cellar.shelves):
        wine_positions[str(i)] = serialize_shelf_wine_positions(shelf)
    
    return {
        'id': cellar.id,
        'name': cellar.name,
        'temperature': cellar.temperature,
        'capacity': cellar.capacity,
        'shelves': [serialize_shelf_to_tuple(shelf) for shelf in cellar.shelves],
        'winePositions': wine_positions,
        'version': cellar.version,
        'createdAt': cellar.created_at,
        'updatedAt': cellar.updated_at
    }


def deserialize_cellar(data: Dict[str, Any], wine_instances: List[WineInstance]) -> Cellar:
    """
    Create Cellar from dictionary
    wine_instances: List of WineInstance objects
    """
    shelves_data = data.get('shelves', [])
    wine_positions_data = data.get('winePositions', {})
    wine_instances_dict = {inst.id: inst for inst in wine_instances}
    
    # Create shelves with their wine positions
    shelves = []
    for i, shelf_tuple in enumerate(shelves_data):
        shelf_key = str(i)
        wine_positions_ids = wine_positions_data.get(shelf_key, {})
        shelves.append(deserialize_shelf_from_tuple(shelf_tuple, wine_positions_ids, wine_instances_dict))
    
    # Handle Decimal from DynamoDB for version and capacity
    from decimal import Decimal
    version_val = data.get('version', 1)
    version = int(version_val) if isinstance(version_val, Decimal) else version_val
    
    capacity_val = data.get('capacity')
    capacity = int(capacity_val) if capacity_val is not None and isinstance(capacity_val, Decimal) else capacity_val
    
    cellar = Cellar(
        id=data['id'],
        name=data['name'],
        shelves=shelves,
        temperature=data.get('temperature'),
        capacity=capacity,  # Will be calculated in __post_init__ if None
        version=version,
        created_at=data.get('createdAt'),
        updated_at=data.get('updatedAt')
    )
    return cellar


# WineReference serialization
def serialize_wine_reference(reference: WineReference) -> Dict[str, Any]:
    """Serialize WineReference to dictionary format for JSON (includes id field from object)"""
    return {
        'id': reference.id,
        'name': reference.name,
        'type': reference.type,
        'vintage': reference.vintage,
        'producer': reference.producer,
        'varietals': reference.varietals,
        'region': reference.region,
        'country': reference.country,
        'rating': reference.rating,
        'tastingNotes': reference.tasting_notes,
        'labelImageUrl': reference.label_image_url,
        'version': reference.version,
        'createdAt': reference.created_at,
        'updatedAt': reference.updated_at
    }


def deserialize_wine_reference(data: Dict[str, Any]) -> WineReference:
    """Create WineReference from dictionary and auto-register in global registry"""
    # Handle Decimal from DynamoDB for version, vintage, rating
    from decimal import Decimal
    version_val = data.get('version', 1)
    version = int(version_val) if isinstance(version_val, Decimal) else version_val
    
    vintage_val = data.get('vintage')
    vintage = int(vintage_val) if vintage_val is not None and isinstance(vintage_val, Decimal) else vintage_val
    
    rating_val = data.get('rating')
    rating = int(rating_val) if rating_val is not None and isinstance(rating_val, Decimal) else rating_val
    
    reference = WineReference(
        id=data['id'],
        name=data['name'],
        type=data['type'],
        vintage=vintage,
        producer=data.get('producer'),
        varietals=data.get('varietals'),
        region=data.get('region'),
        country=data.get('country'),
        rating=rating,
        tasting_notes=data.get('tastingNotes'),
        label_image_url=data.get('labelImageUrl'),
        version=version,
        created_at=data.get('createdAt'),
        updated_at=data.get('updatedAt')
    )
    return reference


# WineInstance serialization
def serialize_wine_instance(instance: WineInstance) -> Dict[str, Any]:
    """Serialize WineInstance to dictionary format for JSON (extracts IDs from objects)"""
    return {
        'id': instance.id,
        'referenceId': instance.reference.id,  # Extract ID from WineReference object
        'price': instance.price,
        'purchaseDate': instance.purchase_date,
        'drinkByDate': instance.drink_by_date,
        'consumed': instance.consumed,
        'consumedDate': instance.consumed_date,
        'coravined': instance.coravined,
        'coravinedDate': instance.coravined_date,
        'storedDate': instance.stored_date,
        'version': instance.version,
        'createdAt': instance.created_at,
        'updatedAt': instance.updated_at
    }


def deserialize_wine_instance(data: Dict[str, Any], reference: WineReference) -> WineInstance:
    """
    Create WineInstance from dictionary, looking up WineReference from global registry
    """
    assert reference is not None
    
    # Handle Decimal from DynamoDB for version
    from decimal import Decimal
    version_val = data.get('version', 1)
    version = int(version_val) if isinstance(version_val, Decimal) else version_val
    
    instance = WineInstance(
        id=data['id'],
        reference=reference,  # Store WineReference object
        price=data.get('price'),
        purchase_date=data.get('purchaseDate'),
        drink_by_date=data.get('drinkByDate'),
        consumed=data.get('consumed', False),
        consumed_date=data.get('consumedDate'),
        coravined=data.get('coravined', False),
        coravined_date=data.get('coravinedDate'),
        stored_date=data.get('storedDate'),
        version=version,
        created_at=data.get('createdAt'),
        updated_at=data.get('updatedAt'))

    return instance
