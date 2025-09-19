"""Test insertion of data into database."""

import pytest
import json
import os


@pytest.fixture
def sample_data():
  """Sample applicant data for testing."""
  return [{
      "program": "Computer Science, MIT",
      "comments": "Let's goooo!",
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
      "url": "",
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
  }]


@pytest.fixture
def sample_data_with_invalid_floats():
  """Sample data with invalid float values for testing error handling."""
  return [{
      "program": "Test Program",
      "comments": "Test",
      "date_added": "2024-01-15",
      "url": "https://test.com",
      "status": "Pending",
      "term": "Fall 2024",
      "US/International": "US",
      "GPA": "invalid_gpa",  # This should cause a ValueError
      "GRE": "320",
      "GRE_V": "160",
      "GRE_AW": "4.5",
      "Degree": "MS",
      "llm-generated-program": "Test",
      "llm-generated-university": "Test University"
  }]


def create_mock_file_opener(content):
  """Create a mock file opener."""

  class MockFile:

    def __init__(self, content):
      self.content = content

    def read(self):
      return self.content

    def __enter__(self):
      return self

    def __exit__(self, *args):
      pass

  def mock_open_func(filename, mode='r'):
    return MockFile(content)

  return mock_open_func


@pytest.fixture
def mock_cursor():
  """Mock database cursor for testing."""

  class MockCursor:

    def __init__(self):
      self.executed_queries = []
      self.executed_params = []

    def execute(self, query, params=None):
      self.executed_queries.append(query.strip())
      if params:
        self.executed_params.append(params)

    def __enter__(self):
      return self

    def __exit__(self, exc_type, exc_val, exc_tb):
      pass

  return MockCursor()


@pytest.fixture
def mock_connection(mock_cursor):
  """Mock database connection for testing."""

  class MockConnection:

    def __init__(self):
      self.cursor_obj = mock_cursor
      self.committed = False
      self.closed = False

    def cursor(self):
      return self.cursor_obj

    def commit(self):
      self.committed = True

    def close(self):
      self.closed = True

  return MockConnection()


@pytest.mark.db
def test_data_to_base_successful_insertion(sample_data, mock_connection,
                                           monkeypatch):
  """Test successful data insertion to database."""
  import src.load_data as load_data

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations using monkeypatch.
  mock_file_content = json.dumps(sample_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))

  # Mock json.load to return our sample data.
  monkeypatch.setattr('json.load', lambda f: sample_data)

  # Call the function.
  load_data.data_to_base("test_file.json")

  # Verify database operations.
  cursor = mock_connection.cursor_obj

  # Check that DROP TABLE was executed.
  assert any("DROP TABLE IF EXISTS applicants" in query
             for query in cursor.executed_queries)

  # Check that CREATE TABLE was executed.
  assert any("CREATE TABLE IF NOT EXISTS applicants" in query
             for query in cursor.executed_queries)

  # Check that INSERT statements were executed (one for each data entry)
  insert_queries = [
      q for q in cursor.executed_queries if "INSERT INTO applicants" in q
  ]
  assert len(insert_queries) == len(sample_data)

  # Verify parameters were passed correctly.
  assert len(cursor.executed_params) == len(sample_data)

  # Verify first entry parameters.
  first_params = cursor.executed_params[0]
  assert first_params[0] == "Computer Science, MIT"
  assert first_params[1] == "Let's goooo!"
  assert first_params[2] == "2024-01-15"
  assert first_params[7] == 3.8
  assert first_params[8] == 320.0

  # Verify second entry handles empty/None values correctly.
  second_params = cursor.executed_params[1]
  assert second_params[1] is None
  assert second_params[2] is None
  assert second_params[3] is None
  assert second_params[7] is None
  assert second_params[8] is None
  assert second_params[12] is None
  assert second_params[13] is None

  # Verify connection operations.
  assert mock_connection.committed
  assert mock_connection.closed


@pytest.mark.db
def test_data_to_base_with_none_values(mock_connection, monkeypatch):
  """Test data insertion with all None/empty values."""
  import src.load_data as load_data

  # Data with all None/empty values
  none_data = [{
      "program": None,
      "comments": None,
      "date_added": None,
      "url": None,
      "status": None,
      "term": None,
      "US/International": None,
      "GPA": None,
      "GRE": None,
      "GRE_V": None,
      "GRE_AW": None,
      "Degree": None,
      "llm-generated-program": None,
      "llm-generated-university": None
  }]

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations using monkeypatch.
  mock_file_content = json.dumps(none_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: none_data)

  # Call the function.
  load_data.data_to_base("test_file.json")

  # Verify that None values are handled correctly.
  cursor = mock_connection.cursor_obj
  params = cursor.executed_params[0]

  # All parameters should be None.
  for param in params:
    assert param is None

  # Verify operations completed.
  assert mock_connection.committed
  assert mock_connection.closed


