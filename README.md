# WineApp

A client-server application for managing a personal wine inventory.

## Project Structure

```
WineApp/
├── webclient/       # Web-based frontend application
├── docs/            # Project documentation
│   └── requirements.md  # Functional and technical requirements
├── server/          # Backend Flask API server
│   ├── app.py       # Main Flask application
│   ├── tests/       # Server-side tests
│   ├── cellars.json # Cellar data storage
│   ├── wine-references.json  # Wine reference data storage
│   ├── wine-instances.json   # Wine instance data storage
│   └── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip3

### Server Setup

1. Navigate to the server directory:
   ```bash
   cd server
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python3 app.py
   ```

The server will start on `http://localhost:5001` (port 5001 is used instead of 5000 to avoid conflicts with macOS AirPlay).

### Web Client Setup

1. Start the Flask server (see Server Setup above)

2. Open the web client:
   ```bash
   cd webclient
   python3 -m http.server 8000
   ```

3. Open `http://localhost:8000` in your web browser

The web client supports offline functionality and will automatically sync with the server when online.

### API Endpoints

See the [requirements document](docs/requirements.md) for the complete API endpoint documentation.

## Usage

The server runs in debug mode and will automatically reload when code changes are made. The wine data is stored in JSON files in the `server/` directory:
- `cellars.json` - Cellar data
- `wine-references.json` - Wine reference data
- `wine-instances.json` - Wine instance data

## Documentation

See the [requirements document](docs/requirements.md) for detailed functional and technical requirements.

## Contributing

_Add contribution guidelines here._

## License

_Add license information here._
