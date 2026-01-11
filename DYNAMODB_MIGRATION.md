# DynamoDB Migration Guide

## Overview

The WineApp server can now use DynamoDB instead of JSON files for storage. The migration involves:

1. Installing Docker and DynamoDB Local
2. Creating DynamoDB tables
3. Migrating existing data
4. Updating the server code to use DynamoDB (optional - currently defaults to file storage)

## Current Status

- ✅ Docker setup scripts created
- ✅ DynamoDB Local setup scripts created
- ✅ DynamoDB storage adapter created (`server/dynamodb_storage.py`)
- ✅ Table setup script created (`server/setup_dynamodb_tables.py`)
- ✅ Migration script created (`server/migrate_to_dynamodb.py`)
- ✅ boto3 added to requirements.txt
- ⚠️  Server code still uses file storage by default

## Quick Start

### 1. Install Docker Desktop

See `DOCKER_SETUP.md` for detailed instructions.

**Quick method:**
- Download from https://www.docker.com/products/docker-desktop
- Or run: `brew install --cask docker` (requires sudo password)
- Launch Docker Desktop

### 2. Start DynamoDB Local

```bash
./start_dynamodb_local.sh
```

This starts DynamoDB Local in a Docker container on port 8000.

### 3. Install Python Dependencies

```bash
pip install -r server/requirements.txt
```

This installs `boto3` for DynamoDB access.

### 4. Create DynamoDB Tables

```bash
PYTHONPATH=. python server/setup_dynamodb_tables.py
```

This creates three tables:
- `wineapp-cellars`
- `wineapp-wine-references`
- `wineapp-wine-instances`

### 5. Migrate Existing Data (Optional)

If you have existing JSON files, migrate them to DynamoDB:

```bash
PYTHONPATH=. python server/migrate_to_dynamodb.py
```

### 6. Use DynamoDB Storage

To switch the server to use DynamoDB, set the environment variable:

```bash
export STORAGE_BACKEND=dynamodb
export DYNAMODB_ENDPOINT=http://localhost:8000
export DYNAMODB_REGION=us-east-1
```

Then start the server as usual.

**Note:** The server code currently defaults to file storage. To make DynamoDB the default, you need to update the modules to use the storage adapter (see "Next Steps" below).

## Architecture

### Storage Layers

1. **Model Objects** (Cellar, WineReference, WineInstance)
   - Defined in `server/models.py`
   - Used by business logic

2. **Serialized Data** (Dict[str, Any])
   - JSON-serializable dictionaries
   - Serialization handled by `server/storage.py`

3. **Storage Backend**
   - File storage: JSON files in `server/data/`
   - DynamoDB storage: Tables in DynamoDB Local or AWS DynamoDB

### Storage Adapter

The `server/storage_adapter.py` module provides a unified interface for storage operations. However, **it's not yet integrated into the server code**. The current implementation in `cellars.py`, `wine_references.py`, and `wine_instances.py` still uses file storage directly.

### Current File Structure

```
server/
├── models.py              # Data models
├── storage.py             # Serialization/deserialization
├── dynamodb_storage.py    # DynamoDB storage operations (low-level)
├── storage_adapter.py     # Unified storage interface (not yet used)
├── cellars.py             # Cellar endpoints (uses file storage)
├── wine_references.py     # Wine reference endpoints (uses file storage)
└── wine_instances.py      # Wine instance endpoints (uses file storage)
```

## Next Steps: Integrating DynamoDB Storage

To fully integrate DynamoDB, you need to update the three module files to use the storage adapter. This requires:

1. **Updating imports** in `cellars.py`, `wine_references.py`, `wine_instances.py`
2. **Replacing file I/O** with storage adapter calls
3. **Handling circular dependencies** (cellars ↔ wine instances)

The storage adapter (`server/storage_adapter.py`) is designed to handle this, but due to circular dependencies between modules, it needs to be carefully integrated.

### Recommended Approach

1. Update `cellars.py` to use `storage_adapter.load_cellars()` and `storage_adapter.save_cellars()`
2. Update `wine_references.py` to use `storage_adapter.load_wine_references()` and `storage_adapter.save_wine_references()`
3. Update `wine_instances.py` to use `storage_adapter.load_wine_instances()` and `storage_adapter.save_wine_instances()`

However, the circular dependency between cellars and wine instances needs careful handling - the current implementation in each module handles this by loading cellars without wine instances first, then loading wine instances, then reloading cellars with wine instances resolved.

## Testing

After switching to DynamoDB, test all endpoints:

```bash
# Test cellars
curl http://localhost:5001/cellars

# Test wine references
curl http://localhost:5001/wine-references

# Test wine instances
curl http://localhost:5001/wine-instances
```

## Troubleshooting

### DynamoDB Local not running
```
Error: Cannot connect to DynamoDB at http://localhost:8000
```
**Solution:** Start DynamoDB Local: `./start_dynamodb_local.sh`

### Tables don't exist
```
ResourceNotFoundException: Requested resource not found
```
**Solution:** Create tables: `PYTHONPATH=. python server/setup_dynamodb_tables.py`

### boto3 not installed
```
ModuleNotFoundError: No module named 'boto3'
```
**Solution:** Install dependencies: `pip install -r server/requirements.txt`
