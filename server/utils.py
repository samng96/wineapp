"""Utility functions for WineApp server"""
import os
import uuid
from datetime import datetime

# File paths for JSON storage
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CELLARS_FILE = os.path.join(DATA_DIR, 'cellars.json')
WINE_REFERENCES_FILE = os.path.join(DATA_DIR, 'wine-references.json')
WINE_INSTANCES_FILE = os.path.join(DATA_DIR, 'wine-instances.json')


def init_data_files():
    """Initialize data directory and JSON files if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Only create files if not in testing mode
    if os.environ.get('FLASK_ENV') != 'testing':
        for filepath in [CELLARS_FILE, WINE_REFERENCES_FILE, WINE_INSTANCES_FILE]:
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    import json
                    json.dump([], f, indent=2)


def generate_id() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current timestamp in ISO 8601 format"""
    return datetime.utcnow().isoformat() + 'Z'


