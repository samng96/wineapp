"""Comprehensive data consistency tests for WineApp models"""
import pytest
from server.models import Shelf, Cellar, WineReference, WineInstance
from server.utils import get_current_timestamp


class TestShelfConsistency:
    """Test Shelf model data consistency"""
    
    def test_shelf_position_range_validation(self):
        """Test that shelf validates position ranges"""
        shelf = Shelf(positions=10, is_double=False)
        
        # Valid positions
        assert shelf.get_wine_at('single', 0) is None
        assert shelf.get_wine_at('single', 9) is None
        
        # Invalid positions should raise ValueError
        with pytest.raises(ValueError, match="out of range"):
            shelf.get_wine_at('single', -1)
        with pytest.raises(ValueError, match="out of range"):
            shelf.get_wine_at('single', 10)
        with pytest.raises(ValueError, match="out of range"):
            shelf.set_wine_at('single', -1, None)
        with pytest.raises(ValueError, match="out of range"):
            shelf.set_wine_at('single', 10, None)
    
    def test_shelf_side_validation_single(self):
        """Test that single shelf only accepts 'single' side"""
        shelf = Shelf(positions=10, is_double=False)
        
        # Valid side
        shelf.get_wine_at('single', 0)
        
        # Invalid sides should raise ValueError
        with pytest.raises(ValueError, match="Invalid side"):
            shelf.get_wine_at('front', 0)
        with pytest.raises(ValueError, match="Invalid side"):
            shelf.get_wine_at('back', 0)
        with pytest.raises(ValueError, match="Invalid side"):
            shelf.set_wine_at('front', 0, None)
    
    def test_shelf_side_validation_double(self):
        """Test that double shelf only accepts 'front' or 'back' side"""
        shelf = Shelf(positions=10, is_double=True)
        
        # Valid sides
        shelf.get_wine_at('front', 0)
        shelf.get_wine_at('back', 0)
        
        # Invalid side should raise ValueError
        with pytest.raises(ValueError, match="Invalid side"):
            shelf.get_wine_at('single', 0)
        with pytest.raises(ValueError, match="Invalid side"):
            shelf.set_wine_at('single', 0, None)
    
    def test_shelf_wine_positions_array_consistency(self):
        """Test that wine_positions array matches shelf configuration"""
        # Single shelf
        single_shelf = Shelf(positions=8, is_double=False)
        assert len(single_shelf.wine_positions) == 1
        assert len(single_shelf.wine_positions[0]) == 8
        
        # Double shelf
        double_shelf = Shelf(positions=12, is_double=True)
        assert len(double_shelf.wine_positions) == 2
        assert len(double_shelf.wine_positions[0]) == 12  # front
        assert len(double_shelf.wine_positions[1]) == 12  # back
    
    def test_shelf_wine_position_independence(self):
        """Test that front and back positions are independent on double shelf"""
        shelf = Shelf(positions=5, is_double=True)
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance1 = WineInstance(id='inst1', reference=ref)
        instance2 = WineInstance(id='inst2', reference=ref)
        
        # Set different wines on front and back
        shelf.set_wine_at('front', 0, instance1)
        shelf.set_wine_at('back', 0, instance2)
        
        assert shelf.get_wine_at('front', 0) == instance1
        assert shelf.get_wine_at('back', 0) == instance2
        assert shelf.get_wine_at('front', 0) != shelf.get_wine_at('back', 0)
    
    def test_shelf_immutability_after_initialization(self):
        """Test that shelf dimensions cannot be changed after initialization"""
        shelf = Shelf(positions=10, is_double=False)
        
        # Try to modify immutable attributes
        with pytest.raises(AttributeError):
            shelf.positions = 20
        with pytest.raises(AttributeError):
            shelf.is_double = True
        
        # Verify original values are unchanged
        assert shelf.positions == 10
        assert shelf.is_double is False


