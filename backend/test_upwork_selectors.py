import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)
try:
    print("Fetching Upwork...")
    driver.get("https://www.upwork.com/nx/search/jobs?q=SaaS&sort=recency")
    time.sleep(5)
    
    html = driver.page_source
    print(f"Page size: {len(html)}")
    
    # Check for challenge
    if "challenge" in driver.current_url.lower():
        print("URL hit a challenge.")
        
    # Dump a portion of the body to see what structure we have
    with open("c:/datascrap/backend/logs/upwork_dump.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Dumped to logs/upwork_dump.html")
    
finally:
    driver.quit()
