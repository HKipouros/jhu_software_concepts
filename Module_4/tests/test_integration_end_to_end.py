"""Tests end-to-end functionality including handling of overlapping data containing duplicate datapoints."""

from flask import Flask
import pytest
from src.website.app import app

@pytest.fixture
def sample_data():
  """Sample applicant data for testing. Contains duplicate datapoints."""
  return [{
      "program": "Computer Science, MIT",
      "comments": "",
      "date_added": "2024-01-15",
      "url": "https://gradcafe.com/1",
      "status": "Accepted",
      "term": "Fall 2024",
      "US/International": "US",
      "GPA": "3.8",
      "GRE": "320",
      "GRE_V": "160",
      "GRE_AW": "4.5",
      "Degree": "MS",
      "llm-generated-program": "Computer Science",
      "llm-generated-university": "MIT"
  }, {
      "program": "Physics, Stanford",
      "comments": "",
      "date_added": None,
      "url": "https://gradcafe.com/2",
      "status": "Rejected",
      "term": "Spring 2024",
      "US/International": "International",
      "GPA": "",
      "GRE": "",
      "GRE_V": "155",
      "GRE_AW": "",
      "Degree": "PhD",
      "llm-generated-program": "",
      "llm-generated-university": None
  },
  {
      "program": "Computer Science, MIT",
      "comments": "",
      "date_added": "2024-01-15",
      "url": "https://gradcafe.com/1",
      "status": "Accepted",
      "term": "Fall 2024",
      "US/International": "US",
      "GPA": "3.8",
      "GRE": "320",
      "GRE_V": "160",
      "GRE_AW": "4.5",
      "Degree": "MS",
      "llm-generated-program": "Computer Science",
      "llm-generated-university": "MIT"
         }]

