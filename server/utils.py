"""Utility functions shared across modules"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict

# Paths to data files
CELLARS_FILE = 'cellars.json'
WINE_REFERENCES_FILE = 'wine-references.json'
WINE_INSTANCES_FILE = 'wine-instances.json'

def init_data_files():
    """Initialize data files with empty arrays if they don't exist"""
    for file in [CELLARS_FILE, WINE_REFERENCES_FILE, WINE_INSTANCES_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump([], f, indent=2)

def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + 'Z'

def add_version_and_timestamps(entity: Dict, is_new: bool = True) -> Dict:
    """Add version and timestamps to an entity"""
    if is_new:
        entity['version'] = 1
        entity['createdAt'] = get_current_timestamp()
    else:
        entity['version'] = entity.get('version', 1) + 1
    entity['updatedAt'] = get_current_timestamp()
    return entity
