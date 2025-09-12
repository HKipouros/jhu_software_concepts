""" Creates Flask object and runs web application"""

import os
import sys
from flask import Flask

# Add current directory to Python path to ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pages import pages

# instantiate app
app = Flask(__name__)

# No special config needed

# call blueprint from pages module
app.register_blueprint(pages)

# run web application
if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    # Configuration for Replit preview (must use port 5000)
    app.run(
        host="0.0.0.0",
        port=5000,  # Has to be 5000 for Replit
        debug=False,  # Disable debug mode for webview
        threaded=True)
