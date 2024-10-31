# server/app.py
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

@app.route('/calculate_roi', methods=['POST'])
def calculate_roi():
    data = request.get_json()
    campaign_link = data.get('campaign_link')
    repeat_listeners = data.get('repeat_listeners')

    # Initialize Chrome WebDriver using webdriver-manager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    # Navigate to the URL
    driver.get(campaign_link)

    # Optional sleep to allow content to load
    time.sleep(5)
    print("time is up")
    
    # Wait for the specific text "Post Performance" to appear on the page
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Post Performance')]"))
    )
    # Wait for the "spinner" class to disappear, indicating the page is fully loaded
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, "spinner"))
    )

    # Get the full page source once the page has fully loaded
    page_html = driver.page_source

    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(page_html, "html.parser")

    # Define a regex pattern to match dollar amounts (e.g., $100, $1,000.50)
    dollar_pattern = r"\$([0-9,]+(?:\.[0-9]{2})?)"

    # Initialize a variable to store the total spend
    total_spend = 0.0

    # Extract and process the additional element text by XPath
    additional_element = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div[3]/div[5]/div/div[2]/div/div[3]/div[2]/div")
    additional_text = additional_element.text
    total_likes = int(additional_text.replace(",", ""))

    # Process dollar amounts in each child div of `div.baTaZbx`
    target_containers = soup.select("div.baTaZbx")

    for container in target_containers:
        # Find the text content in child divs of each `baTaZbx` container
        child_divs = container.find_all("div")
        for child in child_divs:
            child_text = child.get_text()
            # Find all dollar amounts in the child text
            dollar_matches = re.findall(dollar_pattern, child_text)
            
            # Sum up each found dollar amount
            for match in dollar_matches:
                # Remove commas, convert to float, and add to total spend
                amount = float(match.replace(",", ""))
                print(f"Found amount: {amount}")
                total_spend += amount

    total_money_spent = total_spend
    driver.quit()

    # ROI Calculation
    roi = (((total_likes * 0.67 * 0.62 * 0.004 * repeat_listeners) - total_money_spent) / total_money_spent)
    return jsonify({"roi": roi})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # Ensure the port matches Render’s configuration
