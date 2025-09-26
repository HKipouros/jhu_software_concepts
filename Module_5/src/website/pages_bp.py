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

import sys
import os
import psycopg
from flask import Blueprint, render_template, redirect, url_for, flash

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from query_data import run_queries  # pylint: disable=C0413
from update_database import find_recent, updated_scrape, clean_data, process_data_with_llm  # pylint: disable=C0413


def get_db_connection():
    """Create and return a database connection."""
    return psycopg.connect(os.environ["DATABASE_URL"])


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
    """Defines route for Pull Data button"""
    global IS_UPDATING  # pylint: disable=W0603

    if IS_UPDATING:
        return render_template(
            "home.html", message="Update is already in progress. Please wait.")

    IS_UPDATING = True
    try:
        queries = run_queries()  # pylint: disable=W0612

        # Start scraping.
        flash("Starting data scrape from TheGradCafe...")

        # Call functions to scrape new data, clean, and run through LLM.
        recent_result = find_recent()
        if recent_result is None:
            recent_result = 0

        scraped_entries = updated_scrape(recent_result)
        if not scraped_entries:
            flash("No new entries to scrape")
            return redirect(url_for("pages.home"))

        # Clean data.
        flash(
            f"Found {len(scraped_entries)} new entries. Cleaning and validating data..."
        )
        cleaned_data = clean_data(scraped_entries)
        if not cleaned_data:
            flash("Data cleaning failed - no valid entries found")
            return redirect(url_for("pages.home"))

        # Run through LLM.
        flash(
            f"Processing {len(cleaned_data)} entries with LLM for standardization..."
        )
        llm_extend_data = process_data_with_llm(cleaned_data)
        if not llm_extend_data:
            flash("LLM processing failed - no data to add")
            return redirect(url_for("pages.home"))

        # Update database.
        flash(f"Updating database with {len(llm_extend_data)} new entries...")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:  # pylint: disable=E1101
                for entry in llm_extend_data:
                    # Prepare data
                    program = entry["program"] if entry["program"] else None
                    comments = entry["comments"] if entry["comments"] else None
                    date_added = entry["date_added"] if entry[
                        "date_added"] else None
                    url = entry["url"] if entry["url"] else None
                    status = entry["status"] if entry["status"] else None
                    term = entry["term"] if entry["term"] else None
                    us_or_international = entry["US/International"] if entry[
                        "US/International"] else None
                    gpa = float(entry["GPA"]) if entry["GPA"] else None
                    gre = float(entry["GRE"]) if entry["GRE"] else None
                    gre_v = float(entry["GRE_V"]) if entry["GRE_V"] else None
                    gre_aw = float(
                        entry["GRE_AW"]) if entry["GRE_AW"] else None
                    degree = entry["Degree"] if entry["Degree"] else None
                    llm_generated_program = entry[
                        "llm-generated-program"] if entry[
                            "llm-generated-program"] else None
                    llm_generated_university = entry[
                        "llm-generated-university"] if entry[
                            "llm-generated-university"] else None

                    # Define variables for table and columns
                    table_name = psycopg.sql.Identifier("applicants")
                    columns = [
                        "program", "comments", "date_added", "url", "status",
                        "term", "us_or_international", "gpa", "gre", "gre_v",
                        "gre_aw", "degree", "llm_generated_program",
                        "llm_generated_university"
                    ]
                    column_identifiers = [
                        psycopg.sql.Identifier(col) for col in columns
                    ]

                    # SQL string composition
                    query = psycopg.sql.SQL("""
                        INSERT INTO {table} ({fields})
                        VALUES ({placeholders})
                    """).format(
                        table=table_name,
                        fields=psycopg.sql.SQL(', ').join(column_identifiers),
                        placeholders=psycopg.sql.SQL(', ').join(
                            psycopg.sql.Placeholder() for _ in columns))

                    # Values in the same order as the columns list
                    values = (program, comments, date_added, url, status, term,
                              us_or_international, gpa, gre, gre_v, gre_aw,
                              degree, llm_generated_program,
                              llm_generated_university)

                    # Execute the query separately
                    cur.execute(query, values)

            # Commit all changes at once
            conn.commit()  # pylint: disable=E1101
        finally:
            conn.close()  # pylint: disable=E1101

        # Success message
        flash("Data pull completed successfully!")
        return redirect(url_for("pages.home"))

    # First button finished running, update variable
    finally:
        IS_UPDATING = False


@pages.route("/another-button-click", methods=["POST"])
def another_button_click():
    """Define route for Update Analysis button."""
    global IS_UPDATING  # pylint: disable=W0602

    # Do nothing except inform user if data pull still running.
    if IS_UPDATING:
        flash("Please wait. Data pull is still in progress.")

    # Otherwise run analysis and refresh home page.
    queries = run_queries()  # pylint: disable=W0612
    return redirect(url_for("pages.home"))