@pytest.mark.integration
def test_end_insertion(sample_data, monkeypatch):
    """Test the button_click function from pages.py with end-to-end data flow, including properly handling of duplicate entries."""
    from src.website.pages import button_click
    import src.website.pages as pages_module
    
    # Track function calls and database operations
    called_functions = []
    database_operations = []
    flash_messages = []
    
    # Mock external function dependencies
    def mock_run_queries():
        called_functions.append('run_queries')
        return {"mock": "queries"}
    
    def mock_find_recent():
        called_functions.append('find_recent')
        return 100
    
    def mock_updated_scrape(recent_result):
        called_functions.append(f'updated_scrape({recent_result})')
        return ["scraped_entry_1", "scraped_entry_2", "scraped_entry_3"]
    
    def mock_clean_data(scraped_entries):
        called_functions.append(f'clean_data({len(scraped_entries)} entries)')
        return ["cleaned_entry_1", "cleaned_entry_2", "cleaned_entry_3"]
    
    def mock_process_data_with_llm(cleaned_data):
        called_functions.append(f'process_data_with_llm({len(cleaned_data)} entries)')
        return sample_data  # Return our test data
    
    # Mock database connection and cursor
    class MockCursor:
        def __init__(self):
            self.executed_queries = []
            self.executed_params = []
            self.inserted_urls = set()
            
        def execute(self, query, params=None):
            self.executed_queries.append(query.strip())
            if params and "INSERT INTO applicants" in query:
                url = params[3]  # URL is the 4th parameter
                # Simulate ON CONFLICT (url) DO NOTHING behavior
                if url not in self.inserted_urls:
                    self.executed_params.append(params)
                    database_operations.append(f'INSERT: {params[0]} - {url}')
                    if url:
                        self.inserted_urls.add(url)
                else:
                    database_operations.append(f'CONFLICT IGNORED: {url}')
            elif params:
                self.executed_params.append(params)
                
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockConnection:
        def __init__(self):
            self.cursor_obj = MockCursor()
            self.committed = False
            self.closed = False
            
        def cursor(self):
            return self.cursor_obj
            
        def commit(self):
            self.committed = True
            database_operations.append('COMMIT')
            
        def close(self):
            self.closed = True
            database_operations.append('CLOSE')
    
    mock_connection = MockConnection()
    
    # Mock get_db_connection 
    def mock_get_db_connection():
        database_operations.append('CONNECT: DATABASE_URL')
        return mock_connection
    
    # Mock Flask functions
    def mock_flash(message):
        flash_messages.append(message)
    
    def mock_redirect(url):
        return f"REDIRECT_TO: {url}"
    
    def mock_url_for(endpoint):
        return f"URL_FOR: {endpoint}"
    
    def mock_render_template(template, **kwargs):
        return f"TEMPLATE: {template} with {kwargs}"
    
    # Apply all mocks using monkeypatch
    monkeypatch.setattr('src.website.pages.run_queries', mock_run_queries)
    monkeypatch.setattr('src.website.pages.find_recent', mock_find_recent)
    monkeypatch.setattr('src.website.pages.updated_scrape', mock_updated_scrape)
    monkeypatch.setattr('src.website.pages.clean_data', mock_clean_data)
    monkeypatch.setattr('src.website.pages.process_data_with_llm', mock_process_data_with_llm)
    monkeypatch.setattr('src.website.pages.get_db_connection', mock_get_db_connection)
    monkeypatch.setattr('src.website.pages.flash', mock_flash)
    monkeypatch.setattr('src.website.pages.redirect', mock_redirect)
    monkeypatch.setattr('src.website.pages.url_for', mock_url_for)
    monkeypatch.setattr('src.website.pages.render_template', mock_render_template)
    
    # Mock environment variable
    monkeypatch.setenv('DATABASE_URL', 'postgresql://test:test@localhost/test')
    
    # Reset the global is_updating variable
    monkeypatch.setattr('src.website.pages.is_updating', False)
    
    # Execute the button_click function
    result = button_click()
    
    # Verify function call sequence
    expected_calls = [
        'run_queries',
        'find_recent', 
        'updated_scrape(100)',
        'clean_data(3 entries)',
        'process_data_with_llm(3 entries)'
    ]
    assert called_functions == expected_calls, f"Expected {expected_calls}, got {called_functions}"
    
    # Verify flash messages were generated
    expected_flash_messages = [
        "Starting data scrape from TheGradCafe...",
        "Found 3 new entries. Cleaning and validating data...",
        "Processing 3 entries with LLM for standardization...",
        "Updating database with 3 new entries...",
        "Data pull completed successfully! Added 3 new entries to database."
    ]
    assert flash_messages == expected_flash_messages, f"Expected {expected_flash_messages}, got {flash_messages}"
    
    # Verify database operations
    cursor = mock_connection.cursor_obj
    
    # Should have 3 INSERT attempts but only 2 successful (one duplicate URL)
    insert_queries = [q for q in cursor.executed_queries if "INSERT INTO applicants" in q]
    assert len(insert_queries) == 3, f"Expected 3 INSERT attempts, got {len(insert_queries)}"
    
    # Only 2 entries should be inserted due to duplicate URL prevention
    assert len(cursor.executed_params) == 2, f"Expected 2 unique entries inserted, got {len(cursor.executed_params)}"
    
    # Verify correct entries were inserted (first occurrence of duplicate URL kept)
    inserted_urls = [params[3] for params in cursor.executed_params]
    assert "https://gradcafe.com/1" in inserted_urls  # First entry
    assert "https://gradcafe.com/2" in inserted_urls  # Second entry
    assert len([url for url in inserted_urls if url == "https://gradcafe.com/1"]) == 1  # Only one instance of duplicate URL
    
    # Verify database connection operations
    assert mock_connection.committed, "Database transaction should be committed"
    assert mock_connection.closed, "Database connection should be closed"
    
    # Verify database operations sequence
    # Note: button_click commits after each individual insert operation
    expected_db_ops = [
        'CONNECT: DATABASE_URL',
        'INSERT: Computer Science, MIT - https://gradcafe.com/1',
        'INSERT: Physics, Stanford - https://gradcafe.com/2', 
        'CONFLICT IGNORED: https://gradcafe.com/1',  # Duplicate URL ignored
        'COMMIT',  # Single commit for all operations
        'CLOSE'
    ]
    assert database_operations == expected_db_ops, f"Expected {expected_db_ops}, got {database_operations}"
    
    # Verify final redirect result
    assert result == "REDIRECT_TO: URL_FOR: pages.home", f"Expected redirect to home, got {result}"
    
    # Verify is_updating is reset to False (handled by finally block)
    assert pages_module.is_updating == False, "is_updating should be reset to False"

