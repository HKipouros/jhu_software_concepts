"""This module contains unit testing for analysis webpage formatting."""
import re
import pytest
from bs4 import BeautifulSoup
from src.website.app import app


# Fixture to return client object
@pytest.fixture
def client():
  app.config["TESTING"] = True
  with app.test_client() as client:
    yield client

@pytest.mark.analysis
def test_answer_labels(client):
  """Tests for the existence of Answer labels for rendered analysis."""
  response = client.get("/")
  
  # Identify all query sections using Beautiful Soup and check for Answer:
  soup = BeautifulSoup(response.data, "html.parser")
  query_divs = soup.find_all("div", class_="query")
  for query_div in query_divs:
    answer = query_div.find("p")
    assert answer.text.strip().startswith("Answer:")

@pytest.mark.analysis
def test_round(client):
  """Tests that any percentage is formatted with two decimal places."""
  response = client.get("/")
  soup = BeautifulSoup(response.data, "html.parser")
  query_divs = soup.find_all("div", class_="query")
  for query_div in query_divs:
    question = query_div.find("h3")
    if "percent" in question.text.lower():
      answer = query_div.find("p")
      dec_pat = r"\b\d+\.\d{2}\b" # Regex pattern to verify numbers are to two decimal places.
      assert re.search(dec_pat, answer.text.strip())
  
    
  