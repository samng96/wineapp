"""DynamoDB storage adapter for WineApp"""
import os
import json
from typing import List, Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# DynamoDB configuration
DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
DYNAMODB_REGION = os.environ.get('DYNAMODB_REGION', 'us-east-1')

# Table names
CELLARS_TABLE = 'wineapp-cellars'
WINE_REFERENCES_TABLE = 'wineapp-wine-references'
WINE_INSTANCES_TABLE = 'wineapp-wine-instances'

# Initialize DynamoDB resource
def get_dynamodb_resource():
    """Get DynamoDB resource, using local endpoint if specified"""
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


def get_dynamodb_client():
    """Get DynamoDB client, using local endpoint if specified"""
    if DYNAMODB_ENDPOINT:
        return boto3.client(
            'dynamodb',
            endpoint_url=DYNAMODB_ENDPOINT,
            region_name=DYNAMODB_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        return boto3.client('dynamodb', region_name=DYNAMODB_REGION)


# Cellar storage functions
def load_cellars() -> List[Dict[str, Any]]:
    """Load all cellars from DynamoDB as serialized dictionaries"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(CELLARS_TABLE)
    
    try:
        response = table.scan()
        return response.get('Items', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return []
        raise


def save_cellars(cellars: List[Dict[str, Any]]):
    """Save cellars to DynamoDB (accepts serialized dictionaries)"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(CELLARS_TABLE)
    
    # Get all existing cellar IDs
    existing = load_cellars()
    existing_ids = {item['id'] for item in existing}
    new_ids = {c['id'] for c in cellars}
    
    # Delete cellars that are no longer in the new list
    for item in existing:
        if item['id'] not in new_ids:
            table.delete_item(Key={'id': item['id']})
    
    # Put all cellars (DynamoDB put overwrites existing items)
    with table.batch_writer() as batch:
        for cellar in cellars:
            # Convert any sets/lists to proper types for DynamoDB
            batch.put_item(Item=_prepare_item(cellar))


def get_cellar_by_id(cellar_id: str) -> Optional[Dict[str, Any]]:
    """Get a single cellar by ID from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(CELLARS_TABLE)
    
    try:
        response = table.get_item(Key={'id': cellar_id})
        return response.get('Item')
    except ClientError:
        return None


def update_cellar(cellar: Dict[str, Any]):
    """Update a single cellar in DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(CELLARS_TABLE)
    
    table.put_item(Item=_prepare_item(cellar))


def delete_cellar(cellar_id: str):
    """Delete a cellar from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(CELLARS_TABLE)
    
    table.delete_item(Key={'id': cellar_id})


# Wine Reference storage functions
def load_wine_references() -> List[Dict[str, Any]]:
    """Load all wine references from DynamoDB as serialized dictionaries"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_REFERENCES_TABLE)
    
    try:
        response = table.scan()
        return response.get('Items', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return []
        raise


def save_wine_references(references: List[Dict[str, Any]]):
    """Save wine references to DynamoDB (accepts serialized dictionaries)"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_REFERENCES_TABLE)
    
    # Get all existing reference IDs
    existing = load_wine_references()
    existing_ids = {item['id'] for item in existing}
    new_ids = {r['id'] for r in references}
    
    # Delete references that are no longer in the new list
    for item in existing:
        if item['id'] not in new_ids:
            table.delete_item(Key={'id': item['id']})
    
    # Put all references
    with table.batch_writer() as batch:
        for reference in references:
            batch.put_item(Item=_prepare_item(reference))


def get_wine_reference_by_id(reference_id: str) -> Optional[Dict[str, Any]]:
    """Get a single wine reference by ID from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_REFERENCES_TABLE)
    
    try:
        response = table.get_item(Key={'id': reference_id})
        return response.get('Item')
    except ClientError:
        return None


def update_wine_reference(reference: Dict[str, Any]):
    """Update a single wine reference in DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_REFERENCES_TABLE)
    
    table.put_item(Item=_prepare_item(reference))


def delete_wine_reference(reference_id: str):
    """Delete a wine reference from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_REFERENCES_TABLE)
    
    table.delete_item(Key={'id': reference_id})


# Wine Instance storage functions
def load_wine_instances() -> List[Dict[str, Any]]:
    """Load all wine instances from DynamoDB as serialized dictionaries"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_INSTANCES_TABLE)
    
    try:
        response = table.scan()
        return response.get('Items', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return []
        raise


def save_wine_instances(instances: List[Dict[str, Any]]):
    """Save wine instances to DynamoDB (accepts serialized dictionaries)"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_INSTANCES_TABLE)
    
    # Get all existing instance IDs
    existing = load_wine_instances()
    existing_ids = {item['id'] for item in existing}
    new_ids = {i['id'] for i in instances}
    
    # Delete instances that are no longer in the new list
    for item in existing:
        if item['id'] not in new_ids:
            table.delete_item(Key={'id': item['id']})
    
    # Put all instances
    with table.batch_writer() as batch:
        for instance in instances:
            batch.put_item(Item=_prepare_item(instance))


def get_wine_instance_by_id(instance_id: str) -> Optional[Dict[str, Any]]:
    """Get a single wine instance by ID from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_INSTANCES_TABLE)
    
    try:
        response = table.get_item(Key={'id': instance_id})
        return response.get('Item')
    except ClientError:
        return None


def update_wine_instance(instance: Dict[str, Any]):
    """Update a single wine instance in DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_INSTANCES_TABLE)
    
    table.put_item(Item=_prepare_item(instance))


def delete_wine_instance(instance_id: str):
    """Delete a wine instance from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(WINE_INSTANCES_TABLE)
    
    table.delete_item(Key={'id': instance_id})


# Helper function to prepare items for DynamoDB
def _prepare_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a dictionary for DynamoDB storage.
    DynamoDB requires specific types - converts floats to Decimals.
    """
    from decimal import Decimal
    
    def convert_value(value):
        """Recursively convert floats to Decimals"""
        if isinstance(value, float):
            return Decimal(str(value))
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert_value(v) for v in value]
        else:
            return value
    
    return convert_value(item)
