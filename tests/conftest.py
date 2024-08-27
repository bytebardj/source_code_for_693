import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        with patch('app.views.getCursor') as mock_getCursor:
            # Create a mock cursor that returns valid results
            mock_cursor = MagicMock()
            mock_cursor.execute.return_value = None
            mock_cursor.fetchall.return_value = [('Depot 1',), ('Depot 2',)]
            mock_getCursor.return_value = mock_cursor
            yield client