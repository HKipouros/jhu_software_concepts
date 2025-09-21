# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Graduate Data Analysis'
copyright = '2025, Holly Kipouros'
author = 'Holly Kipouros'
release = '0.0.1'

import os
import sys

# Get absolute path to the project root (which is the repo root in this case)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# Add Module_4/src and Module_4/src/website to sys.path
sys.path.insert(0, os.path.join(project_root, "Module_4", "src"))
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc"]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
