"""
Upwork Job Scraper Module
=========================
Scrapes Upwork job postings using standard Selenium WebDriver in headful mode to bypass Cloudflare.
Targets keywords: AI automation, AI chatbot, SaaS, web development, app development.

Fields extracted:
    - Project Title
    - Description
    - Budget
    - Client Location
    - Client Spend History (Placeholder)
    - Posted Date

Output: output/upwork_jobs.csv
"""

import os
import re
import sys
import time
import random
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.logger import setup_logger
from utils.csv_handler import write_csv

logger = setup_logger("upwork_scraper")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
KEYWORDS = [
    "AI automation",
    "AI chatbot",
    "SaaS",
    "web development",
    "app development",
]

OUTPUT_FILE = "upwork_jobs.csv"

CSV_HEADERS = [
    "Project Title",
    "Description",
    "Budget",
    "Client Location",
    "Client Spend History",
    "Posted Date",
    "Keyword",
    "URL",
]

SEARCH_URL_BASE = "https://www.upwork.com/nx/search/jobs"

MIN_DELAY = 4.0
MAX_DELAY = 8.0

class UpworkScraper:
    """
    Selenium-based Upwork backend scraper.
    """

    def __init__(self, progress_callback: Optional[callable] = None, headless: bool = True):
        self.progress_callback = progress_callback
        self.headless = headless
        self.driver = None
        self.results: list[dict] = []
        self._total_keywords = len(KEYWORDS)
        self._current = 0

    def run(self, keywords: Optional[list[str]] = None) -> list[dict]:
        run_keywords = keywords if keywords else KEYWORDS
        
        logger.info("=" * 60)
        logger.info("Upwork Scraper (Selenium Edition) — Starting")
        logger.info(f"Keywords: {', '.join(run_keywords)}")
        logger.info("=" * 60)

        self.results = []
        self._total_keywords = len(run_keywords)

        try:
            self._init_driver()

            for idx, keyword in enumerate(run_keywords, 1):
                self._current = idx
                logger.info(f"[{idx}/{self._total_keywords}] Scraping keyword: '{keyword}'")

                try:
                    jobs = self._scrape_keyword(keyword)
                    self.results.extend(jobs)
                    logger.info(f"  -> Found {len(jobs)} jobs for '{keyword}'")
                except Exception as e:
                    logger.error(f"  Error scraping '{keyword}': {e}")

                if self.progress_callback:
                    self.progress_callback(idx, self._total_keywords)

                if idx < self._total_keywords:
                    self._random_delay()

        except Exception as e:
            logger.error(f"Critical error during Upwork scraping: {e}")
        finally:
            self._quit_driver()

        # De-duplicate
        seen: set[str] = set()
        unique = []
        for job in self.results:
            url = job.get("URL", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(job)
        self.results = unique

        if self.results:
            write_csv(OUTPUT_FILE, CSV_HEADERS, self.results)
        else:
            logger.warning("No results to write — CSV not created.")

        logger.info(f"Upwork Scraper — Done. Total unique jobs: {len(self.results)}")
        return self.results

    def _init_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        
        # Hijack the user's REAL default Chrome profile to bypass Cloudflare
        user_data_path = r"C:\Users\SM\AppData\Local\Google\Chrome\User Data"
        options.add_argument(f"user-data-dir={user_data_path}")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
            )
            self.driver.implicitly_wait(5)
            logger.info("Real Chrome Profile WebDriver initialized successfully")
        except WebDriverException as e:
            if "already in use" in str(e).lower() or "device or resource busy" in str(e).lower():
                logger.error("CRITICAL: You must CLOSE all regular Google Chrome windows to use the Real Profile hack!")
            else:
                logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise

    def _quit_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("WebDriver closed")
            except Exception:
                pass

    def _scrape_keyword(self, keyword: str) -> list[dict]:
        url = f"{SEARCH_URL_BASE}?q={keyword}&sort=recency&per_page=20"
        jobs = []

        self.driver.get(url)
        
        # Wait until either the Cloudflare challenge is gone and job cards load, or 60 seconds pass
        try:
            logger.info(f"  Waiting for page to load for '{keyword}' (Solve captcha if it appears!)...")
            # Wait up to 60 seconds for the challenge to clear and job-tiles to appear
            WebDriverWait(self.driver, 60).until(
                lambda d: "Just a moment" not in d.title and len(d.find_elements(By.CSS_SELECTOR, "section.up-card-section, article.job-tile, div.up-card, [data-test='job-tile-list'] > section, h2.job-tile-title")) > 0
            )
            time.sleep(2) # Extra buffer after they load
        except Exception as e:
            if "Just a moment" in self.driver.title:
                logger.warning(f"  Upwork Cloudflare challenge blocked us for '{keyword}'. Skipping...")
            else:
                logger.info(f"  No job listings found for '{keyword}' after waiting.")
            return []

        # Find job cards
        try:
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.up-card-section, article.job-tile, div.up-card")
            
            if not job_cards:
                 job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-test='job-tile-list'] > section")

            # Disable implicitly wait for faster parsing of each card
            self.driver.implicitly_wait(0)

            for card in job_cards:
                job = self._parse_job_card(card, keyword)
                if job:
                    jobs.append(job)

            self.driver.implicitly_wait(5)
        except Exception as e:
            logger.debug(f"Error fetching cards: {e}")

        return jobs

    def _parse_job_card(self, card, keyword: str) -> Optional[dict]:
        try:
            title = self._safe_text(card, "h2 a, h3 a, [data-test='job-tile-title-link'], a.up-n-link") or "N/A"
            
            url = ""
            try:
                link_el = card.find_element(By.CSS_SELECTOR, "h2 a, h3 a, [data-test='job-tile-title-link']")
                url = link_el.get_attribute("href")
                if url and not url.startswith("http"):
                    url = "https://www.upwork.com" + url
            except:
                pass

            desc = self._safe_text(card, "[data-test='job-description-text'], p, span.js-description") or "N/A"
            budget = self._safe_text(card, "[data-test='budget'], .js-budget, [data-test='is-fixed-price']") or "N/A"
            posted = self._safe_text(card, "[data-test='posted-on'], small.text-muted") or "N/A"
            location = self._safe_text(card, "[data-test='client-location']") or "N/A"
            spend = self._safe_text(card, "[data-test='client-spend']") or "N/A"

            return {
                "Project Title": title.strip(),
                "Description": desc.strip()[:500],
                "Budget": budget.strip(),
                "Client Location": location.strip(),
                "Client Spend History": spend.strip(),
                "Posted Date": posted.strip(),
                "Keyword": keyword,
                "URL": url.split("?")[0] if url else "",
            }

        except Exception as e:
            logger.debug(f"  Error parsing info from card: {e}")
            return None

    def _safe_text(self, parent, selector: str) -> Optional[str]:
        for sel in selector.split(","):
            try:
                el = parent.find_element(By.CSS_SELECTOR, sel.strip())
                return el.text.strip()
            except NoSuchElementException:
                continue
        return None

    @staticmethod
    def _random_delay():
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


if __name__ == "__main__":
    scraper = UpworkScraper(headless=False) # Run non-headless locally to view what happens
    results = scraper.run()
    if results:
         print(f"\\n> Scraped {len(results)} Upwork jobs -> output/upwork_jobs.csv")
    else:
         print("\\n> No jobs found. You might have been blocked.")
