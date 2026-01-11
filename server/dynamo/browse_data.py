#!/usr/bin/env python3
"""
Browse and display DynamoDB Local data
Run this script to view all data in your DynamoDB tables
"""
import os
import sys
import json
from decimal import Decimal
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from server.dynamo.storage import (
    load_cellars,
    load_wine_references,
    load_wine_instances,
    CELLARS_TABLE,
    WINE_REFERENCES_TABLE,
    WINE_INSTANCES_TABLE
)

class DecimalEncoder(json.JSONEncoder):
    """Helper to convert Decimal to string for JSON encoding"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def format_item(item):
    """Format a DynamoDB item for display"""
    # Convert Decimal to float for better display
    formatted = {}
    for key, value in item.items():
        if isinstance(value, Decimal):
            formatted[key] = float(value)
        elif isinstance(value, dict):
            formatted[key] = format_item(value)
        elif isinstance(value, list):
            formatted[key] = [format_item(v) if isinstance(v, dict) else float(v) if isinstance(v, Decimal) else v for v in value]
        else:
            formatted[key] = value
    return formatted

def browse_table(table_name, load_func, label):
    """Browse a single table"""
    print(f"\n{'='*80}")
    print(f"{label} ({table_name})")
    print(f"{'='*80}")
    
    try:
        items = load_func()
        if not items:
            print(f"No {label.lower()} found.")
            return
        
        print(f"\nTotal count: {len(items)}\n")
        
        for i, item in enumerate(items, 1):
            print(f"\n[{i}/{len(items)}] {item.get('id', 'N/A')}")
            print("-" * 80)
            formatted = format_item(item)
            print(json.dumps(formatted, indent=2, cls=DecimalEncoder))
    
    except Exception as e:
        print(f"Error loading {label.lower()}: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to browse all tables"""
    print("DynamoDB Local Data Browser")
    print("=" * 80)
    print(f"Endpoint: {os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Browse all tables
    browse_table(CELLARS_TABLE, load_cellars, "Cellars")
    browse_table(WINE_REFERENCES_TABLE, load_wine_references, "Wine References")
    browse_table(WINE_INSTANCES_TABLE, load_wine_instances, "Wine Instances")
    
    print(f"\n{'='*80}")
    print("Browse complete!")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
