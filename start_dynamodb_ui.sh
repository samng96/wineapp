#!/bin/bash

# Start DynamoDB Local Web UI

echo "Starting DynamoDB Local Web UI..."
echo ""

# Check if DynamoDB Local is running
if ! docker ps --format '{{.Names}}' | grep -q "^dynamodb-local$"; then
    echo "⚠️  DynamoDB Local is not running."
    echo "Please start DynamoDB Local first: ./start_dynamodb_local.sh"
    exit 1
fi

cd "$(dirname "$0")"
PYTHONPATH="$(dirname "$0")" python3 server/dynamo/ui.py
