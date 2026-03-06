# WineApp

A client-server application for managing a personal wine inventory. Track, organize, and manage your wine collection with support for multiple cellars, wine references, tasting notes, and bottle tracking.

## Features

- **Cellar Management**: Create and manage multiple cellars with customizable shelves (single or double-sided)
- **Wine Tracking**: Track individual wine bottles with purchase dates, prices, and consumption status
- **Wine References**: Maintain a global database of wine information (name, vintage, producer, varietals, region, country)
- **Personal Notes**: Add personal ratings and tasting notes to wines
- **Unshelved Wines**: Automatically track wines that haven't been placed in a cellar yet
- **Search & Filter**: Powerful search and filtering capabilities by type, varietal, country, consumption status, and more
- **Wine Details**: View detailed information about wines including location, notes, and related bottles
- **Coravin Support**: Track wines opened with Coravin
- **Vivino Integration**: Search and import wine information from Vivino

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
│   ├── wineSearchManager.js # Wine search and filtering
│   ├── wineDetailView.js  # Wine detail modal/view
│   ├── addWineManager.js  # Add wine functionality
│   ├── notificationOverlay.js # Notification system
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
│   │   └── browse_data.py     # Data browsing utilities
│   ├── data/              # Data serialization
│   │   └── storage_serializers.py
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
├── start_dynamodb_local.sh # Script to start DynamoDB Local
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
- **DynamoDB Local**: Local DynamoDB instance for development
- **DynamoDB**: AWS DynamoDB for production (planned)

## Prerequisites

- Python 3.9 or higher
- pip3
- Java Runtime Environment (JRE) for DynamoDB Local
- AWS CLI (optional, for DynamoDB operations)

## Getting Started

### 1. Install Python Dependencies

```bash
cd server
pip3 install -r requirements.txt
```

### 2. Start DynamoDB Local

DynamoDB Local is required for data persistence. Start it using the provided script:

```bash
./start_dynamodb_local.sh
```

This will start DynamoDB Local on `http://localhost:8000`.

**Optional**: Start the DynamoDB Admin UI for easier data browsing:

```bash
./start_dynamodb_ui.sh
```

This will start the admin UI on `http://localhost:8001`.

### 3. Initialize DynamoDB Tables

Create the required DynamoDB tables:

```bash
cd server
PYTHONPATH=.. python3 dynamo/setup_tables.py
```

### 4. Start the Servers

#### Option A: Use the convenience script (recommended)

```bash
./start_servers.sh
```

This script will:
- Start the Flask backend server on `http://localhost:5001`
- Start the frontend web server on `http://localhost:8000`

#### Option B: Start servers manually

**Start the Flask backend:**

```bash
cd server
PYTHONPATH=.. python3 app.py
```

The server will start on `http://localhost:5001` (port 5001 is used instead of 5000 to avoid conflicts with macOS AirPlay).

**Start the frontend web server:**

In a separate terminal:

```bash
cd webclient
python3 dev_server.py webclient
```

Or use Python's built-in server:

```bash
cd webclient
python3 -m http.server 8000
```

### 5. Open the Application

Open your web browser and navigate to:

```
http://localhost:8000
```

## Development

### Running Tests

#### Server-side Tests

```bash
cd server
PYTHONPATH=.. pytest tests/
```

Run specific test files:

```bash
PYTHONPATH=.. pytest tests/test_cellars.py
PYTHONPATH=.. pytest tests/test_wine_instances.py
```

#### Client-side Tests

Open `webclient/tests/test_suite.html` in your browser to run client-side tests.

### Server Configuration

The server runs in debug mode by default and will automatically reload when code changes are made.

**Environment Variables:**
- `DYNAMODB_ENDPOINT`: DynamoDB endpoint URL (default: `http://localhost:8000`)
- `DYNAMODB_REGION`: AWS region (default: `us-east-1`)
- `DEBUGPY`: Enable debugpy debugger (set to `1` to enable)
- `DEBUGPY_WAIT`: Wait for debugger to attach (set to `1` to enable)

### API Endpoints

The server provides RESTful API endpoints for:

- **Cellars**: `/cellars` (GET, POST, PUT, DELETE)
- **Wine References**: `/wine-references` (GET, POST, PUT, DELETE)
- **User Wine References**: `/user-wine-references` (GET, POST, PUT, DELETE)
- **Wine Instances**: `/wine-instances` (GET, POST, PUT, DELETE)
- **Wine Instance Location**: `/wine-instances/<id>/location` (PUT)
- **Wine Instance Coravin**: `/wine-instances/<id>/coravin` (PUT)
- **Wine Instance Consume**: `/wine-instances/<id>/consume` (PUT)
- **Vivino Search**: `/vivino-search` (GET)

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

See [docs/server_requirements.md](docs/server_requirements.md) for detailed data model specifications.

## Documentation

- **[Server Requirements](docs/server_requirements.md)**: Complete server API and data model documentation
- **[Client Requirements](docs/client_requirements.md)**: Client-side features and requirements

## Troubleshooting

### Server won't start

- Ensure DynamoDB Local is running on port 8000
- Check that all Python dependencies are installed
- Verify that DynamoDB tables have been created

### Connection errors

- Ensure the Flask server is running on port 5001
- Check browser console for CORS errors
- Verify the API endpoint URL in `webclient/api.js`

### DynamoDB connection errors

- Ensure DynamoDB Local is running: `./start_dynamodb_local.sh`
- Check that tables exist: `PYTHONPATH=.. python3 server/dynamo/setup_tables.py`
- Verify the endpoint URL matches your DynamoDB Local configuration

## Contributing

_Add contribution guidelines here._

## License

_Add license information here._
