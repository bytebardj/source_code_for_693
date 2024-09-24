import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
from selenium.webdriver.chrome.options import Options

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://localhost:5001')

@pytest.fixture(scope="module")
def driver():
    options = Options()
    # Comment out the headless option for debugging
    # options.add_argument('--headless')  
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-software-rasterizer')  # Additional option
    options.add_argument('--enable-logging')  # Enable logging
    options.add_argument('--v=1')  # Verbose logging

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        yield driver
    except WebDriverException as e:
        pytest.skip(f"Could not initialize WebDriver: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

@pytest.mark.timeout(60)  # Increased timeout for each test
def test_home_page(driver):
    print("Navigating to home page...")
    driver.get(f"{BASE_URL}/")
    print("Checking page title...")
    assert "Your Website Title" in driver.title

@pytest.mark.timeout(60)
def test_product_list(driver):
    print("Navigating to product list...")
    driver.get(f"{BASE_URL}/products")
    wait = WebDriverWait(driver, 20)  # Increased wait time
    products = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product")))
    print(f"Found {len(products)} products.")
    assert len(products) > 0

@pytest.mark.timeout(60)
def test_add_to_cart(driver):
    print("Navigating to products...")
    driver.get(f"{BASE_URL}/products")
    wait = WebDriverWait(driver, 20)  # Increased wait time
    add_to_cart_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product .add-to-cart")))
    print("Clicking 'Add to Cart' button...")
    add_to_cart_button.click()
    
    cart_count = wait.until(EC.presence_of_element_located((By.ID, "cart-count")))
    print(f"Cart count is now: {cart_count.text}")
    assert int(cart_count.text) > 0

@pytest.mark.timeout(60)
def test_checkout_process(driver):
    print("Navigating to products for checkout...")
    driver.get(f"{BASE_URL}/products")
    wait = WebDriverWait(driver, 20)  # Increased wait time
    add_to_cart_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product .add-to-cart")))
    add_to_cart_button.click()
    
    print("Navigating to cart...")
    driver.get(f"{BASE_URL}/cart")
    checkout_button = wait.until(EC.element_to_be_clickable((By.ID, "checkout-button")))
    print("Clicking 'Checkout' button...")
    checkout_button.click()
    
    wait.until(EC.presence_of_element_located((By.ID, "checkout-form")))
    print("Filling out checkout form...")
    driver.find_element(By.ID, "name").send_keys("John Doe")
    driver.find_element(By.ID, "email").send_keys("john@example.com")
    driver.find_element(By.ID, "address").send_keys("123 Test St")
    driver.find_element(By.ID, "submit-order").click()
    
    confirmation = wait.until(EC.presence_of_element_located((By.ID, "order-confirmation")))
    print("Checking order confirmation...")
    assert "Thank you for your order" in confirmation.text
