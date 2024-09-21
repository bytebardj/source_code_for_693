import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="module")
def driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

def test_home_page(driver):
    driver.get("http://localhost:5000")  # Adjust URL as needed
    assert "Your Website Title" in driver.title

def test_product_list(driver):
    driver.get("http://localhost:5000/products")  # Adjust URL as needed
    wait = WebDriverWait(driver, 10)
    products = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product")))
    assert len(products) > 0

def test_add_to_cart(driver):
    driver.get("http://localhost:5000/products")  # Adjust URL as needed
    wait = WebDriverWait(driver, 10)
    add_to_cart_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product .add-to-cart")))
    add_to_cart_button.click()
    
    cart_count = wait.until(EC.presence_of_element_located((By.ID, "cart-count")))
    assert int(cart_count.text) > 0

def test_checkout_process(driver):
    # Add a product to cart first
    driver.get("http://localhost:5000/products")
    wait = WebDriverWait(driver, 10)
    add_to_cart_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product .add-to-cart")))
    add_to_cart_button.click()
    
    # Go to cart
    driver.get("http://localhost:5000/cart")
    checkout_button = wait.until(EC.element_to_be_clickable((By.ID, "checkout-button")))
    checkout_button.click()
    
    # Fill in checkout form
    wait.until(EC.presence_of_element_located((By.ID, "checkout-form")))
    driver.find_element(By.ID, "name").send_keys("John Doe")
    driver.find_element(By.ID, "email").send_keys("john@example.com")
    driver.find_element(By.ID, "address").send_keys("123 Test St")
    driver.find_element(By.ID, "submit-order").click()
    
    # Check for order confirmation
    confirmation = wait.until(EC.presence_of_element_located((By.ID, "order-confirmation")))
    assert "Thank you for your order" in confirmation.text
