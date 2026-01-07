"""Data models and type definitions for WineApp"""
from typing import List, Optional, Dict, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

if TYPE_CHECKING:
    from typing import TYPE_CHECKING
    # Forward reference for WineInstance
    WineInstance = 'WineInstance'

# Global registry for WineReferences (keyed by ID)
_wine_references_registry: Dict[str, 'WineReference'] = {}

def get_wine_reference(reference_id: str) -> Optional['WineReference']:
    """Get a WineReference from the global registry by ID"""
    return _wine_references_registry.get(reference_id)

def register_wine_reference(reference: 'WineReference'):
    """Register a WineReference in the global registry"""
    _wine_references_registry[reference.id] = reference

def clear_wine_references_registry():
    """Clear the global WineReference registry (mainly for testing)"""
    global _wine_references_registry
    _wine_references_registry.clear()


@dataclass
class Shelf:
    """
    Represents a shelf in a cellar. Configuration (positions, is_double) is immutable after initialization.
    wine_positions is a 2D array: List[List[Optional[WineInstance]]]
    - For is_double=False: 1 row (single side)
    - For is_double=True: 2 rows (front=row 0, back=row 1)
    Each row has 'positions' columns.
    """
    positions: int  # Number of bottle positions per side
    is_double: bool  # True if shelf has front/back, False if single-sided
    wine_positions: List[List[Optional['WineInstance']]] = field(default_factory=list)  # 2D array: rows x positions
    
    def __post_init__(self):
        """Initialize wine_positions if empty"""
        if not self.wine_positions:
            if self.is_double:
                # 2 rows (front and back), each with 'positions' columns
                self.wine_positions = [[None] * self.positions, [None] * self.positions]
            else:
                # 1 row (single), with 'positions' columns
                self.wine_positions = [[None] * self.positions]
    
    def __setattr__(self, name, value):
        """Prevent modification of positions and is_double after initialization"""
        if name in ('positions', 'is_double') and hasattr(self, name):
            raise AttributeError(f"'{self.__class__.__name__}.{name}' is immutable and cannot be modified after initialization")
        super().__setattr__(name, value)
    
    def _get_row_index(self, side: str) -> int:
        """Convert side string to row index (private method)"""
        if self.is_double:
            if side == 'front':
                return 0
            elif side == 'back':
                return 1
            else:
                raise ValueError(f"Invalid side '{side}' for double shelf. Must be 'front' or 'back'")
        else:
            if side == 'single':
                return 0
            else:
                raise ValueError(f"Invalid side '{side}' for single shelf. Must be 'single'")
    
    def get_wine_at(self, side: str, position: int) -> Optional['WineInstance']:
        """Get wine instance at a specific side and position"""
        row = self._get_row_index(side)
        if 0 <= position < self.positions:
            return self.wine_positions[row][position]
        return None
    
    def set_wine_at(self, side: str, position: int, instance: Optional['WineInstance']):
        """Set wine instance at the specified position (mutates wine_positions)"""
        row = self._get_row_index(side)
        if position < 0 or position >= self.positions:
            raise ValueError(f"Position {position} out of range [0, {self.positions})")
        
        self.wine_positions[row][position] = instance
    
    """Used for serialization to/from JSON"""
    def to_tuple(self) -> tuple:
        """Convert to tuple format [Positions, IsDouble]"""
        return [self.positions, self.is_double]
    
    def get_wine_positions_dict(self) -> Dict[str, List[Optional[str]]]:
        """Get wine positions as dictionary with instance IDs (for JSON serialization)"""
        result = {}
        if self.is_double:
            result['front'] = [inst.id if inst else None for inst in self.wine_positions[0]]
            result['back'] = [inst.id if inst else None for inst in self.wine_positions[1]]
        else:
            result['single'] = [inst.id if inst else None for inst in self.wine_positions[0]]
        return result
    
    @classmethod
    def from_tuple(cls, shelf_data: List, wine_positions_ids: Optional[Dict[str, List[Optional[str]]]] = None, 
                   wine_instances: Optional[Dict[str, 'WineInstance']] = None) -> 'Shelf':
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
        
        return cls(positions=positions, is_double=is_double, wine_positions=wine_positions)


