import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from requests import head
from selenium.webdriver.common.by import By


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

# Navigate to the webpage you want to test
driver.get('http://localhost:5001')

# Find all <a> tags on the page
links = driver.find_elements(By.TAG_NAME, 'a')

broken_links = 0
for link in links:
    try:
        url = link.get_attribute('href')
        # Use the requests library to send a HEAD request
        response = head(url, timeout=30)
        # Check if the link is broken based on HTTP status code
        if response.status_code >= 400:
            print(f'Broken link found: {url} with status code {response.status_code}')
            broken_links += 1
    except Exception as e:
        print(f'Error checking link {url}: {e}')

print(f'Total broken links found: {broken_links}')

# Clean up by closing the browser
driver.quit()