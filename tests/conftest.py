import pytest
from app import app  # Import the Flask app instance from app/__init__.py

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client