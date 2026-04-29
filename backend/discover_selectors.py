import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def discover_selectors():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        url = "https://www.google.com/maps/search/restaurants+in+New+York"
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(10) # Give extra time for 'limited view' to settle
        
        print("\n--- Listing Discovery ---")
        # Find all absolute links and their containers
        links = driver.find_elements(By.TAG_NAME, "a")
        found_count = 0
        for link in links:
            href = link.get_attribute("href") or ""
            aria = link.get_attribute("aria-label") or ""
            cls = link.get_attribute("class") or ""
            
            if "/maps/place/" in href or aria:
                print(f"LINK: {href[:60]}... | ARIA: {aria} | CLASS: {cls}")
                found_count += 1
                if found_count > 20: break

        print("\n--- Role Discovery ---")
        roles = ["article", "button", "link", "listitem"]
        for role in roles:
            els = driver.find_elements(By.CSS_SELECTOR, f"[role='{role}']")
            if els:
                print(f"ROLE '{role}': Found {len(els)} elements")
                for el in els[:3]:
                    print(f"  - Text: {el.text[:50]}... | Class: {el.get_attribute('class')}")

    finally:
        driver.quit()

if __name__ == "__main__":
    discover_selectors()
