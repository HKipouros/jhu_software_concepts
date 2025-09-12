"""Control website pages with Flask blueprint"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from query_data import run_queries
from flask import Blueprint, render_template, request, redirect, url_for

pages = Blueprint("pages",
                  __name__,
                  static_folder="static",
                  template_folder="templates")


# Define homepage
@pages.route("/")
def home():
    """Render single page of website displaying data analysis results."""
    queries = run_queries()
    return render_template("home.html", queries=queries)


# Define button click route
@pages.route("/button-click", methods=["POST"])
def button_click():
    """Handle button click and show message."""
    queries = run_queries()
    return render_template("home.html",
                           queries=queries,
                           message="you clicked the button!")


# Define second button click route
@pages.route("/another-button-click", methods=["POST"])
def another_button_click():
    """Handle second button click and show a different message."""
    queries = run_queries()
    return render_template("home.html",
                           queries=queries,
                           message="you clicked the second button!")
