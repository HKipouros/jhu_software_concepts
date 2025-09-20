.. Graduate Data Analysis documentation master file, created by
   sphinx-quickstart on Fri Sep 19 16:42:14 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Graduate Data Analysis documentation
====================================
*Welcome to the Graduate Applicant Data Analysis Tool documentation!*

This tool scrapes data from The Grad Cafe and returns detailed analysis on applicant data.

The tool is executed by running the Flask application module. The Data Loading module is responsible for feeding a PostgreSQL database with over 30,000 historical data points from The Grad Cafe, while the Data Query module analyzes the information within the database. The Database Update module is responsible for updating the database with new data points.

Click on the module documentation pages below to view more information including required envrionmental variables.

A Pytest suite has been developed for testing. After installation of Pytest, testing can be run with the command line prompt "pytest". Marked tests include "web" and "buttons" for webpage testing and "analysis", "db", and "integration" for database and analysis testing.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   src
   src.website