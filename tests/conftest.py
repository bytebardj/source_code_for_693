import pytest
from unittest.mock import patch, MagicMock
from app import app
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import coverage
import os

# Determine the root directory of your project
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Start coverage before any tests run
cov = coverage.Coverage(source=[os.path.join(root_dir, 'app')])
cov.start()

@pytest.fixture(scope='session', autouse=True)
def setup_coverage(request):
    """Set up coverage for all tests."""
    yield
    # Stop coverage after all tests have run
    cov.stop()
    cov.save()
    cov.html_report(directory=os.path.join(root_dir, 'coverage_html'))
    cov.xml_report(outfile=os.path.join(root_dir, 'coverage.xml'))

@pytest.fixture
def selenium_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()

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

def test_webapp_functionality(selenium_driver):
    driver = selenium_driver
    
    # Navigate to your webapp
    driver.get("http://127.0.0.1:5000/")
    
    # Test scenario 1: Login
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-button")
    
    username_field.send_keys("your_username")
    password_field.send_keys("your_password")
    login_button.click()
    
    # Wait for successful login (e.g., dashboard page load)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "dashboard"))
    )
    
    # Assert expected results
    assert "Dashboard" in driver.title

def test_product_search(selenium_driver):
    driver = selenium_driver
    
    # Navigate to the products page
    driver.get("http://127.0.0.1:5000/products")
    
    # Find the search input and submit a search
    search_input = driver.find_element(By.ID, "search-input")
    search_input.send_keys("Product 1")
    search_input.submit()
    
    # Wait for search results
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
    )
    
    # Assert that the search results contain the expected product
    assert "Product 1" in driver.page_source

# Add these new test functions

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
    assert response.status_code == 302  # Assuming redirect after update
    
    # Check if profile was updated
    response = client.get('/profile')
    assert b"newemail@example.com" in response.data
    assert b"This is a new bio" in response.data