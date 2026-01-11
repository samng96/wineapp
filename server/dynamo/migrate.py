"""Migrate data from JSON files to DynamoDB"""
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError
from server.dynamo.storage import CELLARS_TABLE, WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE

# DynamoDB configuration
DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
DYNAMODB_REGION = os.environ.get('DYNAMODB_REGION', 'us-east-1')

# File paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CELLARS_FILE = os.path.join(DATA_DIR, 'cellars.json')
WINE_REFERENCES_FILE = os.path.join(DATA_DIR, 'wine-references.json')
WINE_INSTANCES_FILE = os.path.join(DATA_DIR, 'wine-instances.json')


def get_dynamodb_resource():
    """Get DynamoDB resource"""
    if DYNAMODB_ENDPOINT:
        return boto3.resource(
            'dynamodb',
            endpoint_url=DYNAMODB_ENDPOINT,
            region_name=DYNAMODB_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        return boto3.resource('dynamodb', region_name=DYNAMODB_REGION)


def migrate_table(table_name, file_path, item_key='id'):
    """Migrate data from a JSON file to a DynamoDB table"""
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist. Skipping...")
        return 0
    
    print(f"Migrating {file_path} to {table_name}...")
    
    # Load data from JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if not data:
        print(f"  No data to migrate")
        return 0
    
    # Get DynamoDB table
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(table_name)
    
    # Write data to DynamoDB
    count = 0
    with table.batch_writer() as batch:
        for item in data:
            batch.put_item(Item=item)
            count += 1
    
    print(f"  Migrated {count} items")
    return count


def main():
    """Migrate all data from JSON files to DynamoDB"""
    print("Migrating data from JSON files to DynamoDB...")
    print(f"Endpoint: {DYNAMODB_ENDPOINT}")
    print()
    
    # Check if DynamoDB is accessible
    try:
        client = boto3.client(
            'dynamodb',
            endpoint_url=DYNAMODB_ENDPOINT,
            region_name=DYNAMODB_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        client.list_tables()
    except Exception as e:
        print(f"Error: Cannot connect to DynamoDB at {DYNAMODB_ENDPOINT}")
        print(f"  {e}")
        print()
        print("Make sure DynamoDB Local is running:")
        print("  ./start_dynamodb_local.sh")
        sys.exit(1)
    
    # Migrate each table
    total = 0
    total += migrate_table(CELLARS_TABLE, CELLARS_FILE)
    total += migrate_table(WINE_REFERENCES_TABLE, WINE_REFERENCES_FILE)
    total += migrate_table(WINE_INSTANCES_TABLE, WINE_INSTANCES_FILE)
    
    print()
    print(f"Migration complete! Migrated {total} total items.")


if __name__ == '__main__':
    main()
