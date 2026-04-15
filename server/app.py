"""Main Flask application"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from server.dynamo.init_tables import init_dynamodb_tables
from server.cellars import cellars_bp
from server.wine_references import wine_references_bp, get_all_wine_references
from server.user_wine_references import user_wine_references_bp
from server.wine_instances import wine_instances_bp

app = Flask(__name__)
CORS(app)  # Allows frontend to talk to this server

WINE_IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'data', 'wine_images')

@app.route('/wine-images/<path:filename>')
def serve_wine_image(filename):
    return send_from_directory(WINE_IMAGES_DIR, filename)

# Register blueprints
app.register_blueprint(cellars_bp)
app.register_blueprint(wine_references_bp)
app.register_blueprint(user_wine_references_bp)
app.register_blueprint(wine_instances_bp)

# Initialize DynamoDB tables on startup (checks if they exist)
print("Initializing DynamoDB tables...")
try:
    init_dynamodb_tables()
    print("DynamoDB initialization complete.")
except Exception as e:
    print(f"Warning: DynamoDB initialization failed: {e}")
    print("Server will continue, but DynamoDB operations may fail.")

# Load wine references into the global registry on startup
# This must happen before loading wine instances, which reference wine references
# The deserialize_wine_reference function automatically registers references
print("Loading wine references into registry on startup...")
try:
    loaded_refs = get_all_wine_references()
    print(f"Loaded {len(loaded_refs)} wine references into registry")
except Exception as e:
    print(f"Warning: Could not load wine references on startup: {e}")
    print("Server will continue, but wine references will be loaded on-demand.")

if __name__ == '__main__':
    import os
    # Enable debugpy if DEBUGPY environment variable is set
    if os.environ.get('DEBUGPY'):
        import debugpy
        debugpy.listen(('0.0.0.0', 5678))
        print("Debugpy listening on port 5678. Attach debugger now.")
        # Optionally wait for debugger to attach before continuing
        if os.environ.get('DEBUGPY_WAIT'):
            debugpy.wait_for_client()
            print("Debugger attached!")
    
    app.run(debug=True, port=5001, host='127.0.0.1', use_reloader=False)
