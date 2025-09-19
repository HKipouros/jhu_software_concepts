"""This module contains unit testing for webpage buttons and busy-state behavior."""

import pytest
import re
from src.website.app import app
from src.website import pages


# Fixture to return client object
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# Part A: Test Pull Data button.


@pytest.mark.buttons
def test_button_click_route(client):
    """Test that first button (Pull Data) loads properly (code 200)."""
    response = client.post("/button-click", follow_redirects=True)
    assert response.status_code == 200


@pytest.mark.buttons
def test_button_click_functionality_success(client, monkeypatch):
    """Test first button (Pull Data) functionality with successful data processing using monkeypatch."""

    from src.website import pages
    original_state = pages.is_updating
    pages.is_updating = False

    # Mock database connection.
    class MockCursor:

        def execute(self, query, params=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockConnection:

        def cursor(self):
            return MockCursor()

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr('src.website.pages.psycopg.connect',
                        lambda x: MockConnection())

    try:

        response = client.post("/button-click")

        assert response.status_code in [200, 302]

        if response.status_code == 302:
            assert "/" in response.location or "pages" in response.location

    finally:
        pages.is_updating = original_state


@pytest.mark.buttons
def test_button_click_when_already_updating(client, monkeypatch):
    """Test first button (Pull Data) when is_updating is already True."""

    # Import pages in the test to ensure fresh state.
    from src.website import pages

    # Store original value and set to True.
    original_updating = pages.is_updating
    pages.is_updating = True

    try:

        response = client.post("/button-click")

        assert response.status_code in [200, 302]
        if response.status_code == 200:
            assert b"Update is already in progress" in response.data

    finally:
        # Always reset the state.
        pages.is_updating = original_updating


@pytest.mark.buttons
def test_button_click_basic_functionality(client, monkeypatch):
    """Test first button (Pull Data) basic functionality and response."""

    from src.website import pages
    original_updating = pages.is_updating
    pages.is_updating = False

    try:

        response = client.post("/button-click")

        assert response.status_code in [200, 302]

        assert pages.is_updating == False

    finally:
        pages.is_updating = original_updating


@pytest.mark.buttons
def test_button_click_with_mocked_scraper(client, monkeypatch):
    """Test first button (Pull Data) with mocked scraper returning no data."""

    from src.website import pages
    original_updating = pages.is_updating
    pages.is_updating = False

    # Mock the scraper to return empty results.
    def mock_updated_scrape(recent_id):
        return []  # No new entries

    monkeypatch.setattr('src.website.pages.updated_scrape',
                        mock_updated_scrape)

    try:
        response = client.post("/button-click")

        assert response.status_code in [200, 302]

        assert pages.is_updating == False

    finally:
        pages.is_updating = original_updating


@pytest.mark.buttons
def test_button_click_global_state_management(client, monkeypatch):
    """Test that first button (Pull Data) properly manages the is_updating global state."""

    from src.website import pages
    original_updating = pages.is_updating

    pages.is_updating = False

    try:
        response = client.post("/button-click")

        assert response.status_code in [200, 302]

        assert pages.is_updating == False

    finally:
        pages.is_updating = original_updating


@pytest.mark.buttons
def test_button_click_handles_concurrent_requests(client):
    """Test that first button (Pull Data) can handle multiple requests appropriately."""
    responses = []
    for i in range(3):
        response = client.post("/button-click")
        responses.append(response)

    for response in responses:
        assert response.status_code in [200, 302]


@pytest.mark.buttons
def test_button_click_preserves_global_state(client, monkeypatch):
    """Test that first button (Pull Data) preserves and manages global state correctly."""
    from src.website import pages

    original_state = getattr(pages, 'is_updating', False)

    try:
        pages.is_updating = False

        response = client.post("/button-click")

        assert response.status_code in [200, 302]

        assert pages.is_updating == False

    finally:
        pages.is_updating = original_state


@pytest.mark.buttons
def test_mock_database_connection(client, monkeypatch):
    """Test first button (Pull Data) with mocked database connection."""
    from src.website import pages

    original_state = pages.is_updating
    pages.is_updating = False

    # Mock the database connection.
    connection_calls = []

    class MockConnection:

        def __init__(self, *args, **kwargs):
            connection_calls.append("connect")

        def cursor(self):
            return MockCursor()

        def commit(self):
            connection_calls.append("commit")

        def close(self):
            connection_calls.append("close")

    class MockCursor:

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, *args):
            connection_calls.append("execute")

    # Apply the mock.
    monkeypatch.setattr('src.website.pages.psycopg.connect', MockConnection)

    try:

        response = client.post("/button-click")

        assert response.status_code in [200, 302]

        if connection_calls:
            assert "connect" in connection_calls

    finally:
        pages.is_updating = original_state


# Part B: Test second button (Update Analysis)
@pytest.mark.buttons
def test_another_button_click_returns_200_when_not_updating(
        client, monkeypatch):
    """Test that another_button_click returns 200 when is_updating is false."""

    from src.website import pages
    original_updating = pages.is_updating
    pages.is_updating = False

    # Mock run_queries to prevent actual database calls.
    monkeypatch.setattr('src.website.pages.run_queries',
                        lambda: ["mock_query_data"])

    try:
        # Make the POST request to another-button-click route.
        response = client.post("/another-button-click", follow_redirects=True)

        # Verify it returns 200 when is_updating is false.
        assert response.status_code == 200

    finally:
        pages.is_updating = original_updating


# Part C: Test busy gating.


@pytest.mark.buttons
def test_button_click_busy_gating_simple(client, monkeypatch):
    """Test Pull Data button busy state."""

    from src.website import pages
    original_updating = pages.is_updating

    # Mock run_queries to prevent actual database calls.
    monkeypatch.setattr('src.website.pages.run_queries',
                        lambda: ["mock_query_data"])

    try:
        # Test when busy.
        pages.is_updating = True
        response = client.post("/button-click")
        assert response.status_code in [200, 302]

        # Reset for non-busy state.
        pages.is_updating = False
        response2 = client.post("/button-click")
        assert response2.status_code in [200, 302]

    finally:
        pages.is_updating = original_updating


@pytest.mark.buttons
def test_another_button_click_busy_vs_normal(client, monkeypatch):
    """Test Update Analysis button busy state."""

    from src.website import pages
    original_updating = pages.is_updating

    # Mock run_queries to prevent actual database calls.
    monkeypatch.setattr('src.website.pages.run_queries',
                        lambda: ["mock_query_data"])

    try:
        # Test when busy
        pages.is_updating = True
        response_busy = client.post("/another-button-click",
                                    follow_redirects=True)
        assert response_busy.status_code == 200

        # Test when not busy.
        pages.is_updating = False
        response_normal = client.post("/another-button-click",
                                      follow_redirects=True)
        assert response_normal.status_code == 200

    finally:
        pages.is_updating = original_updating
