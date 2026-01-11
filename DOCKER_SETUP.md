# Docker and DynamoDB Local Setup

## Installing Docker Desktop

Docker Desktop needs to be installed manually on macOS. You have two options:

### Option 1: Download Docker Desktop (Recommended)
1. Go to https://www.docker.com/products/docker-desktop
2. Download Docker Desktop for Mac (Apple Silicon or Intel)
3. Open the downloaded `.dmg` file
4. Drag Docker.app to Applications folder
5. Launch Docker Desktop from Applications
6. Complete the setup wizard

### Option 2: Install via Homebrew (requires sudo password)
```bash
brew install --cask docker
open /Applications/Docker.app
```

After installation, verify Docker is working:
```bash
docker --version
docker ps
```

## Starting DynamoDB Local

Once Docker is installed and running, use the provided script to start DynamoDB Local:

```bash
./start_dynamodb_local.sh
```

Or manually run:
```bash
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local
```

## Stopping DynamoDB Local

```bash
docker stop dynamodb-local
docker rm dynamodb-local
```

Or use the provided script:
```bash
./stop_dynamodb_local.sh
```

## DynamoDB Local Endpoint

Once running, DynamoDB Local will be available at:
- **Endpoint**: `http://localhost:8000`
- **Region**: `us-east-1` (or any region, DynamoDB Local doesn't care)

## Creating Tables

After starting DynamoDB Local, run the table creation script:

```bash
PYTHONPATH=. python server/setup_dynamodb_tables.py
```

This will create three tables:
- `wineapp-cellars`
- `wineapp-wine-references`
- `wineapp-wine-instances`

## Migrating Data from JSON Files

To migrate existing JSON data to DynamoDB:

```bash
PYTHONPATH=. python server/migrate_to_dynamodb.py
```

## Environment Variables

To switch between file storage and DynamoDB, set:

```bash
export STORAGE_BACKEND=dynamodb  # or 'file' for JSON files
export DYNAMODB_ENDPOINT=http://localhost:8000
export DYNAMODB_REGION=us-east-1
```

If `STORAGE_BACKEND` is not set, the server defaults to `file` storage for backward compatibility.
