"""
This module connects to the database using the `DATABASE_URL` environment variable
and defines a set of queries that return insights into applicant data, such as
application volume, acceptance rates, GPA statistics, and other trends.

The `run_queries()` function is used to extract a dictionary of human-readable
questions and corresponding answers based on current data.

Environment Variables:
    DATABASE_URL (str): PostgreSQL connection string used to connect to the database.

Functions:
    run_queries() -> dict
        Executes predefined SQL queries and returns answers with associated questions.

Usage:
    >>> from query_data import run_queries
    >>> results = run_queries()
    >>> print(results["1"])  # ("How many entries...", 154)

Example CLI Execution:
    $ python query_data.py
"""

import os
import psycopg


def get_db_connection():
    """Create and return a database connection."""
    return psycopg.connect(os.environ["DATABASE_URL"])


def run_queries():  # pylint: disable=R0915, R0914
    """Defines SQL queries and interrogates database, storing answers in a dictionary"""
    conn = get_db_connection()
    try:
        # Questions the queries seek to answer in longform strings
        q_1 = "How many entries do you have in your database who have applied for Fall 2025?"
        q_2 = ("What percentage of entries are from international students "
               "(not American or Other) (to two decimal places)?")
        q_3 = "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?"
        q_4 = "What is their average GPA of American students in Fall 2025?"
        q_5 = "What percent of entries for Fall 2025 are Acceptances (to two decimal places)?"
        q_6 = "What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?"
        q_7 = (
            "How many entries are from applicants who applied to JHU for a masters degrees "
            "in Computer Science?")
        q_8 = (
            "How many entries from 2025 are acceptances from applicants who applied to "
            "Georgetown University for a PhD in Computer Science?")
        q_9 = "Which school had the most applicants for Fall 2025?"
        q_10 = (
            "Did the University of Virginia or Virginia Tech have a higher average GPA "
            "for applicants accepted Fall 2025?")

        # Create a cursor object.
        with conn.cursor() as cur:  # pylint: disable=E1101

            # Dictionary to hold query results with key being question
            # and value being a tuple of (longform question, answer).
            query_results = {}

            # Determine total number of rows in db for limit setting
            count_query = psycopg.sql.SQL(
                "SELECT COUNT(*) FROM {table}").format(
                    table=psycopg.sql.Identifier("applicants"))
            cur.execute(count_query)
            row = cur.fetchone()
            total_rows = row[0] if row else 0
            row_limit = total_rows + 100

            # 1. Query to count entries with "Fall 2025" in the term field.
            select_query = psycopg.sql.SQL("""
                SELECT COUNT(*) FROM {table} WHERE {column} = {value} LIMIT {limit}
            """).format(table=psycopg.sql.Identifier("applicants"),
                        column=psycopg.sql.Identifier("term"),
                        value=psycopg.sql.Literal("Fall 2025"),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(select_query)
            result = cur.fetchone()
            count_f_2025 = result[0] if result else 0
            query_results["1"] = (q_1, count_f_2025)

            # 2. Query to find percentage international students.
            percentage_query = psycopg.sql.SQL("""
                SELECT
                    (COUNT(*) FILTER (WHERE {column} = {value}) * 100.0 / COUNT(*)) AS percentage_international
                FROM {table}
                LIMIT {limit}
            """).format(table=psycopg.sql.Identifier("applicants"),
                        column=psycopg.sql.Identifier("us_or_international"),
                        value=psycopg.sql.Literal("International"),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(percentage_query)
            result = cur.fetchone()
            percentage_international = result[0] if result else None
            query_results["2"] = (q_2, round(percentage_international, 2)
                                  if percentage_international else None)

            # 3a. Query to find average GPA score.
            avg_gpa_query = psycopg.sql.SQL("""
                SELECT AVG({column})
                FROM {table}
                WHERE {column} < {threshold}
                LIMIT {limit}
            """).format(column=psycopg.sql.Identifier("gpa"),
                        table=psycopg.sql.Identifier("applicants"),
                        threshold=psycopg.sql.Literal(5),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(avg_gpa_query)
            result = cur.fetchone()
            average_gpa = result[0] if result else None

            # 3b. Query to find average GRE score.
            avg_gre_query = psycopg.sql.SQL("""
                SELECT AVG({column}) FROM (
                    SELECT {column}
                    FROM {table}
                    WHERE {column} < {threshold}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(column=psycopg.sql.Identifier("gre"),
                        table=psycopg.sql.Identifier("applicants"),
                        threshold=psycopg.sql.Literal(170),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(avg_gre_query)
            result = cur.fetchone()
            average_gre = result[0] if result else None

            # 3c. Query to find GRE V score.
            avg_gre_v_query = psycopg.sql.SQL("""
                SELECT AVG({column}) FROM (
                    SELECT {column}
                    FROM {table}
                    WHERE {column} < {threshold}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(column=psycopg.sql.Identifier("gre_v"),
                        table=psycopg.sql.Identifier("applicants"),
                        threshold=psycopg.sql.Literal(170),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(avg_gre_v_query)
            result = cur.fetchone()
            average_gre_v = result[0] if result else None

            # 3d. Query to find GRE AW score.
            avg_gre_aw_query = psycopg.sql.SQL("""
                SELECT AVG({column}) FROM (
                    SELECT {column}
                    FROM {table}
                    WHERE {column} < {threshold}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(column=psycopg.sql.Identifier("gre_aw"),
                        table=psycopg.sql.Identifier("applicants"),
                        threshold=psycopg.sql.Literal(6),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(avg_gre_aw_query)
            result = cur.fetchone()
            average_gre_aw = result[0] if result else None

            query_results["3"] = (q_3, (
                f"Average GPA: {round(average_gpa, 2) if average_gpa else 'N/A'}, "
                f"Average GRE: {round(average_gre, 2) if average_gre else 'N/A'}, "
                f"Average GRE V: {round(average_gre_v, 2) if average_gre_v else 'N/A'}, "
                f"Average GRE AW: {round(average_gre_aw, 2) if average_gre_aw else 'N/A'}"
            ))

            # 4. Query to find average GPA of American applicants.
            avg_gpa_american_query = psycopg.sql.SQL("""
                SELECT AVG({gpa_col}) AS average_gpa_american FROM (
                    SELECT {gpa_col}
                    FROM {table}
                    WHERE {country_col} = {country_val}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(
                gpa_col=psycopg.sql.Identifier("gpa"),
                table=psycopg.sql.Identifier("applicants"),
                country_col=psycopg.sql.Identifier("us_or_international"),
                country_val=psycopg.sql.Literal("American"),
                limit=psycopg.sql.Literal(row_limit))

            cur.execute(avg_gpa_american_query)
            result = cur.fetchone()
            average_gpa_american = result[0] if result else None
            query_results["4"] = (q_4, round(average_gpa_american, 2)
                                  if average_gpa_american else None)

            # 5. Query to find percent Accepted for Fall 2025.
            percentage_accepted_query = psycopg.sql.SQL("""
                SELECT
                    CASE 
                        WHEN COUNT(*) = 0 THEN NULL
                        ELSE (COUNT(*) FILTER (WHERE {status_col} LIKE {status_pattern}) * 100.0 / COUNT(*))
                    END AS percentage_accepted
                FROM (
                    SELECT *
                    FROM {table}
                    WHERE {term_col} = {term_val}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(status_col=psycopg.sql.Identifier("status"),
                        status_pattern=psycopg.sql.Literal("Accepted%"),
                        table=psycopg.sql.Identifier("applicants"),
                        term_col=psycopg.sql.Identifier("term"),
                        term_val=psycopg.sql.Literal("Fall 2025"),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(percentage_accepted_query)
            result = cur.fetchone()
            percentage_accepted_f25 = result[0] if result else None
            query_results["5"] = (q_5, round(percentage_accepted_f25, 2)
                                  if percentage_accepted_f25 else None)

            # 6. Query to find average GPA for Fall 2025 Accepted.
            avg_gpa_accepted_f25_query = psycopg.sql.SQL("""
                SELECT AVG({gpa_col}) AS average_gpa_accepted_f25 FROM (
                    SELECT {gpa_col}
                    FROM {table}
                    WHERE {term_col} = {term_val}
                      AND {gpa_col} < {gpa_threshold}
                      AND {status_col} LIKE {status_pattern}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(gpa_col=psycopg.sql.Identifier("gpa"),
                        table=psycopg.sql.Identifier("applicants"),
                        term_col=psycopg.sql.Identifier("term"),
                        term_val=psycopg.sql.Literal("Fall 2025"),
                        gpa_threshold=psycopg.sql.Literal(5),
                        status_col=psycopg.sql.Identifier("status"),
                        status_pattern=psycopg.sql.Literal("Accepted%"),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(avg_gpa_accepted_f25_query)
            result = cur.fetchone()
            average_gpa_accepted_f25 = result[0] if result else None
            query_results["6"] = (q_6, round(average_gpa_accepted_f25, 2)
                                  if average_gpa_accepted_f25 else None)

            # 7. Query to count applicants to JHU for Masters in Computer Science.
            jhu_cs_masters_count_query = psycopg.sql.SQL("""
                SELECT COUNT(*) AS jhu_cs_masters_count FROM (
                    SELECT *
                    FROM {table}
                    WHERE {university_col} = {university_val}
                      AND {degree_col} = {degree_val}
                      AND {program_col} = {program_val}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(
                table=psycopg.sql.Identifier("applicants"),
                university_col=psycopg.sql.Identifier(
                    "llm_generated_university"),
                university_val=psycopg.sql.Literal("Johns Hopkins University"),
                degree_col=psycopg.sql.Identifier("degree"),
                degree_val=psycopg.sql.Literal("Masters"),
                program_col=psycopg.sql.Identifier("llm_generated_program"),
                program_val=psycopg.sql.Literal("Computer Science"),
                limit=psycopg.sql.Literal(row_limit))

            cur.execute(jhu_cs_masters_count_query)
            result = cur.fetchone()
            count_jhu_cs_masters = result[0] if result else 0
            query_results["7"] = (q_7, count_jhu_cs_masters)

            # 8. Query to count applicants to Georgetown for PhD in CS who were accepted.
            hoya_cs_phd_2025_query = psycopg.sql.SQL("""
                SELECT COUNT(*) AS hoya_cs_phd_2025 FROM (
                    SELECT *
                    FROM {table}
                    WHERE {university_col} = {university_val}
                      AND {degree_col} = {degree_val}
                      AND {program_col} = {program_val}
                      AND {status_col} LIKE {status_pattern}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(
                table=psycopg.sql.Identifier("applicants"),
                university_col=psycopg.sql.Identifier(
                    "llm_generated_university"),
                university_val=psycopg.sql.Literal("Georgetown University"),
                degree_col=psycopg.sql.Identifier("degree"),
                degree_val=psycopg.sql.Literal("PhD"),
                program_col=psycopg.sql.Identifier("llm_generated_program"),
                program_val=psycopg.sql.Literal("Computer Science"),
                status_col=psycopg.sql.Identifier("status"),
                status_pattern=psycopg.sql.Literal("Accepted%"),
                limit=psycopg.sql.Literal(row_limit))

            cur.execute(hoya_cs_phd_2025_query)
            result = cur.fetchone()
            count_hoya_cs_phd_2025 = result[0] if result else 0
            query_results["8"] = (q_8, count_hoya_cs_phd_2025)

            # 9. Query to find most common university for Fall 2025 applicants.
            top_university_query = psycopg.sql.SQL("""
                SELECT {university_col}, COUNT(*) AS count FROM {table}
                WHERE {term_col} = {term_val}
                GROUP BY {university_col}
                ORDER BY count DESC
                LIMIT {limit};
            """).format(university_col=psycopg.sql.Identifier(
                "llm_generated_university"),
                        table=psycopg.sql.Identifier("applicants"),
                        term_col=psycopg.sql.Identifier("term"),
                        term_val=psycopg.sql.Literal("Fall 2025"),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(top_university_query)
            result = cur.fetchone()
            popular_u_f25 = result[0] if result else 'No data'
            query_results["9"] = (q_9, popular_u_f25)

            # 10. Query to compare UVA and VT accepted GPAs for Fall 2025.
            avg_gpa_uva_vt_query = psycopg.sql.SQL("""
                SELECT
                    AVG({gpa_col}) FILTER (
                        WHERE {university_col} = {uva_val} AND {gpa_col} < {gpa_threshold}
                    ) AS uva_gpa,
                    AVG({gpa_col}) FILTER (
                        WHERE {university_col} = {vt_val} AND {gpa_col} < {gpa_threshold}
                    ) AS vt_gpa
                FROM (
                    SELECT *
                    FROM {table}
                    WHERE {term_col} = {term_val}
                      AND {status_col} LIKE {status_pattern}
                    LIMIT {limit}
                ) AS limited_subquery
            """).format(gpa_col=psycopg.sql.Identifier("gpa"),
                        university_col=psycopg.sql.Identifier(
                            "llm_generated_university"),
                        uva_val=psycopg.sql.Literal("University of Virginia"),
                        vt_val=psycopg.sql.Literal("Virginia Tech"),
                        gpa_threshold=psycopg.sql.Literal(5),
                        table=psycopg.sql.Identifier("applicants"),
                        term_col=psycopg.sql.Identifier("term"),
                        term_val=psycopg.sql.Literal("Fall 2025"),
                        status_col=psycopg.sql.Identifier("status"),
                        status_pattern=psycopg.sql.Literal("Accepted%"),
                        limit=psycopg.sql.Literal(row_limit))

            cur.execute(avg_gpa_uva_vt_query)
            result = cur.fetchone()
            uva_gpa, vt_gpa = result if result else (None, None)
            if uva_gpa is not None and vt_gpa is not None:
                if uva_gpa > vt_gpa:
                    statement = (
                        f"The University of Virginia (gpa = {round(uva_gpa, 2)}) "
                        f"had a higher average GPA than Virginia Tech "
                        f"(gpa = {round(vt_gpa, 2)}) for Fall 2025 Accepted")
                else:
                    statement = (
                        f"Virginia Tech (gpa = {round(vt_gpa, 2)}"
                        f"had a higher average GPA than the University of Virginia "
                        f"(gpa = {round(uva_gpa, 2)}) for Fall 2025 Accepted")
            elif uva_gpa is not None:
                statement = (
                    f"Only University of Virginia has data "
                    f"(gpa = {round(uva_gpa, 2)}) for Fall 2025 Accepted")
            elif vt_gpa is not None:
                statement = (
                    f"Only Virginia Tech has data "
                    f"(gpa = {round(vt_gpa, 2)}) for Fall 2025 Accepted")
            else:
                statement = "No GPA data available for either university for Fall 2025 Accepted"
            query_results["10"] = (q_10, statement)

            return query_results
    finally:
        conn.close()  # pylint: disable=E1101


if __name__ == "__main__":
    results = run_queries()
    print("Database queries completed.")
    print("Query Results:")
    for key, value in results.items():
        print(f"{key}. {value[0]}: {value[1]}")
