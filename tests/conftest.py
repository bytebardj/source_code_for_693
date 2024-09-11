import pytest
from unittest.mock import patch, MagicMock
from app import app
import coverage
import os

# Initialize coverage only if it's not already running
if 'COVERAGE_PROCESS_START' not in os.environ:
    cov = coverage.Coverage(source=['app'])
    cov.start()
else:
    cov = None

@pytest.fixture(scope='session', autouse=True)
def setup_coverage(request):
    """Set up coverage for all tests."""
    yield
    # Stop coverage after all tests have run, only if we started it
    if cov:
        cov.stop()
        cov.save()
        cov.html_report(directory='coverage_html')
        cov.xml_report(outfile='coverage.xml')

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

def test_home_page(client):
    """Test that the home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to the webapp" in response.data

def test_product_list(client):
    """Test that the product list page loads and contains expected data"""
    response = client.get('/products')
    assert response.status_code == 200
    assert b"Product 1" in response.data
    assert b"Category 1" in response.data
    assert b"Price" in response.data


@pytest.mark.parametrize("product_id, expected_name", [
    (1, "Product 1"),
    (2, "Product 2"),
])

def test_add_to_cart(client):
    """Test adding a product to the cart"""
    response = client.post('/add-to-cart', data={'product_id': 1, 'quantity': 2})
    assert response.status_code == 302

def test_invalid_route(client):
    """Test that an invalid route returns a 404 error"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404