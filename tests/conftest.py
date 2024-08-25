import pytest
from app import app

@pytest.fixture
def client():
    app = app()  # Create an instance of webapp
    app.config['TESTING'] = True  # Enable testing mode
    with app.test_client() as client:
        yield client
#