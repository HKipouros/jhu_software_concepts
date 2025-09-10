import os
import psycopg2
import json

# Connect to the database
conn = psycopg2.connect(os.environ["DATABASE_URL"])


def run_queries():
    # Create a cursor object
    with conn.cursor() as cur:
        
        # Dictionary to hold query results
        query_results = {}
        
        # 1. Query to count entries with "Fall 2025" in the term field
        cur.execute("SELECT COUNT(*) FROM applicants WHERE term = %s",
                    ("Fall 2025", ))
        count_f_2025 = cur.fetchone()[0]
        query_results["count_f_2025"] = count_f_2025

        # 2. Query to find percentage international students
        cur.execute("""    SELECT
            (COUNT(*) FILTER (WHERE us_or_international = 'International') * 100.0 / COUNT(*)) AS percentage_international
            FROM applicants;""")
        percentage_international = cur.fetchone()[0]
        query_results["percentage_international"] = round(percentage_international, 2) if percentage_international else None

        # 3a. Query to find average GPA score
        cur.execute("SELECT AVG(gpa) FROM applicants;")
        average_gpa = cur.fetchone()[0]
        query_results["average_gpa"] = average_gpa
        
        # 3b. Query to find average GRE score
        cur.execute("SELECT AVG(gre) FROM applicants;")
        average_gre = cur.fetchone()[0]
        query_results["average_gre"] = average_gre

        # 3c. Query to find GRE V score
        cur.execute("SELECT AVG(gre_v) FROM applicants;")
        average_gre_v = cur.fetchone()[0]
        query_results["average_gre_v"] = average_gre_v

        # 3d. Query to find GRE AW score
        cur.execute("SELECT AVG(gre_aw) FROM applicants;")
        average_gre_aw = cur.fetchone()[0]
        query_results["average_gre_aw"] = average_gre_aw

        # 4. Query to find average GPA of American applicants
        cur.execute("""    SELECT
            AVG(gpa) AS average_gpa_american
            FROM applicants
            WHERE us_or_international = 'US';""")
        average_gpa_american = cur.fetchone()[0]
        query_results["average_gpa_american"] = average_gpa_american

        # 5. Query to find percent Accepted for Fall 2025
        cur.execute("""    SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN NULL
                ELSE (COUNT(*) FILTER (WHERE status = 'Accepted') * 100.0 / COUNT(*))
            END AS percentage_accepted
            FROM applicants
            WHERE term = 'Fall 2025';""")
        percentage_accepted_f25 = cur.fetchone()[0]
        query_results["percentage_accepted_f25"] = round(percentage_accepted_f25, 2) if  percentage_accepted_f25 else None

        # 6. Query to find average GPA for Fall 2025 Accepted
        cur.execute("""    SELECT AVG(gpa) AS average_gpa_accepted_f25
            FROM applicants
            WHERE term = 'Fall 2025' AND status = 'Accepted';""")
        average_gpa_accepted_f25 = cur.fetchone()[0]
        query_results["average_gpa_accepted_f25"] = average_gpa_accepted_f25

        # 7. Query to count applicants to JHU for Masters in Computer Science
        cur.execute("""    SELECT COUNT(*) AS jhu_cs_masters_count FROM applicants
            WHERE llm_generated_university = 'Johns Hopkins University' AND degree = 'Masters' AND llm_generated_program = 'Computer Science';""")
        count_jhu_cs_masters = cur.fetchone()[0]
        query_results["count_jhu_cs_masters"] = count_jhu_cs_masters

        # 8. Query to count applicants to Georgetown for PhD in Computer Science for 2025
        cur.execute("""SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN 0
                ELSE COUNT(*)
            END AS count_hoya_cs_phd_2025 
            FROM applicants
            WHERE llm_generated_university = 'Georgetown University' AND degree = 'PhD' 
            AND llm_generated_program = 'Computer Science' AND (term = 'Fall 2025' OR term = 'Spring 2025'); """)
        count_hoya_cs_phd_2025 = cur.fetchone()[0]
        query_results["count_hoya_cs_phd_2025"] = count_hoya_cs_phd_2025
        
    return query_results


if __name__ == "__main__":
    results = run_queries()
    conn.close()
    print("Database queries completed.")
    print("Query Results:")
    for key, value in results.items():
        print(f"{key}: {value}")
