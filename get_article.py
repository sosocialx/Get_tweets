import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_article(url):
    # Set up Chrome options for Selenium (this will open the Chrome window)
    chrome_options = Options()
    # Ensure Chrome window is visible
    # chrome_options.add_argument("--headless")  # Ensure this is not included
    
    # Automatically manage the ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the URL
    driver.get(url)
    
    # Wait for the page to load
    time.sleep(5)

    # Accept cookies if there’s a pop-up
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            if 'accept' in button.text.lower():
                button.click()
                print("Cookies accepted.")
                break
    except Exception as e:
        print("Could not find the accept button:", e)

    # Wait for a few seconds after accepting cookies
    time.sleep(3)

    # Extract the article text or the main content from the page
    try:
        # Assuming the article content is in a specific container (like <article> or <div>)
        article = driver.find_element(By.CSS_SELECTOR, "article")  # You can adjust this selector

        # Extract the visible text
        article_text = article.text
        
        # Define the cutoff text to exclude unwanted content
        cutoff_text = "Want to publish your own Article?"
        
        # Find the index where cutoff_text appears
        cutoff_index = article_text.find(cutoff_text)
        
        # If cutoff_text is found, slice the article text up to the cutoff point
        if cutoff_index != -1:
            article_text = article_text[:cutoff_index]
        
        print("Extracted Article Text (before cutoff):")
        print(article_text)  # Print or process the extracted text

    except Exception as e:
        print(f"Error extracting text: {e}")
    
    # Close the driver
    driver.quit()

    return article_text

# Example usage
#url = 'https://x.com/Defi0xJeff/status/1882488069917721073'  # Your provided URL
#article_text = extract_article_text(url)

# You can now use `article_text` for further processing
