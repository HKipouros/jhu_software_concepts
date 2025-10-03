"""
This module sets up a Flask app, registers blueprints, and starts the server.
It is intended to be run as the main module.

Usage:
    python src/website/app.py

Environment Variables:
    PORT (optional): The port number on which to run the Flask app. Defaults to 5000.
    HOST (optional): The host address to bind to. Defaults to 0.0.0.0 (all interfaces).
    FLASK_DEBUG (optional): Enable debug mode. Defaults to False.
    DATABASE_URL (required): PostgreSQL database connection string.

Notes:
    - Defaults to 0.0.0.0 for cloud deployment and network access
    - For local-only access on Windows/Mac, set HOST=127.0.0.1 in your .env file
"""

import os
from flask import Flask
from pages_bp import pages

# Instantiate app, create key to let us use Flash statements.
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Call blueprint from pages module.
app.register_blueprint(pages)

# Run web application.
if __name__ == "__main__":
    # Get configuration from environment variables with sensible defaults
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True)
