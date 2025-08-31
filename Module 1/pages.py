"""Control website pages with Flask blueprint"""

from flask import Blueprint, render_template

pages = Blueprint("pages", __name__, static_folder="static", template_folder="templates")

# Define homepage
@pages.route("/")
def home():
    return render_template("home.html")

# Define contact info page
@pages.route("/contact")
def contact():
    return render_template("contact.html")

# Define projects listing page
@pages.route("/projects")
def projects():
    return render_template("projects.html")
