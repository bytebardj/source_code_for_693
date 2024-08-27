import pytest
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        with patch('app.views.getCursor') as mock_getCursor:
            # Mock the return value of the cursor to avoid real DB calls
            mock_getCursor.return_value = None
            yield client