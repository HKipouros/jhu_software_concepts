import os
import psycopg
import json

# Connect to the database
conn = psycopg.connect(os.environ["DATABASE_URL"])


def run_queries():
    # Questions the queries seek to answer in longform strings
    q_1 = "How many entries do you have in your database who have applied for Fall 2025?"
    q_2 = "What percentage of entries are from international students (not American or Other) (to two decimal places)?"
    q_3 = "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?"
    q_4 = "What is their average GPA of American students in Fall 2025?"
    q_5 = "What percent of entries for Fall 2025 are Acceptances (to two decimal places)?"
    q_6 = "What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?"
    q_7 = "How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?"
    q_8 = "How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in Computer Science?"
    q_9 = "Which school had the most applicants for Fall 2025?"
    q_10 = "Did the University of Virginia or Virginia Tech have a higher average GPA for applicants accepted Fall 2025?"

    # Create a cursor object
    with conn.cursor() as cur:

        # Dictionary to hold query results with key being question # and value being a tuple of (longform question, answer)
        query_results = {}

        # 1. Query to count entries with "Fall 2025" in the term field
        cur.execute("SELECT COUNT(*) FROM applicants WHERE term = %s",
                    ("Fall 2025", ))
        count_f_2025 = cur.fetchone()[0]
        query_results["1"] = (q_1, count_f_2025)

        # 2. Query to find percentage international students
        cur.execute("""    SELECT
            (COUNT(*) FILTER (WHERE us_or_international = 'International') * 100.0 / COUNT(*)) AS percentage_international
            FROM applicants;""")
        percentage_international = cur.fetchone()[0]
        query_results["2"] = (q_2, round(percentage_international, 2)
                              if percentage_international else None)

        # 3a. Query to find average GPA score
        cur.execute("SELECT AVG(gpa) FROM applicants;")
        average_gpa = cur.fetchone()[0]

        # 3b. Query to find average GRE score
        cur.execute("SELECT AVG(gre) FROM applicants;")
        average_gre = cur.fetchone()[0]

        # 3c. Query to find GRE V score
        cur.execute("SELECT AVG(gre_v) FROM applicants;")
        average_gre_v = cur.fetchone()[0]

        # 3d. Query to find GRE AW score
        cur.execute("SELECT AVG(gre_aw) FROM applicants;")
        average_gre_aw = cur.fetchone()[0]

        query_results["3"] = (
            q_3,
            f"Average GPA: {average_gpa}, Average GRE: {average_gre}, Average GRE V: {average_gre_v}, Average GRE AW: {average_gre_aw}"
        )

        # 4. Query to find average GPA of American applicants
        cur.execute("""    SELECT
            AVG(gpa) AS average_gpa_american
            FROM applicants
            WHERE us_or_international = 'American';""")
        average_gpa_american = cur.fetchone()[0]
        query_results["4"] = (q_4, average_gpa_american)

        # 5. Query to find percent Accepted for Fall 2025
        cur.execute("""    SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN NULL
                ELSE (COUNT(*) FILTER (WHERE status LIKE 'Accepted%') * 100.0 / COUNT(*))
            END AS percentage_accepted
            FROM applicants
            WHERE term = 'Fall 2025';""")
        percentage_accepted_f25 = cur.fetchone()[0]
        query_results["5"] = (q_5, round(percentage_accepted_f25, 2)
                              if percentage_accepted_f25 else None)

        # 6. Query to find average GPA for Fall 2025 Accepted
        cur.execute("""    SELECT AVG(gpa) AS average_gpa_accepted_f25
            FROM applicants
            WHERE term = 'Fall 2025' AND status LIKE 'Accepted%';""")
        average_gpa_accepted_f25 = cur.fetchone()[0]
        query_results["6"] = (q_6, average_gpa_accepted_f25)

        # 7. Query to count applicants to JHU for Masters in Computer Science
        cur.execute(
            """    SELECT COUNT(*) AS jhu_cs_masters_count FROM applicants
            WHERE llm_generated_university = 'Johns Hopkins University' AND degree = 'Masters' AND llm_generated_program = 'Computer Science';"""
        )
        count_jhu_cs_masters = cur.fetchone()[0]
        query_results["7"] = (q_7, count_jhu_cs_masters)

        # 8. Query to count applicants to Georgetown for PhD in Computer Science who were accepted
        cur.execute("""    SELECT COUNT(*) AS hoya_cs_phd_2025 FROM applicants
            WHERE llm_generated_university = 'Georgetown University' AND degree = 'PhD' AND llm_generated_program = 'Computer Science' AND status LIKE 'Accepted%';"""
                    )
        count_hoya_cs_phd_2025 = cur.fetchone()[0]
        query_results["8"] = (q_8, count_hoya_cs_phd_2025)

        # 9. Query to find most common university for Fall 2025 applicants
        cur.execute(
            """    SELECT llm_generated_university, COUNT(*) AS count FROM applicants
            WHERE term = 'Fall 2025'
            GROUP BY llm_generated_university
            ORDER BY count DESC
            LIMIT 1;""")
        popular_u_f25 = cur.fetchone()[0]
        query_results["9"] = (q_9, popular_u_f25)

        # 10. Query to compare UVA and VT accepted GPAs for Fall 2025
        cur.execute("""    SELECT
            (AVG(gpa) FILTER (WHERE llm_generated_university = 'University of Virginia')) AS uva_gpa,
            (AVG(gpa) FILTER (WHERE llm_generated_university = 'Virginia Tech')) AS vt_gpa
            FROM applicants
            WHERE term = 'Fall 2025' AND status LIKE 'Accepted%';""")
        uva_gpa, vt_gpa = cur.fetchone()
        if uva_gpa > vt_gpa:
            statement = f"The University of Virginia (gpa = {round(uva_gpa, 2)}) had a higher average GPA than Virginia Tech (gpa = {round(vt_gpa, 2)}) for Fall 2025 Accepted"
        else:
            statement = f"Virginia Tech (gpa = {round(vt_gpa, 2)}) had a higher average GPA than the University of Virginia (gpa = {round(uva_gpa, 2)}) for Fall 2025 Accepted"
        query_results["10"] = (q_10, statement)

        # Count total rows in database
        cur.execute("SELECT COUNT(*) FROM applicants;")
        total_rows = cur.fetchone()[0]
        query_results["total_rows"] = total_rows

    return query_results


if __name__ == "__main__":
    results = run_queries()
    conn.close()
    print("Database queries completed.")
    print("Query Results:")
    for key, value in results.items():
        print(f"{key}: {value}")
