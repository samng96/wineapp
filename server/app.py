from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Allows frontend to talk to this server

# Path to our data file
DATA_FILE = 'wines.json'

def load_wines():
    """Load wines from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_wines(wines):
    """Save wines to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(wines, f, indent=2)

@app.route('/wines', methods=['GET'])
def get_wines():
    """Get all wines"""
    wines = load_wines()
    return jsonify(wines)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
