"""Script to clear all data from DynamoDB tables"""
import os
import boto3
from server.dynamo.storage import (
    get_dynamodb_resource,
    CELLARS_TABLE, WINE_REFERENCES_TABLE, USER_WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE
)

def clear_all_tables():
    """Clear all items from DynamoDB tables"""
    dynamodb = get_dynamodb_resource()
    
    for table_name in [CELLARS_TABLE, WINE_REFERENCES_TABLE, USER_WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE]:
        table = dynamodb.Table(table_name)
        
        # Scan and delete all items
        response = table.scan()
        items = response.get('Items', [])
        
        print(f"Clearing {table_name}... Found {len(items)} items")
        
        if items:
            with table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={'id': item['id']})
            print(f"  Deleted {len(items)} items from {table_name}")
        else:
            print(f"  No items to delete from {table_name}")

if __name__ == '__main__':
    print("Clearing all data from DynamoDB tables...")
    clear_all_tables()
    print("Done!")
