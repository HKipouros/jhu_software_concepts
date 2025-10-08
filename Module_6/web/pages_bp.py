"""
This module defines routes for rendering the homepage and handling user actions
such as pulling new data from The Grad Cafe and updating analysis results.
It connects to a PostgreSQL database to store processed data entries.

Routes:
    - "/" : Renders the homepage with query results.
    - "/button-click" : Triggers data scrape, cleaning, LLM processing, and DB update.
    - "/another-button-click" : Refreshes the homepage with updated analysis.

Functions:
    - home() : Render homepage with data from queries.
    - button_click() : Pull data, process it, and update the database.
    - another_button_click() : Refresh analysis without pulling new data.

Environment Variables:
    - DATABASE_URL: PostgreSQL connection string.

Dependencies:
    - Flask
    - psycopg
    - Custom modules: run_queries, find_recent, updated_scrape,
      clean_data, process_data_with_llm
"""
from __future__ import annotations
import sys
import os
import psycopg
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, current_app
from publisher import publish_task

from query_data import run_queries

from update_database import find_recent, updated_scrape, clean_data, process_data_with_llm  # pylint: disable=C0413


def get_db_connection():
    """Create and return a database connection."""
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        database_url = "postgresql://postgres:Potassiumtree43!@localhost:5432/gradcafe_db"

    return psycopg.connect(database_url)


# Variable to keep track of first button running
IS_UPDATING = False

pages = Blueprint("pages",
                  __name__,
                  static_folder="static",
                  template_folder="templates")


# Define homepage.
@pages.route("/")
def home():
    """Render single page of website displaying data analysis results."""
    queries = run_queries()
    return render_template("home.html", queries=queries)


# Define Pull Data button route.
@pages.route("/button-click", methods=["POST"])
def button_click():  # pylint: disable=R0914
    global IS_UPDATING
    if IS_UPDATING:
        return render_template("home.html", message="Update is already in progress.")
    
    IS_UPDATING = True
    try:
        publish_task("scrape_new_data", payload={})
        return jsonify({"status": "queued", "task": "scrape_new_data"}), 202

    except Exception:
        current_app.logger.exception("Failed to publish scrape_new_data")
        return jsonify({"error": "publish_failed"}), 503
    
    finally:
        IS_UPDATING = False

@pages.route("/another-button-click", methods=["POST"])
def another_button_click():
    global IS_UPDATING
    if IS_UPDATING:
        return render_template("home.html", message="Update is already in progress.")
    
    try:
        publish_task("recompute_analytics", payload={})
        return jsonify({"status": "queued", "task": "recompute_analytics"}), 202
    except Exception:
        current_app.logger.exception("Failed to publish recompute_analytics")
        return jsonify({"error": "publish_failed"}), 503
    