@pytest.mark.integration
def test_end_update_analysis(sample_data, monkeypatch):
    """Test the another_button_click function from pages.py with both scenarios."""
    from src.website.pages import another_button_click
    import src.website.pages as pages_module
    
    # Test both scenarios: when is_updating is True and False
    
    # === SCENARIO 1: When is_updating is True ===
    flash_messages = []
    run_queries_called_scenario1 = []
    
    def mock_flash(message):
        flash_messages.append(message)
    
    def mock_redirect(url):
        return f"REDIRECT_TO: {url}"
    
    def mock_url_for(endpoint):
        return f"URL_FOR: {endpoint}"
    
    def mock_run_queries_scenario1():
        # This IS called even when is_updating is True
        run_queries_called_scenario1.append("run_queries")
        return {"warning": "analysis_with_update_in_progress"}
    
    # Apply mocks
    monkeypatch.setattr('src.website.pages.flash', mock_flash)
    monkeypatch.setattr('src.website.pages.redirect', mock_redirect)
    monkeypatch.setattr('src.website.pages.url_for', mock_url_for)
    monkeypatch.setattr('src.website.pages.run_queries', mock_run_queries_scenario1)
    
    # Set is_updating to True
    monkeypatch.setattr('src.website.pages.is_updating', True)
    
    # Execute the function when is_updating is True
    result = another_button_click()
    
    # Verify behavior when is_updating is True
    # Note: Function still executes run_queries() and redirects even when is_updating=True
    # It just adds an additional flash message as a warning
    assert len(flash_messages) == 1, f"Expected 1 flash message when is_updating=True, got {len(flash_messages)}"
    assert flash_messages[0] == "Please wait. Data pull is still in progress.", f"Expected specific flash message, got {flash_messages[0]}"
    assert len(run_queries_called_scenario1) == 1, f"Expected run_queries to be called even when is_updating=True, got {len(run_queries_called_scenario1)}"
    assert result == "REDIRECT_TO: URL_FOR: pages.home", f"Expected redirect to home even when is_updating=True, got {result}"
    
    # === SCENARIO 2: When is_updating is False ===
    # Reset tracking variables
    flash_messages.clear()
    run_queries_called = []
    
    def mock_run_queries_scenario2():
        run_queries_called.append("run_queries")
        return {"test": "analysis_data", "entries": sample_data}
    
    # Update the run_queries mock for scenario 2
    monkeypatch.setattr('src.website.pages.run_queries', mock_run_queries_scenario2)
    
    # Set is_updating to False
    monkeypatch.setattr('src.website.pages.is_updating', False)
    
    # Execute the function when is_updating is False
    result = another_button_click()
    
    # Verify behavior when is_updating is False
    assert len(flash_messages) == 0, f"Expected no flash messages when is_updating=False, got {flash_messages}"
    assert len(run_queries_called) == 1, f"Expected run_queries to be called once when is_updating=False, got {len(run_queries_called)}"
    assert run_queries_called[0] == "run_queries", f"Expected run_queries to be called, got {run_queries_called}"
    assert result == "REDIRECT_TO: URL_FOR: pages.home", f"Expected redirect to home, got {result}"
    
    # Verify is_updating state is unchanged (function doesn't modify it)
    assert pages_module.is_updating == False, "is_updating should remain False"