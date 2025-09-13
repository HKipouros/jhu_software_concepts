"""Control website pages with Flask blueprint."""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from query_data import run_queries
from update_database import find_recent, updated_scrape, clean_data, process_data_with_llm
from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg

# Variable to keep track of first button running
is_updating = False

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
def button_click():
    """Defines route for Pull Data button"""
    global is_updating

    if is_updating:
        return render_template(
            "home.html", message="Update is already in progress. Please wait.")

    is_updating = True
    try:
        queries = run_queries()

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
        conn = psycopg.connect(os.environ["DATABASE_URL"])

        for entry in llm_extend_data:
            # Prepare data
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
            llm_generated_university = entry[
                "llm-generated-university"] if entry[
                    "llm-generated-university"] else None

            # Insert
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
            conn.commit()

        conn.close()

        # Success message
        flash(
            f"Data pull completed successfully! Added {len(llm_extend_data)} new entries to database."
        )
        return redirect(url_for("pages.home"))

    # First button finished running, update variable
    finally:
        is_updating = False


@pages.route("/another-button-click", methods=["POST"])
def another_button_click():
    """Define route for Update Analysis button."""
    global is_updating

    # Do nothing except inform user if data pull still running.
    if is_updating:
        flash("Please wait. Data pull is still in progress.")

    # Otherwise run analysis and refresh home page.
    queries = run_queries()
    return redirect(url_for("pages.home"))
