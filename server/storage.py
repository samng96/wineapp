"""Storage abstraction layer for serialization/deserialization of data models"""
from typing import List, Optional, Dict, Any
from server.models import (
    Shelf, Cellar, WineReference, WineInstance,
    get_wine_reference, register_wine_reference
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
                                  wine_instances: Optional[Dict[str, WineInstance]] = None) -> Shelf:
    """
    Create Shelf from tuple format [Positions, IsDouble]
    wine_positions_ids: Dict with instance IDs (from JSON)
    wine_instances: Dict mapping instance IDs to WineInstance objects (for resolving IDs)
    """
    if not isinstance(shelf_data, list) or len(shelf_data) != 2:
        raise ValueError("Shelf must be a list of [Positions, IsDouble]")
    if not isinstance(shelf_data[0], int) or shelf_data[0] <= 0:
        raise ValueError("Positions must be a positive integer")
    if not isinstance(shelf_data[1], bool):
        raise ValueError("IsDouble must be a boolean")
    
    positions = shelf_data[0]
    is_double = shelf_data[1]
    
    # Initialize empty wine_positions
    if is_double:
        wine_positions = [[None] * positions, [None] * positions]
    else:
        wine_positions = [[None] * positions]
    
    # Populate with WineInstance objects if provided
    if wine_positions_ids and wine_instances:
        if is_double:
            if 'front' in wine_positions_ids:
                wine_positions[0] = [wine_instances.get(id) if id else None for id in wine_positions_ids['front']]
            if 'back' in wine_positions_ids:
                wine_positions[1] = [wine_instances.get(id) if id else None for id in wine_positions_ids['back']]
        else:
            if 'single' in wine_positions_ids:
                wine_positions[0] = [wine_instances.get(id) if id else None for id in wine_positions_ids['single']]
    
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


def deserialize_cellar(data: Dict[str, Any], wine_instances: Optional[Dict[str, WineInstance]] = None) -> Cellar:
    """
    Create Cellar from dictionary
    wine_instances: Optional dict mapping instance IDs to WineInstance objects for resolving IDs
    """
    shelves_data = data.get('shelves', [])
    wine_positions_data = data.get('winePositions', {})
    
    # Create shelves with their wine positions
    shelves = []
    for i, shelf_tuple in enumerate(shelves_data):
        shelf_key = str(i)
        wine_positions_ids = wine_positions_data.get(shelf_key, {})
        shelves.append(deserialize_shelf_from_tuple(shelf_tuple, wine_positions_ids, wine_instances))
    
    cellar = Cellar(
        id=data['id'],
        name=data['name'],
        shelves=shelves,
        temperature=data.get('temperature'),
        capacity=data.get('capacity'),  # Will be calculated in __post_init__ if None
        version=data.get('version', 1),
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
    reference = WineReference(
        id=data['id'],
        name=data['name'],
        type=data['type'],
        vintage=data.get('vintage'),
        producer=data.get('producer'),
        varietals=data.get('varietals'),
        region=data.get('region'),
        country=data.get('country'),
        rating=data.get('rating'),
        tasting_notes=data.get('tastingNotes'),
        label_image_url=data.get('labelImageUrl'),
        version=data.get('version', 1),
        created_at=data.get('createdAt'),
        updated_at=data.get('updatedAt')
    )
    # Auto-register in global registry
    register_wine_reference(reference)
    return reference


# WineInstance serialization
def serialize_wine_instance(instance: WineInstance) -> Dict[str, Any]:
    """Serialize WineInstance to dictionary format for JSON (extracts IDs from objects)"""
    # Serialize location
    location_dict = None
    if instance.location is not None:
        cellar, shelf, position, is_front = instance.location
        # Find shelf index in cellar
        shelf_index = None
        for i, s in enumerate(cellar.shelves):
            if s is shelf:
                shelf_index = i
                break
        if shelf_index is None:
            raise ValueError(f"Shelf not found in cellar {cellar.id}")
        
        location_dict = {
            'cellarId': cellar.id,  # Extract ID from Cellar object
            'shelfIndex': shelf_index,
            'position': position,
            'isFront': is_front
        }
    
    return {
        'id': instance.id,
        'referenceId': instance.reference.id,  # Extract ID from WineReference object
        'location': location_dict,
        'price': instance.price,
        'purchaseDate': instance.purchase_date,
        'drinkByDate': instance.drink_by_date,
        'consumed': instance.consumed,
        'consumedDate': instance.consumed_date,
        'storedDate': instance.stored_date,
        'version': instance.version,
        'createdAt': instance.created_at,
        'updatedAt': instance.updated_at
    }


def deserialize_wine_instance(data: Dict[str, Any], cellars: Optional[List[Cellar]] = None) -> WineInstance:
    """
    Create WineInstance from dictionary, looking up WineReference from global registry
    cellars: Optional list of Cellar objects for resolving location (if None, location will be None)
    """
    reference_id = data['referenceId']
    reference = get_wine_reference(reference_id)
    if not reference:
        raise ValueError(f"WineReference with ID '{reference_id}' not found in registry")
    
    # Deserialize location
    location = None
    location_data = data.get('location')
    if location_data and cellars:
        cellar_id = location_data.get('cellarId')
        shelf_index = location_data.get('shelfIndex')
        position = location_data.get('position')
        is_front = location_data.get('isFront')
        
        if cellar_id is not None and shelf_index is not None and position is not None and is_front is not None:
            # Find cellar
            cellar = next((c for c in cellars if c.id == cellar_id), None)
            if not cellar:
                return None
            
            # Get shelf
            if shelf_index < 0 or shelf_index >= len(cellar.shelves):
                raise ValueError(f"Shelf index {shelf_index} out of range for cellar {cellar_id}")
            shelf = cellar.shelves[shelf_index]
            
            location = (cellar, shelf, position, is_front)
    
    return WineInstance(
        id=data['id'],
        reference=reference,  # Store WineReference object
        location=location,
        price=data.get('price'),
        purchase_date=data.get('purchaseDate'),
        drink_by_date=data.get('drinkByDate'),
        consumed=data.get('consumed', False),
        consumed_date=data.get('consumedDate'),
        stored_date=data.get('storedDate'),
        version=data.get('version', 1),
        created_at=data.get('createdAt'),
        updated_at=data.get('updatedAt')
    )
