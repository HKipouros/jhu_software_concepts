"""This module contains unit testing for the Flask webpage, including page loading and contents."""

import re
from flask import Flask
import pytest
from src.website.app import app

# Part A: test that a Flask app is created with required routes
@pytest.mark.web
def test_create_flask_app():
  """Test that a Flask app is created with required routes"""
  
  # Test that app is created.
  assert app is not None
  
  # Test that app is a Flask app.
  assert type(app) == type(Flask(__name__))

# Test that required routes are present
assert app.blueprints["pages"] is not None

# Part B: Test loading of home (analysis) page, existence of "Pull Data" and "Update Analysis" buttons, and that page text includes "Analysis" and at least one "Answer".

# Fixture to return client object
@pytest.fixture
def client():
  app.config["TESTING"] = True
  with app.test_client() as client:
    yield client

@pytest.mark.web
def test_home_route(client):
  """Test proper loading (status code is 200) of home page of analysis website."""
  response = client.get("/")
  assert response.status_code == 200

@pytest.mark.web
def test_home_contains_buttons(client):
  """Test for existence of Pull Data and Update Analysis buttons in webpage"""

  response = client.get("/")
  html = response.data.decode('utf-8')

  # Regex pattern to find a button including Pull Data
  pull_pat = r"<button[^>]*>[\s\S]*?Pull Data[\s\S]*?</button>"
  # Regex pattern to find button including Update Analysis
  update_pat = r"<button[^>]*>[\s\S]*?Update Analysis[\s\S]*?</button>"

  assert re.search(pull_pat, html)
  assert re.search(update_pat, html)


@pytest.mark.web
def test_home_contains_text(client):
  """Test for existence of Analysis and Answer: text in webpage"""
  response = client.get("/")
  html = response.data.decode('utf-8')
  assert "Analysis" in html
  assert "Answer:" in html