@dataclass
class Cellar:
    """Represents a wine cellar"""
    id: str
    name: str
    shelves: List[Shelf]
    temperature: Optional[int] = None
    capacity: Optional[int] = None
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        # We assume capacity is never provided, so we need to calculate it here.
        self.capacity = sum(shelf.positions * (2 if shelf.is_double else 1) for shelf in self.shelves)
    
    """Used for serialization to/from JSON"""
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization"""
        # Build winePositions dict from shelves
        wine_positions = {}
        for i, shelf in enumerate(self.shelves):
            wine_positions[str(i)] = shelf.get_wine_positions_dict()
        
        return {
            'id': self.id,
            'name': self.name,
            'temperature': self.temperature,
            'capacity': self.capacity,
            'shelves': [shelf.to_tuple() for shelf in self.shelves],
            'winePositions': wine_positions,
            'version': self.version,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], wine_instances: Optional[Dict[str, 'WineInstance']] = None) -> 'Cellar':
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
            shelves.append(Shelf.from_tuple(shelf_tuple, wine_positions_ids, wine_instances))
        
        cellar = cls(
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
    
    def _get_shelf(self, shelf_index: int) -> Optional[Shelf]:
        """Get shelf by index (private method)"""
        if 0 <= shelf_index < len(self.shelves):
            return self.shelves[shelf_index]
        return None
    
    def is_position_valid(self, shelf_index: int, side: str, position: int) -> bool:
        """Check if a position is valid for this cellar"""
        shelf = self._get_shelf(shelf_index)
        if not shelf:
            return False
        
        if shelf.is_double:
            if side not in ['front', 'back']:
                return False
        else:
            if side != 'single':
                return False
        
        if position < 0 or position >= shelf.positions:
            return False
        
        return True
    
    def is_position_available(self, shelf_index: int, side: str, position: int) -> bool:
        """Check if a position is available (not occupied)"""
        if not self.is_position_valid(shelf_index, side, position):
            return False
        
        shelf = self._get_shelf(shelf_index)
        if not shelf:
            return True
        
        instance = shelf.get_wine_at(side, position)
        return instance is None
    
    def assign_wine_to_position(self, shelf_index: int, side: str, position: int, instance: 'WineInstance'):
        """Assign a wine instance to a position"""
        if not self.is_position_valid(shelf_index, side, position):
            raise ValueError(f"Invalid position: shelf {shelf_index}, side {side}, position {position}")
        
        shelf = self._get_shelf(shelf_index)
        if not shelf:
            raise ValueError(f"Shelf {shelf_index} not found")
        
        # Directly mutate the shelf's wine_positions
        shelf.set_wine_at(side, position, instance)
    
    def remove_wine_from_position(self, shelf_index: int, side: str, position: int):
        """Remove a wine instance from a position"""
        shelf = self._get_shelf(shelf_index)
        if not shelf:
            raise ValueError(f"Shelf {shelf_index} not found")

        if not self.is_position_valid(shelf_index, side, position):
            raise ValueError(f"Invalid position: shelf {shelf_index}, side {side}, position {position}")
        
        # Directly mutate the shelf's wine_positions
        shelf.set_wine_at(side, position, None)


@dataclass
class WineReference:
    """Represents a wine reference (singleton pattern)"""
    id: str
    name: str
    type: str  # Red, White, Rosé, Sparkling
    vintage: int
    producer: Optional[str] = None
    varietals: List[str] = field(default_factory=list)
    region: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[int] = None  # 1-5 stars
    tasting_notes: Optional[str] = None
    label_image_url: Optional[str] = None
    instance_count: int = 0
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'vintage': self.vintage,
            'producer': self.producer,
            'varietals': self.varietals,
            'region': self.region,
            'country': self.country,
            'rating': self.rating,
            'tastingNotes': self.tasting_notes,
            'labelImageUrl': self.label_image_url,
            'instanceCount': self.instance_count,
            'version': self.version,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WineReference':
        """Create WineReference from dictionary and register it in the global registry"""
        reference = cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            vintage=data['vintage'],
            producer=data.get('producer'),
            varietals=data.get('varietals', []),
            region=data.get('region'),
            country=data.get('country'),
            rating=data.get('rating'),
            tasting_notes=data.get('tastingNotes'),
            label_image_url=data.get('labelImageUrl'),
            instance_count=data.get('instanceCount', 0),
            version=data.get('version', 1),
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt')
        )
        # Register in global registry
        register_wine_reference(reference)
        return reference
    
    def get_unique_key(self) -> tuple:
        """Get unique key for duplicate detection (name, vintage, producer)"""
        return (self.name, self.vintage, self.producer)


@dataclass
class WineInstance:
    """Represents a wine instance (physical bottle)"""
    id: str
    reference: 'WineReference'  # WineReference object (not ID)
    location: Optional[Tuple['Cellar', 'Shelf', int, bool]] = None  # (Cellar, Shelf, Position, IsFront) or None for unshelved
    price: Optional[float] = None
    purchase_date: Optional[str] = None
    drink_by_date: Optional[str] = None
    consumed: bool = False
    consumed_date: Optional[str] = None
    stored_date: Optional[str] = None
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization"""
        # Serialize location
        location_dict = None
        if self.location is not None:
            cellar, shelf, position, is_front = self.location
            # Find shelf index in cellar
            shelf_index = None
            for i, s in enumerate(cellar.shelves):
                if s is shelf:
                    shelf_index = i
                    break
            if shelf_index is None:
                raise ValueError(f"Shelf not found in cellar {cellar.id}")
            
            location_dict = {
                'cellarId': cellar.id,
                'shelfIndex': shelf_index,
                'position': position,
                'isFront': is_front
            }
        
        return {
            'id': self.id,
            'referenceId': self.reference.id,  # Get ID from WineReference object
            'location': location_dict,
            'price': self.price,
            'purchaseDate': self.purchase_date,
            'drinkByDate': self.drink_by_date,
            'consumed': self.consumed,
            'consumedDate': self.consumed_date,
            'storedDate': self.stored_date,
            'version': self.version,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], cellars: Optional[List['Cellar']] = None) -> 'WineInstance':
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
                    raise ValueError(f"Cellar with ID '{cellar_id}' not found")
                
                # Get shelf
                if shelf_index < 0 or shelf_index >= len(cellar.shelves):
                    raise ValueError(f"Shelf index {shelf_index} out of range for cellar {cellar_id}")
                shelf = cellar.shelves[shelf_index]
                
                location = (cellar, shelf, position, is_front)
        
        return cls(
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
    
    def _is_in_cellar(self) -> bool:
        """Check if instance is in a cellar (internal method)"""
        return self.location is not None
    
    def _is_unshelved(self) -> bool:
        """Check if instance is unshelved (internal method)"""
        return self.location is None
    
    def get_cellar_location(self) -> Optional[Dict[str, Any]]:
        """Get cellar location details if in a cellar"""
        if self.location is not None:
            cellar, shelf, position, is_front = self.location
            # Find shelf index
            shelf_index = None
            for i, s in enumerate(cellar.shelves):
                if s is shelf:
                    shelf_index = i
                    break
            
            if shelf_index is not None:
                # Convert is_front to side string
                if shelf.is_double:
                    side = 'front' if is_front else 'back'
                else:
                    side = 'single'
                
                return {
                    'cellarId': cellar.id,
                    'shelfIndex': shelf_index,
                    'side': side,
                    'position': position
                }
        return None
