import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        yield driver
    finally:
        if 'driver' in locals():
            driver.quit()

def test_homepage(driver):
    driver.get('http://localhost:5001')
    assert "Your Website Title" in driver.title

def test_product_list(driver):
    driver.get('http://localhost:5001/products')
    wait = WebDriverWait(driver, 10)
    products = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product")))
    assert len(products) > 0


# Add more test functions as needed