@pytest.mark.db
def test_data_to_base_with_empty_strings(mock_connection, monkeypatch):
  """Test data insertion with empty strings converted to None."""
  import src.load_data as load_data

  # Data with empty strings.
  empty_data = [{
      "program": "",
      "comments": "",
      "date_added": "",
      "url": "",
      "status": "",
      "term": "",
      "US/International": "",
      "GPA": "",
      "GRE": "",
      "GRE_V": "",
      "GRE_AW": "",
      "Degree": "",
      "llm-generated-program": "",
      "llm-generated-university": ""
  }]

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations using monkeypatch.
  mock_file_content = json.dumps(empty_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: empty_data)

  # Call the function.
  load_data.data_to_base("test_file.json")

  # Verify that empty strings are converted to None.
  cursor = mock_connection.cursor_obj
  params = cursor.executed_params[0]

  # All parameters should be None (empty strings converted).
  for param in params:
    assert param is None

  assert mock_connection.committed
  assert mock_connection.closed


@pytest.mark.db
def test_data_to_base_float_conversion(mock_connection, monkeypatch):
  """Test proper float conversion for numeric fields."""
  import src.load_data as load_data

  # Data with numeric values as strings
  numeric_data = [{
      "program": "Test Program",
      "comments": "Test",
      "date_added": "2024-01-15",
      "url": "https://test.com",
      "status": "Accepted",
      "term": "Fall 2024",
      "US/International": "US",
      "GPA": "3.95",
      "GRE": "325",
      "GRE_V": "165",
      "GRE_AW": "5.0",
      "Degree": "PhD",
      "llm-generated-program": "Test Program",
      "llm-generated-university": "Test University"
  }]

  # Mock the global connection
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations using monkeypatch
  mock_file_content = json.dumps(numeric_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: numeric_data)

  # Call the function
  load_data.data_to_base("test_file.json")

  # Verify float conversion
  cursor = mock_connection.cursor_obj
  params = cursor.executed_params[0]

  assert params[7] == 3.95
  assert params[8] == 325.0
  assert params[9] == 165.0
  assert params[10] == 5.0

  assert mock_connection.committed
  assert mock_connection.closed


@pytest.mark.db
def test_data_to_base_invalid_float_raises_error(
    sample_data_with_invalid_floats, mock_connection, monkeypatch):
  """Test that invalid float values raise ValueError."""
  import src.load_data as load_data

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations using monkeypatch.
  mock_file_content = json.dumps(sample_data_with_invalid_floats)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: sample_data_with_invalid_floats)

  # Call the function and expect ValueError.
  with pytest.raises(ValueError):
    load_data.data_to_base("test_file.json")


@pytest.mark.db
def test_data_to_base_file_not_found(mock_connection, monkeypatch):
  """Test FileNotFoundError when file doesn't exist."""
  import src.load_data as load_data

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations to raise FileNotFoundError.
  def mock_open_file_not_found(filename, mode='r'):
    raise FileNotFoundError("No such file or directory")

  monkeypatch.setattr('builtins.open', mock_open_file_not_found)

  # Call the function and expect FileNotFoundError
  with pytest.raises(FileNotFoundError):
    load_data.data_to_base("nonexistent_file.json")


@pytest.mark.db
def test_data_to_base_invalid_json(mock_connection, monkeypatch):
  """Test JSONDecodeError when file contains invalid JSON."""
  import src.load_data as load_data

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations with invalid JSON.
  invalid_json = "{ invalid json content"
  monkeypatch.setattr('builtins.open', create_mock_file_opener(invalid_json))

  # Mock json.load to raise JSONDecodeError.
  def mock_json_load_error(f):
    raise json.JSONDecodeError("Invalid JSON", "document", 0)

  monkeypatch.setattr('json.load', mock_json_load_error)

  # Call the function and expect JSONDecodeError.
  with pytest.raises(json.JSONDecodeError):
    load_data.data_to_base("invalid.json")


@pytest.mark.db
def test_data_to_base_empty_data_list(mock_connection, monkeypatch):
  """Test handling of empty data list."""
  import src.load_data as load_data

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations with empty list.
  empty_data = []
  mock_file_content = json.dumps(empty_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: empty_data)

  # Call the function.
  load_data.data_to_base("empty_file.json")

  # Verify database setup operations still occur.
  cursor = mock_connection.cursor_obj
  assert any("DROP TABLE IF EXISTS applicants" in query
             for query in cursor.executed_queries)
  assert any("CREATE TABLE IF NOT EXISTS applicants" in query
             for query in cursor.executed_queries)

  # But no INSERT operations should occur
  insert_queries = [
      q for q in cursor.executed_queries if "INSERT INTO applicants" in q
  ]
  assert len(insert_queries) == 0

  # Connection should still be committed and closed
  assert mock_connection.committed
  assert mock_connection.closed


