from unittest.mock import patch
from app import app

@patch('app.views.getCursor')
def test_homepage(mock_getCursor, client):
    # Mock the return value of the database cursor to avoid real DB calls
    mock_getCursor.return_value = None

    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data
