# DynamoDB Storage Tests

This document describes the DynamoDB storage tests in `test_dynamodb_storage.py`.

## Prerequisites

1. **DynamoDB Local must be running**:
   ```bash
   ./start_dynamodb_local.sh
   ```

2. **Install dependencies**:
   ```bash
   pip install -r server/requirements.txt
   ```

## Running Tests

### Run all DynamoDB storage tests:
```bash
PYTHONPATH=. python3 -m pytest server/tests/test_dynamodb_storage.py -v
```

### Run specific test categories:
```bash
# Test only cellar operations
PYTHONPATH=. python3 -m pytest server/tests/test_dynamodb_storage.py -k "cellar" -v

# Test only wine reference operations
PYTHONPATH=. python3 -m pytest server/tests/test_dynamodb_storage.py -k "wine_reference" -v

# Test only wine instance operations
PYTHONPATH=. python3 -m pytest server/tests/test_dynamodb_storage.py -k "wine_instance" -v
```

### Run with coverage:
```bash
PYTHONPATH=. python3 -m pytest server/tests/test_dynamodb_storage.py --cov=server.dynamo --cov-report=html -v
```

## Test Structure

The tests are organized into the following categories:

### Cellar Tests (8 tests)
- `test_load_cellars_empty` - Loading from empty table
- `test_save_and_load_cellars` - Basic save/load operations
- `test_save_multiple_cellars` - Saving multiple items
- `test_get_cellar_by_id` - Getting item by ID
- `test_get_cellar_by_id_not_found` - Non-existent item handling
- `test_update_cellar` - Updating existing item
- `test_delete_cellar` - Deleting item
- `test_save_cellars_replaces_existing` - Replace behavior

### Wine Reference Tests (8 tests)
- `test_load_wine_references_empty` - Loading from empty table
- `test_save_and_load_wine_references` - Basic save/load operations
- `test_save_multiple_wine_references` - Saving multiple items
- `test_get_wine_reference_by_id` - Getting item by ID
- `test_get_wine_reference_by_id_not_found` - Non-existent item handling
- `test_update_wine_reference` - Updating existing item
- `test_delete_wine_reference` - Deleting item
- `test_save_wine_references_replaces_existing` - Replace behavior

### Wine Instance Tests (9 tests)
- `test_load_wine_instances_empty` - Loading from empty table
- `test_save_and_load_wine_instances` - Basic save/load operations
- `test_save_multiple_wine_instances` - Saving multiple items
- `test_get_wine_instance_by_id` - Getting item by ID
- `test_get_wine_instance_by_id_not_found` - Non-existent item handling
- `test_update_wine_instance` - Updating existing item
- `test_delete_wine_instance` - Deleting item
- `test_save_wine_instances_replaces_existing` - Replace behavior
- `test_wine_instance_with_location` - Instance with cellar location

### Integration Tests (3 tests)
- `test_full_crud_cycle_cellar` - Complete CRUD cycle for cellars
- `test_full_crud_cycle_wine_reference` - Complete CRUD cycle for wine references
- `test_full_crud_cycle_wine_instance` - Complete CRUD cycle for wine instances

## Test Fixtures

### `dynamodb_tables` (module scope)
- Sets up DynamoDB Local connection
- Creates tables if they don't exist
- Cleans up all items after all tests complete

### `clear_tables` (autouse, function scope)
- Clears all items from all tables before each test
- Ensures test isolation

## Test Coverage

The tests cover:
- ✅ Creating/reading/updating/deleting entities
- ✅ Batch operations (saving multiple items)
- ✅ Empty table handling
- ✅ Non-existent item handling
- ✅ Replace behavior (saving replaces existing items)
- ✅ Complex data structures (cellar locations, nested objects)
- ✅ Full CRUD cycles

## Notes

- Tests use DynamoDB Local, so they don't require AWS credentials
- Each test is isolated - tables are cleared before each test
- Tests use the actual storage functions, not mocks
- All tests verify data integrity (IDs, fields, relationships)
