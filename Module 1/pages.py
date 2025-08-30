from flask import Blueprint, render_template

pages = Blueprint("pages", __name__, static_folder="static", template_folder="templates")

@pages.route("/")
def home():
    return render_template("home.html")

@pages.route("/contact")
def contact():
    return render_template("contact.html")

@pages.route("/projects")
def projects():
    return render_template("projects.html")