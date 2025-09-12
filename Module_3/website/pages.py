"""Control website pages with Flask blueprint"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from query_data import run_queries
from update_database import find_recent, updated_scrape, clean_data, process_data_with_llm
from flask import Blueprint, render_template, request, redirect, url_for
import psycopg

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


# Define Pull Data button route
@pages.route("/button-click", methods=["POST"])
def button_click():
    """Handle button click and resulting data scrape/database update."""
    queries = run_queries()

    # Call functions to scrape new data, clean, and run through LLM
    recent_result = find_recent()
    scraped_entries = updated_scrape(recent_result) if updated_scrape(
        recent_result) else None
    cleaned_data = clean_data(scraped_entries) if clean_data(
        scraped_entries) else None
    llm_extend_data = process_data_with_llm(
        cleaned_data) if process_data_with_llm(cleaned_data) else None

    # Update database with new data
    conn = psycopg.connect(os.environ["DATABASE_URL"])

    for entry in llm_extend_data:

        # Prepare data for insertion
        program = entry["program"] if entry["program"] else None
        comments = entry["comments"] if entry["comments"] else None
        date_added = entry["date_added"] if entry["date_added"] else None
        url = entry["url"] if entry["url"] else None
        status = entry["status"] if entry["status"] else None
        term = entry["term"] if entry["term"] else None
        us_or_international = entry["US/International"] if entry[
            "US/International"] else None
        gpa = float(entry["GPA"]) if entry["GPA"] else None
        gre = float(entry["GRE"]) if entry["GRE"] else None
        gre_v = float(entry["GRE_V"]) if entry["GRE_V"] else None
        gre_aw = float(entry["GRE_AW"]) if entry["GRE_AW"] else None
        degree = entry["Degree"] if entry["Degree"] else None
        llm_generated_program = entry["llm-generated-program"] if entry[
            "llm-generated-program"] else None
        llm_generated_university = entry["llm-generated-university"] if entry[
            "llm-generated-university"] else None

        # Create a cursor object
        with conn.cursor() as cur:
            cur.execute(
                """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term, 
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_generated_program, llm_generated_university
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (program, comments, date_added, url, status, term,
              us_or_international, gpa, gre, gre_v, gre_aw, degree,
              llm_generated_program, llm_generated_university))

        # Commit the changes to the database
        conn.commit()

    # Close the connection
    conn.close()

    return render_template(
        "home.html",
        queries=queries,
        message=f"New entries scraped and added to database.")


# Define Update Analysis button route
@pages.route("/another-button-click", methods=["POST"])
def another_button_click():
    """Handle second button click and re-analyze data."""
    queries = run_queries()
    return render_template(
        "home.html",
        queries=queries,
        message="Analysis completed on newly updated database.")
