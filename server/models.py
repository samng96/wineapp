"""Data models and type definitions for WineApp"""
from typing import List, Optional, Dict, Any, Tuple, TYPE_CHECKING, Callable
from dataclasses import dataclass, field
from server.utils import get_current_timestamp

if TYPE_CHECKING:
    # Forward references for type checking
    WineInstance = 'WineInstance'
    Cellar = 'Cellar'
    Shelf = 'Shelf'

@dataclass
class Shelf:
    """
    Represents a shelf in a cellar. Configuration (positions, is_double) is immutable after initialization.
    wine_positions is a 2D array: List[List[Optional[WineInstance]]]
    - For is_double=False: 1 row (single side)
    - For is_double=True: 2 rows (front=row 0, back=row 1)
    Each row has 'positions' columns.
    """
    positions: int  # Number of bottle positions per side (immutable)
    is_double: bool  # True if shelf has front/back, False if single-sided (immutable)
    wine_positions: List[List[Optional['WineInstance']]] = field(default_factory=list)  # 2D array: rows x positions (mutable)
    
    def __post_init__(self):
        """Initialize wine_positions if empty"""
        if not self.wine_positions:
            if self.is_double:
                # 2 rows (front and back), each with 'positions' columns
                self.wine_positions = [[None] * self.positions, [None] * self.positions]
            else:
                # 1 row (single), with 'positions' columns
                self.wine_positions = [[None] * self.positions]
        
        # Make positions and is_double immutable after initialization
        object.__setattr__(self, '_positions_frozen', True)
        object.__setattr__(self, '_is_double_frozen', True)
    
    def __setattr__(self, name, value):
        """Override to make positions and is_double immutable"""
        if hasattr(self, '_positions_frozen') and self._positions_frozen:
            if name == 'positions' or name == 'is_double':
                raise AttributeError(f"'{name}' is immutable after initialization")
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
        """Get wine instance object at position (returns object, not ID)"""
        if position < 0 or position >= self.positions:
            raise ValueError(f"Position {position} out of range [0, {self.positions})")
        
        row_index = self._get_row_index(side)
        return self.wine_positions[row_index][position]
    
    def set_wine_at(self, side: str, position: int, instance: Optional['WineInstance']):
        """Set wine instance object at position"""
        if position < 0 or position >= self.positions:
            raise ValueError(f"Position {position} out of range [0, {self.positions})")
        
        row_index = self._get_row_index(side)
        self.wine_positions[row_index][position] = instance


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
        """Calculate capacity if not provided"""
        if self.capacity is None:
            self.capacity = sum(shelf.positions * (2 if shelf.is_double else 1) for shelf in self.shelves)
    
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
        wine = shelf.get_wine_at(side, position)
        return wine is None
    
    def assign_wine_to_position(self, shelf_index: int, side: str, position: int, instance: 'WineInstance'):
        """Assign wine instance object to a position"""
        if not self.is_position_valid(shelf_index, side, position):
            raise ValueError(f"Invalid position: shelf_index={shelf_index}, side={side}, position={position}")
        if not self.is_position_available(shelf_index, side, position):
            raise ValueError(f"Position is not available: shelf_index={shelf_index}, side={side}, position={position}")
        
        shelf = self._get_shelf(shelf_index)
        shelf.set_wine_at(side, position, instance)
    
    def remove_wine_from_cellar(self, instance: 'WineInstance'):
        """Remove wine from a cellar"""
        for shelf in self.shelves:
            if shelf.is_double:
                sides = ['front', 'back']
            else:
                sides = ['single']
            for side in sides:
                for position in range(shelf.positions):
                    if shelf.get_wine_at(side, position) == instance:
                        shelf.set_wine_at(side, position, None)
                        return  # Wine instance found and removed, exit early

    def is_wine_instance_in_cellar(self, instance: 'WineInstance') -> bool: 
        """Check if a wine instance is in this cellar"""
        for shelf in self.shelves:
            if shelf.is_double:
                sides = ['front', 'back']
            else:
                sides = ['single']
            for side in sides:
                for position in range(shelf.positions):
                    if shelf.get_wine_at(side, position) == instance:
                        return True
        return False

@dataclass
class WineReference:
    """Represents a wine reference (singleton for each wine type)"""
    id: str
    name: str
    type: str  # Red, White, Rosé, Sparkling, etc.
    vintage: Optional[int] = None
    producer: Optional[str] = None
    varietals: Optional[List[str]] = None
    region: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[int] = None  # 1-5
    tasting_notes: Optional[str] = None
    label_image_url: Optional[str] = None  # URL to blob storage
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def get_unique_key(self) -> tuple:
        """Get unique key for deduplication (name, vintage, producer)"""
        return (self.name, self.vintage, self.producer)

@dataclass
class WineInstance:
    """Represents a wine instance (physical bottle)"""
    id: str
    reference: 'WineReference'  # WineReference object (not ID - loaded from global registry)
    price: Optional[float] = None
    purchase_date: Optional[str] = None  # ISO 8601 date
    drink_by_date: Optional[str] = None  # ISO 8601 date
    consumed: bool = False
    consumed_date: Optional[str] = None  # ISO 8601 timestamp
    coravined: bool = False
    coravined_date: Optional[str] = None  # ISO 8601 timestamp
    stored_date: Optional[str] = None  # ISO 8601 timestamp
    version: int = 1
    created_at: Optional[str] = None  # ISO 8601 timestamp
    updated_at: Optional[str] = None  # ISO 8601 timestamp

    def set_consumed(self):
        self.consumed = True
        self.consumed_date = get_current_timestamp()

    def set_coravined(self):
        self.coravined = True
        self.coravined_date = get_current_timestamp()