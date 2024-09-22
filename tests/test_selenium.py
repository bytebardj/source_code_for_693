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


options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Set an explicit timeout for all browser interactions
driver.set_page_load_timeout(60)
driver.implicitly_wait(30)

# Example: Wait until an element is present
element = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.NAME, "q"))
)

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://localhost:5000')

@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        yield driver
    except WebDriverException as e:
        pytest.skip(f"Could not initialize WebDriver: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

@pytest.mark.timeout(10)
def test_home_page(driver):
    try:
        driver.get(f"{BASE_URL}/")
        assert "Your Website Title" in driver.title
    except TimeoutException:
        pytest.fail("Timed out waiting for home page to load")

@pytest.mark.timeout(10)
def test_product_list(driver):
    try:
        driver.get(f"{BASE_URL}/products")
        wait = WebDriverWait(driver, 5)
        products = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product")))
        assert len(products) > 0
    except TimeoutException:
        pytest.fail("Timed out waiting for products to load")

@pytest.mark.timeout(10)
def test_add_to_cart(driver):
    try:
        driver.get(f"{BASE_URL}/products")
        wait = WebDriverWait(driver, 5)
        add_to_cart_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product .add-to-cart")))
        add_to_cart_button.click()
        
        cart_count = wait.until(EC.presence_of_element_located((By.ID, "cart-count")))
        assert int(cart_count.text) > 0
    except TimeoutException:
        pytest.fail("Timed out during add to cart process")

@pytest.mark.timeout(15)
def test_checkout_process(driver):
    try:
        driver.get(f"{BASE_URL}/products")
        wait = WebDriverWait(driver, 5)
        add_to_cart_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product .add-to-cart")))
        add_to_cart_button.click()
        
        driver.get(f"{BASE_URL}/cart")
        checkout_button = wait.until(EC.element_to_be_clickable((By.ID, "checkout-button")))
        checkout_button.click()
        
        wait.until(EC.presence_of_element_located((By.ID, "checkout-form")))
        driver.find_element(By.ID, "name").send_keys("John Doe")
        driver.find_element(By.ID, "email").send_keys("john@example.com")
        driver.find_element(By.ID, "address").send_keys("123 Test St")
        driver.find_element(By.ID, "submit-order").click()
        
        confirmation = wait.until(EC.presence_of_element_located((By.ID, "order-confirmation")))
        assert "Thank you for your order" in confirmation.text
    except TimeoutException:
        pytest.fail("Timed out during checkout process")
