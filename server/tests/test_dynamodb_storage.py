"""Tests for DynamoDB storage operations"""
import pytest
import os
import boto3
from botocore.exceptions import ClientError
from server.dynamo.storage import (
    # Cellar functions
    get_all_cellars,
    put_cellar,
    get_cellar_by_id,
    delete_cellar,
    # Wine reference functions
    get_all_wine_references,
    put_wine_reference,
    get_wine_reference_by_id,
    delete_wine_reference,
    # Wine instance functions
    get_all_wine_instances,
    save_wine_instances,
    get_wine_instance_by_id,
    put_wine_instance,
    delete_wine_instance,
    # Table names
    CELLARS_TABLE,
    WINE_REFERENCES_TABLE,
    USER_WINE_REFERENCES_TABLE,
    WINE_INSTANCES_TABLE
)
from server.dynamo.setup_tables import get_dynamodb_client
from server.models import Shelf, Cellar, GlobalWineReference, UserWineReference, WineInstance
from server.data.storage_serializers import serialize_cellar, serialize_global_wine_reference, serialize_wine_instance
from server.utils import generate_id, get_current_timestamp

# Helper functions for batch operations (wrappers around put_* functions)
def save_cellars(cellars):
    """Save multiple cellars (batch operation - replaces all existing)"""
    # Get all existing cellars and delete them first (to match "replaces" behavior)
    existing = get_all_cellars()
    for c in existing:
        delete_cellar(c['id'])
    # Save new cellars
    for c in cellars:
        put_cellar(c)

def save_wine_references(refs):
    """Save multiple wine references (batch operation - replaces all existing)"""
    # Get all existing references and delete them first (to match "replaces" behavior)
    existing = get_all_wine_references()
    for r in existing:
        delete_wine_reference(r['id'])
    # Save new references
    for r in refs:
        put_wine_reference(r)

def update_cellar(cellar):
    """Update a cellar (alias for put_cellar)"""
    put_cellar(cellar)

def update_wine_reference(ref):
    """Update a wine reference (alias for put_wine_reference)"""
    put_wine_reference(ref)

def update_wine_instance(inst):
    """Update a wine instance (alias for put_wine_instance)"""
    put_wine_instance(inst)

def save_wine_instances(instances):
    """Save multiple wine instances (batch operation - replaces all existing)"""
    # Get all existing instances and delete them first (to match "replaces" behavior)
    existing = get_all_wine_instances()
    for inst in existing:
        delete_wine_instance(inst['id'])
    # Save new instances
    for inst in instances:
        put_wine_instance(inst)


@pytest.fixture(scope="module")
def dynamodb_tables():
    """Set up DynamoDB Local tables for testing"""
    # Use DynamoDB Local endpoint
    endpoint = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
    # Set environment variables for this module
    os.environ['DYNAMODB_ENDPOINT'] = endpoint
    os.environ['DYNAMODB_REGION'] = 'us-east-1'
    
    client = get_dynamodb_client()
    
    # Create tables if they don't exist
    tables = client.list_tables().get('TableNames', [])
    
    def create_table_if_not_exists(table_name):
        """Helper to create a table if it doesn't exist"""
        if table_name not in tables:
            try:
                client.create_table(
                    TableName=table_name,
                    KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                    AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                    BillingMode='PAY_PER_REQUEST'
                )
                waiter = client.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceInUseException':
                    raise
    
    create_table_if_not_exists(CELLARS_TABLE)
    create_table_if_not_exists(WINE_REFERENCES_TABLE)
    create_table_if_not_exists(USER_WINE_REFERENCES_TABLE)
    create_table_if_not_exists(WINE_INSTANCES_TABLE)

    yield

    # Cleanup: delete all items from tables
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=endpoint,
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )

    for table_name in [CELLARS_TABLE, WINE_REFERENCES_TABLE, USER_WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE]:
        table = dynamodb.Table(table_name)
        # Scan and delete all items
        response = table.scan()
        with table.batch_writer() as batch:
            for item in response.get('Items', []):
                batch.delete_item(Key={'id': item['id']})


@pytest.fixture(autouse=True)
def clear_tables(dynamodb_tables):
    """Clear all tables before each test"""
    endpoint = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=endpoint,
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    # Clear all items from all tables
    for table_name in [CELLARS_TABLE, WINE_REFERENCES_TABLE, USER_WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE]:
        table = dynamodb.Table(table_name)
        response = table.scan()
        with table.batch_writer() as batch:
            for item in response.get('Items', []):
                batch.delete_item(Key={'id': item['id']})


