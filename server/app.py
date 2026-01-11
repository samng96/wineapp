"""Main Flask application"""
from flask import Flask
from flask_cors import CORS
from server.dynamo.init_tables import init_dynamodb_tables
from server.cellars import cellars_bp
from server.wine_references import wine_references_bp, get_all_wine_references
from server.wine_instances import wine_instances_bp

app = Flask(__name__)
CORS(app)  # Allows frontend to talk to this server

# Register blueprints
app.register_blueprint(cellars_bp)
app.register_blueprint(wine_references_bp)
app.register_blueprint(wine_instances_bp)

# Initialize DynamoDB tables on startup (checks if they exist)
init_dynamodb_tables()

# Load wine references into the global registry on startup
# This must happen before loading wine instances, which reference wine references
# The deserialize_wine_reference function automatically registers references
print("Loading wine references into registry on startup...")
loaded_refs = get_all_wine_references()
print(f"Loaded {len(loaded_refs)} wine references into registry")

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
