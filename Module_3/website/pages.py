"""Control website pages with Flask blueprint"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from query_data import run_queries
from flask import Blueprint, render_template

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
