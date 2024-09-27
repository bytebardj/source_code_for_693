import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://localhost:5001')

@pytest.fixture(scope="module")
def driver():
    options = Options()
    # Add Firefox-specific options if needed
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    yield driver

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
