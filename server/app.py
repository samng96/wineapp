"""Main Flask application"""
from flask import Flask
from flask_cors import CORS
from server.utils import init_data_files
from server.cellars import cellars_bp
from server.wine_references import wine_references_bp
from server.wine_instances import wine_instances_bp

app = Flask(__name__)
CORS(app)  # Allows frontend to talk to this server

# Register blueprints
app.register_blueprint(cellars_bp)
app.register_blueprint(wine_references_bp)
app.register_blueprint(wine_instances_bp)

# Initialize data files on startup
init_data_files()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
