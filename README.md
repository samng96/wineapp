# WineApp

A client-server application for managing a personal wine inventory. Track, organize, and manage your wine collection with support for multiple cellars, wine references, tasting notes, and bottle tracking.

## Features

- **Cellar Management**: Create and manage multiple cellars with customizable shelves (single or double-sided)
- **Wine Tracking**: Track individual wine bottles with purchase dates, prices, and consumption status
- **Wine References**: Maintain a global database of wine information (name, vintage, producer, varietals, region, country)
- **Personal Notes**: Add personal ratings and tasting notes to wines
- **Drink By Date**: Track recommended drink-by years per wine, auto-calculated from Vivino vintage data
- **Unshelved Wines**: Automatically track wines that haven't been placed in a cellar yet
- **Search & Filter**: Powerful search and filtering capabilities by type, varietal, country, consumption status, and more
- **Wine Details**: View detailed information about wines including location, notes, related bottles, and other vintages
- **Coravin Support**: Track wines opened with Coravin
- **Vivino Integration**: Search and import wine information from Vivino, including label images
- **Local Label Images**: Wine label images are downloaded at populate time and served locally

## Project Structure

```
WineApp/
├── webclient/              # Web-based frontend application
│   ├── models/            # Client-side data models (Cellar, Shelf, WineInstance, WineReference)
│   ├── utils/             # Utility functions (location utilities)
│   ├── tests/             # Client-side tests
│   ├── assets/            # Images and UI assets
│   ├── app.js             # Main application controller
│   ├── api.js             # API communication layer
│   ├── cellarManager.js   # Cellar management logic
│   ├── wineManager.js     # Wine instance management
│   ├── wineSearchManager.js     # Wine search and filtering
│   ├── wineSearchDetailCard.js  # Search result detail card (add to collection)
│   ├── wineDetailView.js  # Wine detail modal/view
│   ├── addWineManager.js  # Add wine functionality
│   ├── notificationOverlay.js   # Notification system
│   ├── styles.css         # Application styles
│   └── index.html         # Main HTML file
│
├── server/                # Backend Flask API server
│   ├── app.py             # Main Flask application
│   ├── models.py          # Data models (Cellar, Shelf, GlobalWineReference, UserWineReference, WineInstance)
│   ├── utils.py           # Utility functions
│   ├── cellars.py         # Cellar management endpoints
│   ├── wine_references.py # Wine reference endpoints
│   ├── user_wine_references.py # User wine reference endpoints
│   ├── wine_instances.py  # Wine instance endpoints
│   ├── vivino_search.py   # Vivino search integration
│   ├── dynamo/            # DynamoDB integration
│   │   ├── setup_tables.py    # Table creation scripts
│   │   ├── storage.py         # DynamoDB storage operations
│   │   ├── init_tables.py     # Table initialization
│   │   ├── populate.py        # Sample data population with Vivino image fetching
│   │   ├── clear_all_data.py  # Utility to clear all DynamoDB tables
│   │   └── browse_data.py     # Data browsing utilities
│   ├── data/              # Data serialization and static assets
│   │   ├── storage_serializers.py
│   │   └── wine_images/   # Downloaded wine label images (checked into source control)
│   └── tests/             # Server-side tests
│       ├── test_cellars.py
│       ├── test_wine_references.py
│       ├── test_user_wine_references.py
│       ├── test_wine_instances.py
│       └── conftest.py
│
├── docs/                  # Project documentation
│   ├── server_requirements.md  # Server API and data model specifications
│   └── client_requirements.md  # Client-side requirements and features
│
├── start_servers.sh       # Script to start both servers
├── start_dynamodb_local.sh # Script to start DynamoDB Local via Docker
├── start_dynamodb_ui.sh   # Script to start DynamoDB Admin UI
└── README.md              # This file
```

## Technology Stack

### Backend
- **Python 3.9+**: Core language
- **Flask**: Web framework for REST API
- **Flask-CORS**: Cross-origin resource sharing
- **Boto3**: AWS SDK for DynamoDB access
- **Pytest**: Testing framework
- **BeautifulSoup4**: Web scraping for Vivino integration
- **Requests**: HTTP library

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **HTML5/CSS3**: Modern web standards
- **Fetch API**: HTTP requests

### Data Storage
- **DynamoDB Local**: Local DynamoDB instance for development (runs via Docker on port 8001)
- **DynamoDB**: AWS DynamoDB for production (planned)

## Prerequisites

- Python 3.9 or higher
- pip3
- Docker Desktop (for DynamoDB Local)

## Getting Started

### 1. Install Python Dependencies

```bash
cd server
pip3 install -r requirements.txt
```

### 2. Start Docker Desktop

DynamoDB Local runs in a Docker container. Make sure Docker Desktop is running before proceeding.

### 3. Start DynamoDB Local

```bash
./start_dynamodb_local.sh
```

