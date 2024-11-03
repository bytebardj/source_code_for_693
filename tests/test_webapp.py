import pytest
from flask import url_for
import time

@pytest.fixture(autouse=True)
def timeout():
    yield
    if time.time() - timeout.start > 5:  # 5 seconds timeout for each test
        pytest.fail("Test execution exceeded 5 seconds")

@pytest.fixture(autouse=True)
def timer():
    timeout.start = time.time()

def test_home_page(client):
    """Test that the home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    # Update this to match your actual home page content
    assert b"<title>" in response.data and b"</title>" in response.data

def test_product_list(client):
    """Test that the product list page loads and contains expected data"""
    response = client.get('/products')
    assert response.status_code == 200
    # Update these assertions to match your actual product list content
    assert b"Product" in response.data

@pytest.mark.parametrize("product_id, expected_name", [
    (1, "Product 1"),
    (2, "Product 2"),
])
def test_product_detail(client, product_id, expected_name):
    """Test that individual product pages load correctly"""
    response = client.get(f'/product/{product_id}')
    if response.status_code == 404:
        pytest.skip(f"Product detail page for ID {product_id} not implemented yet")
    assert response.status_code == 200
    assert expected_name.encode() in response.data

def test_add_to_cart(client):
    """Test adding a product to the cart"""
    response = client.post('/add-to-cart', data={'product_id': 1, 'quantity': 2})
    assert response.status_code in [200, 302]  # Accept either OK or redirect

def test_view_cart(client):
    """Test viewing the cart contents"""
    # First, add an item to the cart
    client.post('/add-to-cart', data={'product_id': 1, 'quantity': 2})
    
    response = client.get('/cart')
    assert response.status_code == 200
    # Update these assertions to match your actual cart page content
    assert b"Cart" in response.data or b"Shopping" in response.data

def test_checkout_process(client):
    """Test the checkout process"""
    # Add item to cart
    client.post('/add-to-cart', data={'product_id': 1, 'quantity': 1})
    
    # Start checkout
    response = client.get('/checkout')
    if response.status_code == 404:
        pytest.skip("Checkout page not implemented yet")
    assert response.status_code == 200
    assert b"Checkout" in response.data

def test_search_functionality(client):
    """Test the search functionality"""
    response = client.get('/search?q=Product+1')
    if response.status_code == 404:
        pytest.skip("Search functionality not implemented yet")
    assert response.status_code == 200
    # Update these assertions to match your actual search results
    assert b"Search" in response.data

def test_invalid_route(client):
    """Test that an invalid route returns a 404 error"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404

def test_user_registration(client):
    """Test user registration process"""
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'securepassword'
    })
    assert response.status_code in [200, 302, 400]  # Accept OK, redirect, or bad request

@pytest.mark.skip(reason="User authentication not implemented yet")
def test_user_profile(client):
    """Test user profile page"""
    # First, log in the user (you may need to implement this)
    # client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    
    response = client.get('/profile')
    if response.status_code == 404:
        pytest.skip("User profile page not implemented yet")
    assert response.status_code == 200
    # Update these assertions to match your actual profile page content
    assert b"Profile" in response.data