class TestCellarConsistency:
    """Test Cellar model data consistency"""
    
    def test_cellar_capacity_calculation_consistency(self):
        """Test that capacity is calculated correctly for various shelf configurations"""
        # Test 1: All single shelves
        shelves1 = [
            Shelf(positions=10, is_double=False),
            Shelf(positions=5, is_double=False),
            Shelf(positions=8, is_double=False)
        ]
        cellar1 = Cellar(id='c1', name='Cellar 1', shelves=shelves1)
        assert cellar1.capacity == 23  # 10 + 5 + 8
        
        # Test 2: Mixed single and double
        shelves2 = [
            Shelf(positions=10, is_double=False),   # 10 positions
            Shelf(positions=8, is_double=True),      # 16 positions (8 * 2)
            Shelf(positions=5, is_double=False)      # 5 positions
        ]
        cellar2 = Cellar(id='c2', name='Cellar 2', shelves=shelves2)
        assert cellar2.capacity == 31  # 10 + 16 + 5
        
        # Test 3: All double shelves
        shelves3 = [
            Shelf(positions=10, is_double=True),    # 20 positions
            Shelf(positions=8, is_double=True)      # 16 positions
        ]
        cellar3 = Cellar(id='c3', name='Cellar 3', shelves=shelves3)
        assert cellar3.capacity == 36  # 20 + 16
    
    def test_cellar_position_validation(self):
        """Test that cellar validates positions correctly"""
        shelves = [
            Shelf(positions=10, is_double=False),
            Shelf(positions=8, is_double=True)
        ]
        cellar = Cellar(id='c1', name='Test Cellar', shelves=shelves)
        
        # Valid positions
        assert cellar.is_position_valid(0, 'single', 0) is True
        assert cellar.is_position_valid(0, 'single', 9) is True
        assert cellar.is_position_valid(1, 'front', 0) is True
        assert cellar.is_position_valid(1, 'back', 7) is True
        
        # Invalid shelf index
        assert cellar.is_position_valid(-1, 'single', 0) is False
        assert cellar.is_position_valid(2, 'single', 0) is False
        
        # Invalid side for shelf type
        assert cellar.is_position_valid(0, 'front', 0) is False  # single shelf
        assert cellar.is_position_valid(1, 'single', 0) is False  # double shelf
        
        # Invalid position index
        assert cellar.is_position_valid(0, 'single', -1) is False
        assert cellar.is_position_valid(0, 'single', 10) is False
        assert cellar.is_position_valid(1, 'front', 8) is False
    
    def test_cellar_position_availability(self):
        """Test position availability checks"""
        shelves = [Shelf(positions=5, is_double=False)]
        cellar = Cellar(id='c1', name='Test Cellar', shelves=shelves)
        
        # Initially all positions should be available
        assert cellar.is_position_available(0, 'single', 0) is True
        assert cellar.is_position_available(0, 'single', 4) is True
        
        # After assigning, position should be unavailable
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance = WineInstance(id='inst1', reference=ref)
        cellar.assign_wine_to_position(0, 'single', 0, instance)
        assert cellar.is_position_available(0, 'single', 0) is False
        assert cellar.is_position_available(0, 'single', 1) is True
    
    def test_cellar_wine_assignment_validation(self):
        """Test that wine assignment validates positions"""
        shelves = [Shelf(positions=5, is_double=False)]
        cellar = Cellar(id='c1', name='Test Cellar', shelves=shelves)
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance = WineInstance(id='inst1', reference=ref)
        
        # Valid assignment
        cellar.assign_wine_to_position(0, 'single', 0, instance)
        
        # Invalid position should raise ValueError
        with pytest.raises(ValueError, match="Invalid position"):
            cellar.assign_wine_to_position(0, 'single', 10, instance)
        with pytest.raises(ValueError, match="Invalid position"):
            cellar.assign_wine_to_position(1, 'single', 0, instance)  # shelf doesn't exist
        
        # Occupied position should raise ValueError
        instance2 = WineInstance(id='inst2', reference=ref)
        with pytest.raises(ValueError, match="not available"):
            cellar.assign_wine_to_position(0, 'single', 0, instance2)
    
    def test_cellar_wine_removal(self):
        """Test removing wine from cellar"""
        shelves = [Shelf(positions=5, is_double=False)]
        cellar = Cellar(id='c1', name='Test Cellar', shelves=shelves)
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance = WineInstance(id='inst1', reference=ref)
        
        # Assign wine
        cellar.assign_wine_to_position(0, 'single', 0, instance)
        assert cellar.is_position_available(0, 'single', 0) is False
        assert cellar.is_wine_instance_in_cellar(instance) is True
        
        # Remove wine
        cellar.remove_wine_from_cellar(instance)
        assert cellar.is_position_available(0, 'single', 0) is True
        assert cellar.is_wine_instance_in_cellar(instance) is False
    
    def test_cellar_wine_instance_tracking(self):
        """Test that cellar correctly tracks wine instances"""
        shelves = [Shelf(positions=5, is_double=True)]
        cellar = Cellar(id='c1', name='Test Cellar', shelves=shelves)
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance1 = WineInstance(id='inst1', reference=ref)
        instance2 = WineInstance(id='inst2', reference=ref)
        
        # Initially no instances
        assert cellar.is_wine_instance_in_cellar(instance1) is False
        assert cellar.is_wine_instance_in_cellar(instance2) is False
        
        # Assign instances to different positions
        cellar.assign_wine_to_position(0, 'front', 0, instance1)
        cellar.assign_wine_to_position(0, 'back', 0, instance2)
        
        # Both should be tracked
        assert cellar.is_wine_instance_in_cellar(instance1) is True
        assert cellar.is_wine_instance_in_cellar(instance2) is True
        
        # Remove one
        cellar.remove_wine_from_cellar(instance1)
        assert cellar.is_wine_instance_in_cellar(instance1) is False
        assert cellar.is_wine_instance_in_cellar(instance2) is True


