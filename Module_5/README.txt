Name: Holly Kipouros (hkipour1)

Module Info: Module 5: Software Assurance, Static Code Analysis, and SQL Injections due 09/28/2025 at 11:59 PM EST

SSH url to GitHub repo:  git@github.com:HKipouros/jhu_software_concepts.git

Approach: 
Pylint - I installed Pylint and used it in an interative process over the /src Python files until each file was rated 10/10. Common issues included lines too long and variable names that did not conform to PEP-8 conventions, and these were corrected.

SQL Injection Defenses - In pages_bp.py, I separated out the SQL statement and execution statement (previously this was done in one step) and used string composition and sql.Identifier to insert data into the database. In load_data.py, I similarly separated out SQL statement and execution statements for dropping the applicants table if it exists and creating the applicants table otherwise, with the use of sql.Identifier. The aforementioned modules use only INSERT statements and therefore I did not impose any limit feature in the statements. The module query_data.py includes SQL queries, so in order to set limits for the query statements, I initially determined the size of the database and set a limit of the size plus 100. Each query in query_data.py was treated to separate out statements and execution, and sql.Identifier and sql.Literal were used to handle query values and the limit value. The update_database.py module also uses a SQL query to examine urls in the database to determine the most recent entry, and therefore this module was also modified to set a limit as in query_data.py for the SQL statement, with the statement and execution being separated out with sql.Identifier and sql.Literal as above.

Dependency graps - I installed pydeps and used graphviz to create dependency graphs for app.py and pages_bp.py (which is imported into app.py and includes the bulk of the logic).

Virtual environment - I verified that app.py still produced a working webpage by running it from the command prompt after applying the linting and SQL statement edits discussed above.

Snyk - I installed snyk and obtained an API token so I could run it from my Replit environment. It tested 31 dependencies and found no vulnerabilities. Therefore, the project is free of known malicious packages.

Known bugs: There are no known bugs.