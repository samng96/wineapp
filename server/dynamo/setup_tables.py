"""Create DynamoDB tables for WineApp"""
import os
import boto3
from botocore.exceptions import ClientError
from server.dynamo.storage import CELLARS_TABLE, WINE_REFERENCES_TABLE, USER_WINE_REFERENCES_TABLE, WINE_INSTANCES_TABLE

# DynamoDB configuration
DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
DYNAMODB_REGION = os.environ.get('DYNAMODB_REGION', 'us-east-1')


def get_dynamodb_client():
    """Get DynamoDB client"""
    from botocore.config import Config
    # Configure shorter timeouts to prevent hanging when DynamoDB isn't available
    config = Config(
        connect_timeout=2,
        read_timeout=2,
        retries={'max_attempts': 1}
    )
    if DYNAMODB_ENDPOINT:
        return boto3.client(
            'dynamodb',
            endpoint_url=DYNAMODB_ENDPOINT,
            region_name=DYNAMODB_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy',
            config=config
        )
    else:
        return boto3.client('dynamodb', region_name=DYNAMODB_REGION, config=config)


def create_table(table_name, key_schema, attribute_definitions):
    """Create a DynamoDB table"""
    client = get_dynamodb_client()
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode='PAY_PER_REQUEST'  # On-demand billing for DynamoDB Local
        )
        print(f"Created table: {table_name}")
        # Wait for table to be active
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"Table {table_name} is now active")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists")
            return False
        else:
            print(f"Error creating table {table_name}: {e}")
            raise


def main():
    """Create all DynamoDB tables"""
    print("Creating DynamoDB tables...")
    print(f"Endpoint: {DYNAMODB_ENDPOINT}")
    print()
    
    # Create cellars table
    create_table(
        CELLARS_TABLE,
        [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ]
    )
    
    # Create wine references table
    create_table(
        WINE_REFERENCES_TABLE,
        [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ]
    )
    
    # Create user wine references table
    create_table(
        USER_WINE_REFERENCES_TABLE,
        [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ]
    )

    # Create wine instances table
    create_table(
        WINE_INSTANCES_TABLE,
        [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ]
    )
    
    print()
    print("All tables created successfully!")


if __name__ == '__main__':
    main()