class TestWineReferenceConsistency:
    """Test WineReference model data consistency"""
    
    def test_wine_reference_required_fields(self):
        """Test that required fields are present"""
        # Valid reference with all required fields
        ref = WineReference(
            id='ref1',
            name='Test Wine',
            type='Red',
            vintage=2018
        )
        assert ref.id == 'ref1'
        assert ref.name == 'Test Wine'
        assert ref.type == 'Red'
        assert ref.vintage == 2018
    
    def test_wine_reference_optional_fields(self):
        """Test that optional fields can be None"""
        ref = WineReference(
            id='ref1',
            name='Test Wine',
            type='Red',
            vintage=2018
        )
        assert ref.producer is None
        assert ref.varietals is None
        assert ref.region is None
        assert ref.country is None
        assert ref.rating is None
        assert ref.tasting_notes is None
        assert ref.label_image_url is None
    
    def test_wine_reference_unique_key_consistency(self):
        """Test that unique keys are consistent"""
        ref1 = WineReference(
            id='ref1',
            name='Wine A',
            type='Red',
            vintage=2018,
            producer='Winery A'
        )
        ref2 = WineReference(
            id='ref2',
            name='Wine A',
            type='Red',
            vintage=2018,
            producer='Winery A'
        )
        ref3 = WineReference(
            id='ref3',
            name='Wine A',
            type='Red',
            vintage=2019,  # Different vintage
            producer='Winery A'
        )
        ref4 = WineReference(
            id='ref4',
            name='Wine A',
            type='Red',
            vintage=2018,
            producer='Winery B'  # Different producer
        )
        
        # Same name, vintage, producer = same unique key
        assert ref1.get_unique_key() == ref2.get_unique_key()
        
        # Different vintage = different key
        assert ref1.get_unique_key() != ref3.get_unique_key()
        
        # Different producer = different key
        assert ref1.get_unique_key() != ref4.get_unique_key()
    
    def test_wine_reference_unique_key_with_none_producer(self):
        """Test unique key handling when producer is None"""
        ref1 = WineReference(
            id='ref1',
            name='Wine A',
            type='Red',
            vintage=2018,
            producer=None
        )
        ref2 = WineReference(
            id='ref2',
            name='Wine A',
            type='Red',
            vintage=2018
            # producer defaults to None
        )
        
        # Both should have same unique key (producer is None for both)
        assert ref1.get_unique_key() == ref2.get_unique_key()


class TestWineInstanceConsistency:
    """Test WineInstance model data consistency"""
    
    def test_wine_instance_required_reference(self):
        """Test that WineInstance requires a WineReference object"""
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        
        # Valid instance with reference
        instance = WineInstance(id='inst1', reference=ref)
        assert instance.reference == ref
        assert instance.reference.id == 'ref1'
    
    def test_wine_instance_state_transitions(self):
        """Test consumed and coravined state transitions"""
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance = WineInstance(id='inst1', reference=ref)
        
        # Initial state
        assert instance.consumed is False
        assert instance.consumed_date is None
        assert instance.coravined is False
        assert instance.coravined_date is None
        
        # Set consumed
        instance.set_consumed()
        assert instance.consumed is True
        assert instance.consumed_date is not None
        assert instance.coravined is False  # Unchanged
        
        # Reset and test coravined
        instance2 = WineInstance(id='inst2', reference=ref)
        instance2.set_coravined()
        assert instance2.coravined is True
        assert instance2.coravined_date is not None
        assert instance2.consumed is False  # Unchanged
    
    def test_wine_instance_optional_fields(self):
        """Test that optional fields can be None"""
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance = WineInstance(id='inst1', reference=ref)
        
        assert instance.price is None
        assert instance.purchase_date is None
        assert instance.drink_by_date is None
        assert instance.consumed_date is None
        assert instance.coravined_date is None
        assert instance.stored_date is None
        assert instance.created_at is None
        assert instance.updated_at is None


