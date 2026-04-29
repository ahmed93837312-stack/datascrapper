import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def debug_gmaps():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        url = "https://www.google.com/maps/search/restaurants+in+New+York"
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Save screenshot
        screenshot_path = "gmaps_debug_initial.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Save page source
        with open("gmaps_debug_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Page source saved to: gmaps_debug_source.html")
        
        # Check for consent screen
        print(f"Current URL: {driver.current_url}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_gmaps()
