#!/bin/bash

# Stop DynamoDB Local Docker container

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

if docker ps --format '{{.Names}}' | grep -q "^dynamodb-local$"; then
    echo "Stopping DynamoDB Local..."
    docker stop dynamodb-local
    echo "DynamoDB Local stopped."
else
    echo "DynamoDB Local is not running."
fi

# Optionally remove the container
if docker ps -a --format '{{.Names}}' | grep -q "^dynamodb-local$"; then
    read -p "Remove container? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rm dynamodb-local
        echo "Container removed."
    fi
fi