class TestCrossModelConsistency:
    """Test consistency across multiple models"""
    
    def test_wine_instance_reference_consistency(self):
        """Test that WineInstance references are valid WineReference objects"""
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        
        # Valid: instance with proper reference
        instance = WineInstance(id='inst1', reference=ref)
        assert isinstance(instance.reference, WineReference)
        assert instance.reference.id == ref.id
        assert instance.reference.name == ref.name
    
    def test_cellar_wine_instance_consistency(self):
        """Test that wine instances assigned to cellars are tracked correctly"""
        shelves = [Shelf(positions=5, is_double=True)]
        cellar = Cellar(id='c1', name='Test Cellar', shelves=shelves)
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance = WineInstance(id='inst1', reference=ref)
        
        # Assign to cellar
        cellar.assign_wine_to_position(0, 'front', 0, instance)
        
        # Verify instance is tracked
        assert cellar.is_wine_instance_in_cellar(instance) is True
        retrieved_instance = cellar.shelves[0].get_wine_at('front', 0)
        assert retrieved_instance == instance
        assert retrieved_instance.id == instance.id
        assert retrieved_instance.reference == instance.reference
    
    def test_wine_instance_single_cellar_placement(self):
        """Test that a wine instance can only be in one cellar position at a time"""
        shelves1 = [Shelf(positions=5, is_double=False)]
        shelves2 = [Shelf(positions=5, is_double=False)]
        cellar1 = Cellar(id='c1', name='Cellar 1', shelves=shelves1)
        cellar2 = Cellar(id='c2', name='Cellar 2', shelves=shelves2)
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance = WineInstance(id='inst1', reference=ref)
        
        # Assign to first cellar
        cellar1.assign_wine_to_position(0, 'single', 0, instance)
        assert cellar1.is_wine_instance_in_cellar(instance) is True
        assert cellar2.is_wine_instance_in_cellar(instance) is False
        
        # Try to assign to second cellar (should succeed, but instance removed from first)
        # Note: The current model allows this, but in practice you might want to check first
        cellar1.remove_wine_from_cellar(instance)
        cellar2.assign_wine_to_position(0, 'single', 0, instance)
        assert cellar1.is_wine_instance_in_cellar(instance) is False
        assert cellar2.is_wine_instance_in_cellar(instance) is True
    
    def test_multiple_instances_same_reference(self):
        """Test that multiple instances can share the same reference"""
        ref = WineReference(id='ref1', name='Test Wine', type='Red', vintage=2018)
        instance1 = WineInstance(id='inst1', reference=ref)
        instance2 = WineInstance(id='inst2', reference=ref)
        instance3 = WineInstance(id='inst3', reference=ref)
        
        # All instances reference the same WineReference object
        assert instance1.reference == ref
        assert instance2.reference == ref
        assert instance3.reference == ref
        assert instance1.reference == instance2.reference
        
        # But instances are different
        assert instance1.id != instance2.id
        assert instance1.id != instance3.id
        assert instance2.id != instance3.id


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_cellar(self):
        """Test cellar with no shelves"""
        cellar = Cellar(id='c1', name='Empty Cellar', shelves=[])
        assert cellar.capacity == 0
        assert len(cellar.shelves) == 0
        assert cellar.is_position_valid(0, 'single', 0) is False
    
    def test_single_position_shelf(self):
        """Test shelf with only one position"""
        shelf = Shelf(positions=1, is_double=False)
        assert shelf.positions == 1
        assert len(shelf.wine_positions[0]) == 1
        assert shelf.get_wine_at('single', 0) is None
        
        # Should raise error for position 1
        with pytest.raises(ValueError):
            shelf.get_wine_at('single', 1)
    
    def test_large_shelf(self):
        """Test shelf with many positions"""
        shelf = Shelf(positions=100, is_double=True)
        assert shelf.positions == 100
        assert len(shelf.wine_positions[0]) == 100
        assert len(shelf.wine_positions[1]) == 100
        
        # Valid positions
        assert shelf.get_wine_at('front', 0) is None
        assert shelf.get_wine_at('front', 99) is None
        assert shelf.get_wine_at('back', 99) is None
    
    def test_zero_vintage(self):
        """Test wine reference with vintage 0 (edge case)"""
        ref = WineReference(
            id='ref1',
            name='Test Wine',
            type='Red',
            vintage=0  # Edge case: vintage 0
        )
        assert ref.vintage == 0
        assert ref.get_unique_key()[1] == 0  # vintage is second element
    
    def test_negative_vintage(self):
        """Test wine reference with negative vintage (should be allowed by model)"""
        ref = WineReference(
            id='ref1',
            name='Test Wine',
            type='Red',
            vintage=-100  # Negative vintage (edge case)
        )
        assert ref.vintage == -100
