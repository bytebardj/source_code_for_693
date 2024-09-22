from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import requests
from requests import head
from selenium.webdriver.common.by import By

# Initialize the Selenium driver
driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()))

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