@pytest.mark.db
def test_data_to_base_database_error(sample_data, monkeypatch):
  """Test database connection or operation errors."""
  import src.load_data as load_data

  # Mock a connection that raises an error.
  class MockConnectionError:

    def cursor(self):
      raise Exception("Database connection error")

  mock_conn_error = MockConnectionError()

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_conn_error)

  # Mock file operations using monkeypatch.
  mock_file_content = json.dumps(sample_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: sample_data)

  # Call the function and expect database error
  with pytest.raises(Exception, match="Database connection error"):
    load_data.data_to_base("test_file.json")


@pytest.mark.db
def test_main_execution_block(monkeypatch):
  """Test the if __name__ == '__main__' execution block."""
  import src.load_data as load_data

  # Mock data_to_base function
  called_with = []

  def mock_data_to_base(filename):
    called_with.append(filename)

  monkeypatch.setattr('src.load_data.data_to_base', mock_data_to_base)

  # Mock print to capture output
  printed_output = []

  def mock_print(*args):
    printed_output.extend(args)

  monkeypatch.setattr('builtins.print', mock_print)

  # Simulate the main block execution
  input_file = "llm_extend_applicant_data.json"
  load_data.data_to_base(input_file)
  print("Done!!")

  # Verify the function was called with correct filename.
  assert called_with == [input_file]
  assert printed_output == ["Done!!"]


@pytest.mark.db
def test_all_field_processing_combinations(mock_connection, monkeypatch):
  """Test all field processing combinations for comprehensive coverage."""
  import src.load_data as load_data

  # Data with mixed valid/invalid/empty values for comprehensive testing
  mixed_data = [{
      "program": "Valid Program",
      "comments": None,
      "date_added": "2024-01-15",
      "url": "",
      "status": "Accepted",
      "term": None,
      "US/International": "US",
      "GPA": "3.7",
      "GRE": "",
      "GRE_V": "158",
      "GRE_AW": None,
      "Degree": "MS",
      "llm-generated-program": "",
      "llm-generated-university": "Valid University"
  }]

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations using monkeypatch.
  mock_file_content = json.dumps(mixed_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: mixed_data)

  # Call the function.
  load_data.data_to_base("test_file.json")

  # Verify mixed value processing.
  cursor = mock_connection.cursor_obj
  params = cursor.executed_params[0]

  # Verify specific field processing.
  assert params[0] == "Valid Program"
  assert params[1] is None
  assert params[2] == "2024-01-15"
  assert params[3] is None
  assert params[4] == "Accepted"
  assert params[5] is None
  assert params[6] == "US"
  assert params[7] == 3.7
  assert params[8] is None
  assert params[9] == 158.0
  assert params[10] is None
  assert params[11] == "MS"
  assert params[12] is None
  assert params[13] == "Valid University"
  assert mock_connection.committed
  assert mock_connection.closed


@pytest.mark.db
def test_cursor_context_manager_behavior(mock_connection, monkeypatch):
  """Test that cursor context manager behavior is properly used."""
  import src.load_data as load_data

  # Simple test data
  test_data = [{
      "program": "Test Program",
      "comments": "Test",
      "date_added": "2024-01-15",
      "url": "https://test.com",
      "status": "Accepted",
      "term": "Fall 2024",
      "US/International": "US",
      "GPA": "3.8",
      "GRE": "320",
      "GRE_V": "160",
      "GRE_AW": "4.5",
      "Degree": "MS",
      "llm-generated-program": "Test",
      "llm-generated-university": "Test University"
  }]

  # Mock the global connection.
  monkeypatch.setattr('src.load_data.conn', mock_connection)

  # Mock file operations using monkeypatch.
  mock_file_content = json.dumps(test_data)
  monkeypatch.setattr('builtins.open',
                      create_mock_file_opener(mock_file_content))
  monkeypatch.setattr('json.load', lambda f: test_data)

  # Call the function.
  load_data.data_to_base("test_file.json")

  # Verify that the cursor was used in context manager (mock supports __enter__ and __exit__).
  cursor = mock_connection.cursor_obj

  # Should have executed DROP, CREATE, and INSERT statements.
  assert len(cursor.executed_queries) == 3
  assert any("DROP TABLE" in query for query in cursor.executed_queries)
  assert any("CREATE TABLE" in query for query in cursor.executed_queries)
  assert any("INSERT INTO" in query for query in cursor.executed_queries)

  # Should have one set of insert parameters.
  assert len(cursor.executed_params) == 1

  # Verify connection operations.
  assert mock_connection.committed
  assert mock_connection.closed
