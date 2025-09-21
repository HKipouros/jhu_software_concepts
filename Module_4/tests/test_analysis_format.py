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


@pytest.mark.analysis
def test_query_data_edge_cases(monkeypatch):
    """Test edge cases in query_data.py for 100% coverage"""
    from src.query_data import run_queries
    
    # Test different GPA comparison scenarios
    test_scenarios = [
        # VT higher than UVA
        (3.4, 3.6, "Virginia Tech (gpa = 3.6) had a higher average GPA than the University of Virginia (gpa = 3.4)"),
        # Only UVA data
        (3.5, None, "Only University of Virginia has data (gpa = 3.5)"),
        # Only VT data
        (None, 3.7, "Only Virginia Tech has data (gpa = 3.7)"),
        # No data for either
        (None, None, "No GPA data available for either university")
    ]
    
    for uva_gpa, vt_gpa, expected_text in test_scenarios:
        # Mock database operations
        class MockCursor:
            def __init__(self, uva_result, vt_result):
                self.uva_result = uva_result
                self.vt_result = vt_result
                self.queries = []
                
            def execute(self, query, params=None):
                self.queries.append(query)
                self.params = params
                
            def fetchone(self):
                # Return specific results for the UVA/VT GPA comparison query
                if "uva_gpa" in self.queries[-1]:
                    return (self.uva_result, self.vt_result)
                return (42,)  # Default for other queries
                
            def __enter__(self):
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        class MockConnection:
            def __init__(self, uva_result, vt_result):
                self.uva_result = uva_result
                self.vt_result = vt_result
                
            def cursor(self):
                return MockCursor(self.uva_result, self.vt_result)
                
            def close(self):
                pass  # Mock close method
        
        # Apply mock
        monkeypatch.setattr('src.query_data.get_db_connection', lambda: MockConnection(uva_gpa, vt_gpa))
        
        # Execute function
        results = run_queries()
        
        # Verify specific edge case is covered
        result_10 = results["10"][1]
        assert expected_text in result_10