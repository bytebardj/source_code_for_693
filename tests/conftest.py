import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        with patch('app.views.getCursor') as mock_getCursor:
            # Mock the cursor
            mock_cursor = MagicMock()
            mock_cursor.execute.return_value = None
            # Mock fetchall to return well-formed data
            mock_cursor.fetchall.return_value = [('Product 1', 'Category 1', 'Description', 'Price', 'image.png')]
            mock_getCursor.return_value = mock_cursor

            # Mock any other functions that provide data to the template
            with patch('app.views.get_depot') as mock_get_depot:
                mock_get_depot.return_value = [('Depot 1', 'Location 1', 'Manager 1')]
                yield client