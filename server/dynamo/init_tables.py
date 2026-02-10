"""Initialize DynamoDB tables on startup"""
import os
from server.dynamo.setup_tables import get_dynamodb_client
from server.dynamo.storage import CELLARS_TABLE, WINE_REFERENCES_TABLE, USER_WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE


def init_dynamodb_tables():
    """Initialize DynamoDB tables if they don't exist"""
    client = get_dynamodb_client()
    
    # Check if tables exist
    try:
        tables = client.list_tables()['TableNames']
        all_tables_exist = all(
            table in tables 
            for table in [CELLARS_TABLE, WINE_REFERENCES_TABLE, USER_WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE]
        )
        if not all_tables_exist:
            print("DynamoDB tables not found. Please run: PYTHONPATH=. python server/dynamo/setup_tables.py")
    except Exception as e:
        print(f"Error checking DynamoDB tables: {e}")
        print("Make sure DynamoDB Local is running: ./start_dynamodb_local.sh")
