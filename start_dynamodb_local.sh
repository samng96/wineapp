#!/bin/bash

# Start DynamoDB Local in a Docker container

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker Desktop first."
    echo "See DOCKER_SETUP.md for instructions."
    exit 1
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo "Error: Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

# Check if container already exists and is running
if docker ps -a --format '{{.Names}}' | grep -q "^dynamodb-local$"; then
    if docker ps --format '{{.Names}}' | grep -q "^dynamodb-local$"; then
        echo "DynamoDB Local is already running."
        exit 0
    else
        echo "Starting existing DynamoDB Local container..."
        docker start dynamodb-local
        exit 0
    fi
fi

# Start new container
echo "Starting DynamoDB Local on port 8000..."
docker run -d \
    -p 8000:8000 \
    --name dynamodb-local \
    amazon/dynamodb-local

if [ $? -eq 0 ]; then
    echo "DynamoDB Local started successfully!"
    echo "Endpoint: http://localhost:8000"
    echo ""
    echo "To stop: ./stop_dynamodb_local.sh"
else
    echo "Failed to start DynamoDB Local"
    exit 1
fi
