from flask import Flask, render_template
from pages import pages

app = Flask(__name__)

app.register_blueprint(pages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)