# ==================== Cellar Tests ====================

def test_load_cellars_empty(dynamodb_tables):
    """Test loading cellars when table is empty"""
    cellars = get_all_cellars()
    assert cellars == []
    assert isinstance(cellars, list)


def test_save_and_load_cellars(dynamodb_tables):
    """Test saving and loading cellars"""
    # Create a test cellar
    shelves = [Shelf(positions=10, is_double=False), Shelf(positions=8, is_double=True)]
    cellar = Cellar(
        id=generate_id(),
        name="Test Cellar",
        shelves=shelves,
        temperature=55,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    
    # Serialize and save
    cellar_data = serialize_cellar(cellar)
    save_cellars([cellar_data])
    
    # Load and verify
    loaded = get_all_cellars()
    assert len(loaded) == 1
    assert loaded[0]['id'] == cellar.id
    assert loaded[0]['name'] == 'Test Cellar'
    assert loaded[0]['temperature'] == 55
    assert loaded[0]['shelves'] == [[10, False], [8, True]]


def test_save_multiple_cellars(dynamodb_tables):
    """Test saving multiple cellars"""
    cellars = []
    for i in range(3):
        cellar = Cellar(
            id=generate_id(),
            name=f"Cellar {i}",
            shelves=[Shelf(positions=5, is_double=False)],
            version=1,
            created_at=get_current_timestamp(),
            updated_at=get_current_timestamp()
        )
        cellars.append(serialize_cellar(cellar))
    
    save_cellars(cellars)
    
    loaded = get_all_cellars()
    assert len(loaded) == 3
    assert {c['name'] for c in loaded} == {'Cellar 0', 'Cellar 1', 'Cellar 2'}


def test_get_cellar_by_id(dynamodb_tables):
    """Test getting a cellar by ID"""
    # Create and save a cellar
    cellar = Cellar(
        id=generate_id(),
        name="Specific Cellar",
        shelves=[Shelf(positions=10, is_double=False)],
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_cellars([serialize_cellar(cellar)])
    
    # Get by ID
    found = get_cellar_by_id(cellar.id)
    assert found is not None
    assert found['id'] == cellar.id
    assert found['name'] == 'Specific Cellar'


def test_get_cellar_by_id_not_found(dynamodb_tables):
    """Test getting a non-existent cellar"""
    found = get_cellar_by_id('non-existent-id')
    assert found is None


def test_update_cellar(dynamodb_tables):
    """Test updating a cellar"""
    # Create and save
    cellar = Cellar(
        id=generate_id(),
        name="Original Name",
        shelves=[Shelf(positions=10, is_double=False)],
        temperature=50,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_cellars([serialize_cellar(cellar)])
    
    # Update
    cellar.name = "Updated Name"
    cellar.temperature = 60
    cellar.version = 2
    cellar.updated_at = get_current_timestamp()
    update_cellar(serialize_cellar(cellar))
    
    # Verify
    found = get_cellar_by_id(cellar.id)
    assert found['name'] == 'Updated Name'
    assert found['temperature'] == 60
    assert found['version'] == 2


def test_delete_cellar(dynamodb_tables):
    """Test deleting a cellar"""
    # Create and save
    cellar = Cellar(
        id=generate_id(),
        name="To Delete",
        shelves=[Shelf(positions=10, is_double=False)],
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_cellars([serialize_cellar(cellar)])
    
    # Delete
    delete_cellar(cellar.id)
    
    # Verify deleted
    found = get_cellar_by_id(cellar.id)
    assert found is None
    
    # Verify table is empty
    all_cellars = get_all_cellars()
    assert len(all_cellars) == 0


def test_save_cellars_replaces_existing(dynamodb_tables):
    """Test that saving cellars replaces existing ones"""
    # Create and save initial cellars
    cellar1 = Cellar(
        id=generate_id(),
        name="Cellar 1",
        shelves=[Shelf(positions=10, is_double=False)],
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    cellar2 = Cellar(
        id=generate_id(),
        name="Cellar 2",
        shelves=[Shelf(positions=8, is_double=False)],
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_cellars([serialize_cellar(cellar1), serialize_cellar(cellar2)])
    
    # Save only one cellar (should remove the other)
    cellar3 = Cellar(
        id=generate_id(),
        name="Cellar 3",
        shelves=[Shelf(positions=5, is_double=False)],
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_cellars([serialize_cellar(cellar3)])
    
    # Verify only the new cellar exists
    loaded = get_all_cellars()
    assert len(loaded) == 1
    assert loaded[0]['name'] == 'Cellar 3'


# ==================== Wine Reference Tests ====================

def test_load_wine_references_empty(dynamodb_tables):
    """Test loading wine references when table is empty"""
    references = get_all_wine_references()
    assert references == []
    assert isinstance(references, list)


def test_save_and_load_wine_references(dynamodb_tables):
    """Test saving and loading wine references"""
    # Create a test reference
    reference = GlobalWineReference(
        id=generate_id(),
        name="Test Wine",
        type="Red",
        vintage=2018,
        producer="Test Producer",
        varietals=["Cabernet Sauvignon"],
        region="Napa Valley",
        country="USA",
        label_image_url="https://example.com/label.jpg",
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    
    # Serialize and save
    reference_data = serialize_global_wine_reference(reference)
    save_wine_references([reference_data])
    
    # Load and verify
    loaded = get_all_wine_references()
    assert len(loaded) == 1
    assert loaded[0]['id'] == reference.id
    assert loaded[0]['name'] == 'Test Wine'
    assert loaded[0]['type'] == 'Red'
    assert loaded[0]['vintage'] == 2018
    assert loaded[0]['producer'] == 'Test Producer'


def test_save_multiple_wine_references(dynamodb_tables):
    """Test saving multiple wine references"""
    references = []
    for i in range(3):
        reference = GlobalWineReference(
            id=generate_id(),
            name=f"Wine {i}",
            type="Red" if i % 2 == 0 else "White",
            vintage=2018 + i,
            version=1,
            created_at=get_current_timestamp(),
            updated_at=get_current_timestamp()
        )
        references.append(serialize_global_wine_reference(reference))
    
    save_wine_references(references)
    
    loaded = get_all_wine_references()
    assert len(loaded) == 3
    assert {r['name'] for r in loaded} == {'Wine 0', 'Wine 1', 'Wine 2'}


def test_get_wine_reference_by_id(dynamodb_tables):
    """Test getting a wine reference by ID"""
    # Create and save
    reference = GlobalWineReference(
        id=generate_id(),
        name="Specific Wine",
        type="Red",
        vintage=2018,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_references([serialize_global_wine_reference(reference)])
    
    # Get by ID
    found = get_wine_reference_by_id(reference.id)
    assert found is not None
    assert found['id'] == reference.id
    assert found['name'] == 'Specific Wine'


def test_get_wine_reference_by_id_not_found(dynamodb_tables):
    """Test getting a non-existent wine reference"""
    found = get_wine_reference_by_id('non-existent-id')
    assert found is None


def test_update_wine_reference(dynamodb_tables):
    """Test updating a wine reference"""
    # Create and save
    reference = GlobalWineReference(
        id=generate_id(),
        name="Original Name",
        type="Red",
        vintage=2018,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_references([serialize_global_wine_reference(reference)])

    # Update
    reference.name = "Updated Name"
    reference.version = 2
    reference.updated_at = get_current_timestamp()
    update_wine_reference(serialize_global_wine_reference(reference))

    # Verify
    found = get_wine_reference_by_id(reference.id)
    assert found['name'] == 'Updated Name'
    assert found['version'] == 2


def test_delete_wine_reference(dynamodb_tables):
    """Test deleting a wine reference"""
    # Create and save
    reference = GlobalWineReference(
        id=generate_id(),
        name="To Delete",
        type="Red",
        vintage=2018,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_references([serialize_global_wine_reference(reference)])
    
    # Delete
    delete_wine_reference(reference.id)
    
    # Verify deleted
    found = get_wine_reference_by_id(reference.id)
    assert found is None
    
    # Verify table is empty
    all_references = get_all_wine_references()
    assert len(all_references) == 0


def test_save_wine_references_replaces_existing(dynamodb_tables):
    """Test that saving wine references replaces existing ones"""
    # Create and save initial references
    ref1 = GlobalWineReference(
        id=generate_id(),
        name="Reference 1",
        type="Red",
        vintage=2018,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    ref2 = GlobalWineReference(
        id=generate_id(),
        name="Reference 2",
        type="White",
        vintage=2019,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_references([serialize_global_wine_reference(ref1), serialize_global_wine_reference(ref2)])
    
    # Save only one reference (should remove the other)
    ref3 = GlobalWineReference(
        id=generate_id(),
        name="Reference 3",
        type="Red",
        vintage=2020,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_references([serialize_global_wine_reference(ref3)])
    
    # Verify only the new reference exists
    loaded = get_all_wine_references()
    assert len(loaded) == 1
    assert loaded[0]['name'] == 'Reference 3'


# ==================== Wine Instance Tests ====================

def test_load_wine_instances_empty(dynamodb_tables):
    """Test loading wine instances when table is empty"""
    instances = get_all_wine_instances()
    assert instances == []
    assert isinstance(instances, list)


def test_save_and_load_wine_instances(dynamodb_tables):
    """Test saving and loading wine instances"""
    # Create a user wine reference first
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    # Create a wine instance
    instance = WineInstance(
        id=generate_id(),
        reference=user_ref,
        price=45.99,
        purchase_date="2024-01-15",
        drink_by_date="2030-01-15",
        consumed=False,
        stored_date=get_current_timestamp(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    
    # Serialize and save
    instance_data = serialize_wine_instance(instance)
    save_wine_instances([instance_data])
    
    # Load and verify
    loaded = get_all_wine_instances()
    assert len(loaded) == 1
    assert loaded[0]['id'] == instance.id
    assert loaded[0]['referenceId'] == user_ref.id
    # DynamoDB returns Decimals, so convert for comparison
    assert float(loaded[0]['price']) == 45.99
    assert loaded[0]['purchaseDate'] == '2024-01-15'


def test_save_multiple_wine_instances(dynamodb_tables):
    """Test saving multiple wine instances"""
    # Create a user wine reference
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )

    instances = []
    for i in range(3):
        instance = WineInstance(
            id=generate_id(),
            reference=user_ref,
            price=50.0 + i,
            version=1,
            created_at=get_current_timestamp(),
            updated_at=get_current_timestamp()
        )
        instances.append(serialize_wine_instance(instance))
    
    save_wine_instances(instances)
    
    loaded = get_all_wine_instances()
    assert len(loaded) == 3
    # DynamoDB returns Decimals, so convert for comparison
    assert {float(inst['price']) for inst in loaded} == {50.0, 51.0, 52.0}


def test_get_wine_instance_by_id(dynamodb_tables):
    """Test getting a wine instance by ID"""
    # Create user reference and instance
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )

    instance = WineInstance(
        id=generate_id(),
        reference=user_ref,
        price=99.99,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_instances([serialize_wine_instance(instance)])
    
    # Get by ID
    found = get_wine_instance_by_id(instance.id)
    assert found is not None
    assert found['id'] == instance.id
    # DynamoDB returns Decimals, so convert for comparison
    assert float(found['price']) == 99.99


def test_get_wine_instance_by_id_not_found(dynamodb_tables):
    """Test getting a non-existent wine instance"""
    found = get_wine_instance_by_id('non-existent-id')
    assert found is None


def test_update_wine_instance(dynamodb_tables):
    """Test updating a wine instance"""
    # Create user reference and instance
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )

    instance = WineInstance(
        id=generate_id(),
        reference=user_ref,
        price=50.0,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_instances([serialize_wine_instance(instance)])
    
    # Update
    instance.price = 75.0
    instance.version = 2
    instance.updated_at = get_current_timestamp()
    update_wine_instance(serialize_wine_instance(instance))
    
    # Verify
    found = get_wine_instance_by_id(instance.id)
    # DynamoDB returns Decimals, so convert for comparison
    assert float(found['price']) == 75.0
    assert found['version'] == 2


def test_delete_wine_instance(dynamodb_tables):
    """Test deleting a wine instance"""
    # Create user reference and instance
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )

    instance = WineInstance(
        id=generate_id(),
        reference=user_ref,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_instances([serialize_wine_instance(instance)])
    
    # Delete
    delete_wine_instance(instance.id)
    
    # Verify deleted
    found = get_wine_instance_by_id(instance.id)
    assert found is None
    
    # Verify table is empty
    all_instances = get_all_wine_instances()
    assert len(all_instances) == 0


def test_save_wine_instances_replaces_existing(dynamodb_tables):
    """Test that saving wine instances replaces existing ones"""
    # Create user reference
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )

    # Create and save initial instances
    inst1 = WineInstance(
        id=generate_id(),
        reference=user_ref,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    inst2 = WineInstance(
        id=generate_id(),
        reference=user_ref,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_instances([serialize_wine_instance(inst1), serialize_wine_instance(inst2)])

    # Save only one instance (should remove the other)
    inst3 = WineInstance(
        id=generate_id(),
        reference=user_ref,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_instances([serialize_wine_instance(inst3)])
    
    # Verify only the new instance exists
    loaded = get_all_wine_instances()
    assert len(loaded) == 1
    assert loaded[0]['id'] == inst3.id


def test_wine_instance_with_coravined(dynamodb_tables):
    """Test saving and loading wine instance with coravined field"""
    # Create user reference
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )

    # Create instance with coravined
    instance = WineInstance(
        id=generate_id(),
        reference=user_ref,
        coravined=True,
        coravined_date=get_current_timestamp(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    
    # Save and verify
    save_wine_instances([serialize_wine_instance(instance)])
    loaded = get_all_wine_instances()
    assert len(loaded) == 1
    assert loaded[0]['coravined'] is True
    assert loaded[0]['coravinedDate'] is not None


# ==================== Integration Tests ====================

def test_full_crud_cycle_cellar(dynamodb_tables):
    """Test complete CRUD cycle for cellars"""
    # Create
    cellar = Cellar(
        id=generate_id(),
        name="CRUD Test Cellar",
        shelves=[Shelf(positions=10, is_double=False)],
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_cellars([serialize_cellar(cellar)])
    
    # Read
    found = get_cellar_by_id(cellar.id)
    assert found is not None
    assert found['name'] == 'CRUD Test Cellar'
    
    # Update
    cellar.name = "Updated CRUD Cellar"
    cellar.version = 2
    cellar.updated_at = get_current_timestamp()
    update_cellar(serialize_cellar(cellar))
    
    found = get_cellar_by_id(cellar.id)
    assert found['name'] == 'Updated CRUD Cellar'
    assert found['version'] == 2
    
    # Delete
    delete_cellar(cellar.id)
    found = get_cellar_by_id(cellar.id)
    assert found is None


def test_full_crud_cycle_wine_reference(dynamodb_tables):
    """Test complete CRUD cycle for wine references"""
    # Create
    reference = GlobalWineReference(
        id=generate_id(),
        name="CRUD Test Wine",
        type="Red",
        vintage=2018,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_references([serialize_global_wine_reference(reference)])
    
    # Read
    found = get_wine_reference_by_id(reference.id)
    assert found is not None
    assert found['name'] == 'CRUD Test Wine'
    
    # Update
    reference.name = "Updated CRUD Wine"
    reference.version = 2
    reference.updated_at = get_current_timestamp()
    update_wine_reference(serialize_global_wine_reference(reference))
    
    found = get_wine_reference_by_id(reference.id)
    assert found['name'] == 'Updated CRUD Wine'
    assert found['version'] == 2
    
    # Delete
    delete_wine_reference(reference.id)
    found = get_wine_reference_by_id(reference.id)
    assert found is None


def test_full_crud_cycle_wine_instance(dynamodb_tables):
    """Test complete CRUD cycle for wine instances"""
    # Create user reference
    user_ref = UserWineReference(
        id=generate_id(),
        global_reference_id=generate_id(),
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )

    # Create instance
    instance = WineInstance(
        id=generate_id(),
        reference=user_ref,
        price=50.0,
        version=1,
        created_at=get_current_timestamp(),
        updated_at=get_current_timestamp()
    )
    save_wine_instances([serialize_wine_instance(instance)])
    
    # Read
    found = get_wine_instance_by_id(instance.id)
    assert found is not None
    # DynamoDB returns Decimals, so convert for comparison
    assert float(found['price']) == 50.0
    
    # Update
    instance.price = 75.0
    instance.version = 2
    instance.updated_at = get_current_timestamp()
    update_wine_instance(serialize_wine_instance(instance))
    
    found = get_wine_instance_by_id(instance.id)
    # DynamoDB returns Decimals, so convert for comparison
    assert float(found['price']) == 75.0
    assert found['version'] == 2
    
    # Delete
    delete_wine_instance(instance.id)
    found = get_wine_instance_by_id(instance.id)
    assert found is None
