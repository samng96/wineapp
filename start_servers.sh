#!/bin/bash

# Start Wine App Servers
# This script starts both the Flask backend and the frontend web server

echo "Starting Wine App servers..."
echo ""

# Check if Flask server is already running
if lsof -ti:5001 > /dev/null; then
    echo "⚠️  Flask server already running on port 5001"
else
    echo "Starting Flask backend server on port 5001..."
    cd "$(dirname "$0")/server"
    python3 app.py &
    FLASK_PID=$!
    echo "Flask server started (PID: $FLASK_PID)"
    echo ""
fi

# Check if web server is already running
if lsof -ti:8000 > /dev/null; then
    echo "⚠️  Web server already running on port 8000"
else
    echo "Starting frontend web server on port 8000..."
    cd "$(dirname "$0")"
    python3 webclient/dev_server.py webclient &
    WEB_PID=$!
    echo "Web server started (PID: $WEB_PID) - with no-cache headers for development"
    echo ""
fi

echo "✅ Servers should be running!"
echo ""
echo "Open your browser and go to: http://localhost:8000"
echo ""
echo "To stop the servers, press Ctrl+C or run:"
echo "  kill $FLASK_PID $WEB_PID"

# Wait for user to stop
wait
