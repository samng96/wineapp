# WineApp

A client-server application for managing a personal wine inventory.

## Project Structure

```
WineApp/
├── client/          # Frontend application (to be implemented)
├── docs/            # Project documentation
│   └── requirements.md  # Functional and technical requirements
├── server/          # Backend Flask API server
│   ├── app.py       # Main Flask application
│   ├── wines.json   # Wine data storage (JSON file)
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

### API Endpoints

- `GET /wines` - Retrieve all wines from the inventory
  - Returns: JSON array of wine objects
  - Example: `curl http://localhost:5001/wines`

## Usage

The server runs in debug mode and will automatically reload when code changes are made. The wine data is stored in `server/wines.json` as a JSON file.

## Documentation

See the [requirements document](docs/requirements.md) for detailed functional and technical requirements.

## Contributing

_Add contribution guidelines here._

## License

_Add license information here._