This starts DynamoDB Local in a Docker container mapped to `http://localhost:8001`.

**Optional**: Start the DynamoDB Admin UI:

```bash
./start_dynamodb_ui.sh
```

### 4. Initialize DynamoDB Tables

Create the required DynamoDB tables:

```bash
DYNAMODB_ENDPOINT=http://localhost:8001 PYTHONPATH=. python3 server/dynamo/setup_tables.py
```

### 5. Populate Sample Data (optional)

Populate the database with sample wines. The script will use any already-downloaded label images from `server/data/wine_images/` and attempt to download missing ones from Vivino:

```bash
DYNAMODB_ENDPOINT=http://localhost:8001 PYTHONPATH=. python3 server/dynamo/populate.py
```

### 6. Start the Servers

#### Option A: Use the convenience script (recommended)

```bash
DYNAMODB_ENDPOINT=http://localhost:8001 ./start_servers.sh
```

This script will:
- Start the Flask backend server on `http://localhost:5001`
- Start the frontend web server on `http://localhost:8000`

#### Option B: Start servers manually

**Start the Flask backend:**

```bash
DYNAMODB_ENDPOINT=http://localhost:8001 PYTHONPATH=. python3 server/app.py
```

The server will start on `http://localhost:5001`.

**Start the frontend web server:**

```bash
python3 webclient/dev_server.py webclient
```

### 7. Open the Application

```
http://localhost:8000
```

## Development

### Running Tests

#### Server-side Tests

```bash
PYTHONPATH=. pytest server/tests/
```

#### Client-side Tests

Open `webclient/tests/test_suite.html` in your browser.

### Server Configuration

**Environment Variables:**
- `DYNAMODB_ENDPOINT`: DynamoDB endpoint URL (default: `http://localhost:8000`; use `http://localhost:8001` when running via Docker)
- `DYNAMODB_REGION`: AWS region (default: `us-east-1`)
- `DEBUGPY`: Enable debugpy debugger (set to `1` to enable)
- `DEBUGPY_WAIT`: Wait for debugger to attach (set to `1` to enable)

### API Endpoints

- **Cellars**: `/cellars` (GET, POST, PUT, DELETE)
- **Wine References**: `/wine-references` (GET, POST, PUT, DELETE)
- **User Wine References**: `/user-wine-references` (GET, POST, PUT, DELETE)
- **Wine Instances**: `/wine-instances` (GET, POST, PUT, DELETE)
- **Wine Instance Location**: `/wine-instances/<id>/location` (PUT)
- **Wine Instance Coravin**: `/wine-instances/<id>/coravin` (PUT)
- **Wine Instance Consume**: `/wine-instances/<id>/consume` (PUT)
- **Vivino Search**: `/vivino/search` (GET)
- **Wine Images**: `/wine-images/<filename>` (GET) — serves locally stored label images

See [docs/server_requirements.md](docs/server_requirements.md) for complete API documentation.

## Data Model

### Core Entities

1. **Cellar**: Container for wine storage with configurable shelves
2. **Shelf**: Storage unit within a cellar (single or double-sided)
3. **GlobalWineReference**: Shared wine information (name, type, vintage, producer, etc.)
4. **UserWineReference**: Per-user personal data (ratings, tasting notes) linked to a GlobalWineReference
5. **WineInstance**: Physical bottle instance with location, purchase info, consumption status

### Key Concepts

- **Location Tracking**: WineInstance location is tracked by storing the instance in a Cellar's Shelf structure, not on the instance itself
- **Unshelved Wines**: WineInstances not found in any cellar are considered "unshelved"
- **Version Tracking**: All entities include version numbers for conflict resolution
- **Drink By Date**: Stored on WineInstance as an ISO 8601 date; only the year is displayed in the UI
- **Label Images**: Stored locally in `server/data/wine_images/` and served at `/wine-images/<filename>`

See [docs/server_requirements.md](docs/server_requirements.md) for detailed data model specifications.

## Documentation

- **[Server Requirements](docs/server_requirements.md)**: Complete server API and data model documentation
- **[Client Requirements](docs/client_requirements.md)**: Client-side features and requirements

## Troubleshooting

### Server won't start

- Ensure Docker Desktop is running and DynamoDB Local container is started (`./start_dynamodb_local.sh`)
- Check that all Python dependencies are installed
- Verify DynamoDB tables have been created with `DYNAMODB_ENDPOINT=http://localhost:8001`

### DynamoDB connection errors

- The DynamoDB Local Docker container maps to port **8001** on the host (not 8000)
- Always set `DYNAMODB_ENDPOINT=http://localhost:8001` when running locally
- Verify the container is running: `docker ps | grep dynamodb-local`

### Connection errors

- Ensure the Flask server is running on port 5001
- Check browser console for CORS errors
- Verify the API endpoint URL in `webclient/api.js`

## Contributing

_Add contribution guidelines here._

## License

_Add license information here._
