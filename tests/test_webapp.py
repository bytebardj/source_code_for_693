import pytest
from flask import url_for
import time

def test_home_page(client):
    """Test that the home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    # Update this to match your actual home page content
    assert b"Your actual home page content" in response.data

def test_product_list(client):
    """Test that the product list page loads and contains expected data"""
    response = client.get('/products')
    assert response.status_code == 200
    # Update these assertions to match your actual product list content
    assert b"Product list identifier" in response.data

@pytest.mark.parametrize("product_id, expected_name", [
    (1, "Product 1"),
    (2, "Product 2"),
])
def test_product_detail(client, product_id, expected_name):
    """Test that individual product pages load correctly"""
    response = client.get(f'/product/{product_id}')
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
    assert b"Cart page identifier" in response.data

def test_checkout_process(client):
    """Test the checkout process"""
    # Add item to cart
    client.post('/add-to-cart', data={'product_id': 1, 'quantity': 1})
    
    # Start checkout
    response = client.get('/checkout')
    assert response.status_code == 200
    assert b"Checkout page identifier" in response.data
    
    # Submit order
    response = client.post('/place-order', data={
        'name': 'John Doe',
        'address': '123 Test St',
        'payment_method': 'credit_card'
    })
    assert response.status_code in [200, 302]  # Accept either OK or redirect

def test_search_functionality(client):
    """Test the search functionality"""
    response = client.get('/search?q=Product+1')
    assert response.status_code == 200
    # Update these assertions to match your actual search results
    assert b"Search results identifier" in response.data

def test_invalid_route(client):
    """Test that an invalid route returns a 404 error"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404

@pytest.mark.timeout(5)  # Set a 5-second timeout for this test
def test_user_registration(client):
    """Test user registration process"""
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'securepassword'
    })
    assert response.status_code in [200, 302]  # Accept either OK or redirect

@pytest.mark.timeout(5)  # Set a 5-second timeout for this test
def test_user_profile(client):
    """Test user profile page"""
    # First, log in the user
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    
    response = client.get('/profile')
    assert response.status_code == 200
    # Update these assertions to match your actual profile page content
    assert b"Profile page identifier" in response.data

@pytest.mark.timeout(5)  # Set a 5-second timeout for this test
def test_update_user_profile(client):
    """Test updating user profile"""
    # Log in the user
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    
    # Update profile
    response = client.post('/update-profile', data={
        'email': 'newemail@example.com',
        'bio': 'This is a new bio'
    })
    assert response.status_code in [200, 302]  # Accept either OK or redirect
    
    # Check if profile was updated
    response = client.get('/profile')
    assert b"newemail@example.com" in response.data
    assert b"This is a new bio" in response.data
