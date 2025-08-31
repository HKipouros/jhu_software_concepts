""" Creates Flask object and runs web application"""

from flask import Flask
from pages import pages

# instantiate app
app = Flask(__name__)

# call blueprint from pages module
app.register_blueprint(pages)

# run web application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
