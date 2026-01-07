# WineApp Server API Tests

This directory contains comprehensive API tests for the WineApp server. The tests are located in `server/tests/` since they test server-side functionality.

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_cellars.py` - Tests for cellar endpoints
- `test_wine_references.py` - Tests for wine reference endpoints
- `test_wine_instances.py` - Tests for wine instance endpoints (including unshelved)

## Running Tests

### Run all tests:
```bash
python3 -m pytest server/tests/ -v
```

### Run specific test file:
```bash
python3 -m pytest server/tests/test_cellars.py -v
```

### Run a specific test:
```bash
python3 -m pytest server/tests/test_cellars.py::test_create_cellar -v
```

### Run with coverage:
```bash
python3 -m pytest server/tests/ --cov=server --cov-report=html
```

## Test Coverage

The tests cover:

### Cellars (8 tests)
- GET all cellars
- POST create cellar
- GET cellar by ID
- GET cellar not found (404)
- PUT update cellar
- DELETE cellar
- GET cellar layout
- Create cellar with minimal data

### Wine References (7 tests)
- GET all wine references
- POST create wine reference
- POST create duplicate (409 conflict)
- GET wine reference by ID (with instances)
- GET wine reference not found (404)
- PUT update wine reference
- DELETE wine reference
- Create with minimal data

### Wine Instances (12 tests)
- GET all wine instances
- POST create wine instance
- POST create with invalid reference (404)
- GET wine instance by ID
- GET wine instance not found (404)
- PUT update wine instance
- DELETE wine instance
- POST consume wine instance
- PUT update wine instance location
- GET unshelved instances
- POST assign unshelved to cellar

## Test Fixtures

The `conftest.py` file provides:
- `client` - Flask test client with isolated test data
- `sample_cellar` - Sample cellar data
- `sample_wine_reference` - Sample wine reference data
- `sample_wine_instance` - Sample wine instance data
- `created_wine_reference` - Pre-created wine reference for instance tests

## Test Isolation

Each test runs with:
- Temporary directory for JSON data files
- Isolated data (no interference between tests)
- Automatic cleanup after each test
