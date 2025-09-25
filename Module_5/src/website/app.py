"""
This module sets up a Flask app, registers blueprints, and starts the server.
It is intended to be run as the main module.

Usage:
    python main.py

Environment Variables:
    PORT (optional): The port number on which to run the Flask app. Defaults to 5000.

Notes:
    - This app is designed for use with Replit, which requires port 5000.
    - The pages blueprint must be defined in the pages module.
"""

import os
from flask import Flask
from pages_bp import pages

# Instantiate app, create key to let us use Flash statements.
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Call blueprint from pages module.
app.register_blueprint(pages)

# Run web application.
if __name__ == "__main__":
    # Get port from environment or default to 5000.
    port = int(os.environ.get("PORT", 5000))
    # Configuration for Replit preview (must use port 5000).
    app.run(
        host="0.0.0.0",
        port=5000,  # Has to be 5000 for Replit
        debug=False,  # Disable debug mode for webview
        threaded=True)
