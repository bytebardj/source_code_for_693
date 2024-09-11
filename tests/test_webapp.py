import pytest

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
def test_product_detail(client, product_id, expected_name):
    """Test that individual product pages load correctly"""
    response = client.get(f'/product/{product_id}')
    assert response.status_code == 200
    assert expected_name.encode() in response.data

def test_add_to_cart(client):
    """Test adding a product to the cart"""
    response = client.post('/add-to-cart', data={'product_id': 1, 'quantity': 2})
    assert response.status_code == 302  # Assuming a redirect after adding to cart

def test_view_cart(client):
    """Test viewing the cart contents"""
    # First, add an item to the cart
    client.post('/add-to-cart', data={'product_id': 1, 'quantity': 2})
    
    response = client.get('/cart')
    assert response.status_code == 200
    assert b"Product 1" in response.data
    assert b"Quantity: 2" in response.data

def test_checkout_process(client):
    """Test the checkout process"""
    # Add item to cart
    client.post('/add-to-cart', data={'product_id': 1, 'quantity': 1})
    
    # Start checkout
    response = client.get('/checkout')
    assert response.status_code == 200
    assert b"Checkout" in response.data
    
    # Submit order
    response = client.post('/place-order', data={
        'name': 'John Doe',
        'address': '123 Test St',
        'payment_method': 'credit_card'
    })
    assert response.status_code == 302  # Assuming redirect to order confirmation
    
    # Check order confirmation
    response = client.get('/order-confirmation')
    assert response.status_code == 200
    assert b"Order Confirmed" in response.data

def test_search_functionality(client):
    """Test the search functionality"""
    response = client.get('/search?q=Product+1')
    assert response.status_code == 200
    assert b"Product 1" in response.data
    assert b"No results found" not in response.data

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
    assert response.status_code == 302  # Assuming redirect after successful registration
    
    # Check if user can now log in
    response = client.post('/login', data={
        'username': 'newuser',
        'password': 'securepassword'
    })
    assert response.status_code == 302  # Assuming redirect after successful login

def test_user_profile(client):
    """Test user profile page"""
    # First, log in the user
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    
    response = client.get('/profile')
    assert response.status_code == 200
    assert b"User Profile" in response.data
    assert b"testuser" in response.data

def test_update_user_profile(client):
    """Test updating user profile"""
    # Log in the user
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    
    # Update profile
    response = client.post('/update-profile', data={
        'email': 'newemail@example.com',
        'bio': 'This is a new bio'
    })
    assert response.status_code == 302  # or 200 if it doesn't redirect
    
    # Check if profile was updated
    response = client.get('/profile')
    assert b"newemail@example.com" in response.data
    assert b"This is a new bio" in response.data
