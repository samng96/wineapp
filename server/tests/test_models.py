"""Tests for data models"""
import pytest
from server.models import Shelf, Cellar, WineReference, WineInstance, register_wine_reference, clear_wine_references_registry


def test_shelf_initialization():
    """Test Shelf initialization"""
    shelf = Shelf(positions=10, is_double=False)
    assert shelf.positions == 10
    assert shelf.is_double is False
    assert len(shelf.wine_positions) == 1  # Single row
    assert len(shelf.wine_positions[0]) == 10


def test_shelf_double_initialization():
    """Test Shelf initialization for double-sided shelf"""
    shelf = Shelf(positions=12, is_double=True)
    assert shelf.positions == 12
    assert shelf.is_double is True
    assert len(shelf.wine_positions) == 2  # Front and back
    assert len(shelf.wine_positions[0]) == 12
    assert len(shelf.wine_positions[1]) == 12


def test_shelf_immutable_dimensions():
    """Test that shelf dimensions are immutable"""
    shelf = Shelf(positions=10, is_double=False)
    
    # Try to change positions (should raise AttributeError)
    with pytest.raises(AttributeError):
        shelf.positions = 20
    
    # Try to change is_double (should raise AttributeError)
    with pytest.raises(AttributeError):
        shelf.is_double = True


def test_shelf_get_wine_at():
    """Test getting wine at a position"""
    shelf = Shelf(positions=5, is_double=False)
    assert shelf.get_wine_at('single', 0) is None
    
    # Set a wine instance
    from server.models import WineInstance, WineReference
    clear_wine_references_registry()
    ref = WineReference(id='ref1', name='Test Wine', type='Red')
    register_wine_reference(ref)
    instance = WineInstance(id='inst1', reference=ref)
    
    shelf.set_wine_at('single', 0, instance)
    assert shelf.get_wine_at('single', 0) == instance


def test_cellar_capacity_calculation():
    """Test that cellar capacity is calculated correctly"""
    shelves = [
        Shelf(positions=10, is_double=False),  # 10 positions
        Shelf(positions=12, is_double=True),   # 24 positions (12 * 2)
        Shelf(positions=8, is_double=False)     # 8 positions
    ]
    cellar = Cellar(id='cellar1', name='Test Cellar', shelves=shelves)
    assert cellar.capacity == 10 + 24 + 8  # 42 total positions


def test_wine_reference_get_unique_key():
    """Test WineReference unique key generation"""
    ref1 = WineReference(id='ref1', name='Wine', type='Red', vintage=2018, producer='Winery')
    ref2 = WineReference(id='ref2', name='Wine', type='Red', vintage=2018, producer='Winery')
    ref3 = WineReference(id='ref3', name='Wine', type='Red', vintage=2019, producer='Winery')
    
    assert ref1.get_unique_key() == ref2.get_unique_key()
    assert ref1.get_unique_key() != ref3.get_unique_key()


def test_wine_reference_registry():
    """Test WineReference global registry"""
    clear_wine_references_registry()
    
    ref = WineReference(id='ref1', name='Test Wine', type='Red')
    register_wine_reference(ref)
    
    from server.models import get_wine_reference
    retrieved = get_wine_reference('ref1')
    assert retrieved == ref
    assert retrieved.id == 'ref1'


def test_wine_instance_location():
    """Test WineInstance location tuple"""
    clear_wine_references_registry()
    
    ref = WineReference(id='ref1', name='Test Wine', type='Red')
    register_wine_reference(ref)
    
    cellar = Cellar(id='cellar1', name='Test Cellar', shelves=[Shelf(positions=10, is_double=False)])
    shelf = cellar.shelves[0]
    
    instance = WineInstance(
        id='inst1',
        reference=ref,
        location=(cellar, shelf, 5, True)
    )
    
    assert instance.location is not None
    cellar_obj, shelf_obj, position, is_front = instance.location
    assert cellar_obj.id == 'cellar1'
    assert position == 5
    assert is_front is True


def test_wine_instance_unshelved():
    """Test WineInstance with no location (unshelved)"""
    clear_wine_references_registry()
    
    ref = WineReference(id='ref1', name='Test Wine', type='Red')
    register_wine_reference(ref)
    
    instance = WineInstance(id='inst1', reference=ref, location=None)
    assert instance.location is None
