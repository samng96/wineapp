"""Utility functions for WineApp server"""
import uuid
from datetime import datetime


def generate_id() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current timestamp in ISO 8601 format"""
    return datetime.utcnow().isoformat() + 'Z'


