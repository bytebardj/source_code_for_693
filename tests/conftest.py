import pytest
from unittest.mock import patch, MagicMock
from app import app
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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

def selenium_driver():
    driver = webdriver.Chrome()  # You can change this to other browsers if needed
    yield driver
    driver.quit()

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

def test_webapp_functionality():
    # Setup WebDriver (e.g., Chrome)
    driver = webdriver.Chrome()
    
    try:
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
        
        # Add more test scenarios here
        
        # Assert expected results
        assert "Dashboard" in driver.title
        
    finally:
        # Cleanup
        driver.quit()

if __name__ == "__main__":
    test_webapp_functionality()

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