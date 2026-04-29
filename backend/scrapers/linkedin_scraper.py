"""
LinkedIn Jobs Scraper Module
=============================
Uses Selenium WebDriver to authenticate and scrape LinkedIn job postings.
Credentials are loaded from environment variables for security.

Required environment variables:
    LINKEDIN_EMAIL    — Your LinkedIn email address
    LINKEDIN_PASSWORD — Your LinkedIn password

Keywords: AI automation, AI chatbot, SaaS, web development, app development.

Fields extracted:
    - Job Title
    - Company Name
    - Recruiter Name (if available)
    - Location
    - Job Description

Output: output/linkedin_jobs.csv

Usage:
    from scrapers.linkedin_scraper import LinkedInScraper
    scraper = LinkedInScraper()
    scraper.run()
"""

import os
import re
import sys
import time
import random
from typing import Optional

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.logger import setup_logger
from utils.csv_handler import write_csv

logger = setup_logger("linkedin_scraper")

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

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

OUTPUT_FILE = "linkedin_jobs.csv"

CSV_HEADERS = [
    "Job Title",
    "Company Name",
    "Recruiter Name",
    "Location",
    "Job Description",
    "Keyword",
    "URL",
]

LOGIN_URL = "https://www.linkedin.com/login"
JOBS_SEARCH_URL = "https://www.linkedin.com/jobs/search/"

MIN_DELAY = 3.0
MAX_DELAY = 6.0
PAGE_LOAD_TIMEOUT = 20
MAX_PAGES_PER_KEYWORD = 3
JOBS_PER_PAGE = 25


class LinkedInScraper:
    """
    Selenium-based LinkedIn job scraper.

    Authenticates using credentials from environment variables, then
    searches for each keyword and extracts job listing details.
    """

    def __init__(self, progress_callback: Optional[callable] = None, headless: bool = True):
        """
        Args:
            progress_callback: Optional function(current, total) for progress updates.
            headless: Run Chrome in headless mode (no GUI). Default True.
        """
        self.progress_callback = progress_callback
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.results: list[dict] = []
        self._total_keywords = len(KEYWORDS)
        self._current = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, keywords: Optional[list[str]] = None, location: Optional[str] = None) -> list[dict]:
        """
        Execute the full LinkedIn scraping pipeline.

        Returns:
            List of dicts (one per job posting).
        """
        email = os.getenv("LINKEDIN_EMAIL", "")
        password = os.getenv("LINKEDIN_PASSWORD", "")

        if not email or not password:
            logger.error("Missing LINKEDIN_EMAIL or LINKEDIN_PASSWORD in environment")
            return []

        run_keywords = keywords if keywords else KEYWORDS
        self._total_keywords = len(run_keywords)

        logger.info("=" * 60)
        logger.info("LinkedIn Scraper — Starting")
        logger.info(f"Keywords: {', '.join(run_keywords)}")
        if location:
            logger.info(f"Location: {location}")
        logger.info("=" * 60)

        self.results = []

        try:
            self._init_driver()
            self._login(email, password)

            for idx, keyword in enumerate(run_keywords, 1):
                self._current = idx
                logger.info(f"[{idx}/{self._total_keywords}] Searching: '{keyword}'")

                try:
                    jobs = self._scrape_keyword(keyword, location=location)
                    self.results.extend(jobs)
                    logger.info(f"  → Found {len(jobs)} jobs for '{keyword}'")
                except Exception as e:
                    logger.error(f"  ✗ Error scraping '{keyword}': {e}")

                if self.progress_callback:
                    self.progress_callback(idx, self._total_keywords)

                self._random_delay()

        except Exception as e:
            logger.error(f"Critical error during LinkedIn scraping: {e}")
        finally:
            self._quit_driver()

        # De-duplicate by URL
        seen: set[str] = set()
        unique = []
        for job in self.results:
            url = job.get("URL", "")
            if url not in seen:
                seen.add(url)
                unique.append(job)
        self.results = unique

        # Write CSV
        if self.results:
            write_csv(OUTPUT_FILE, CSV_HEADERS, self.results)
        else:
            logger.warning("No results found — CSV not created.")

        logger.info(f"LinkedIn Scraper — Done. Total unique jobs: {len(self.results)}")
        return self.results

    # ------------------------------------------------------------------
    # Browser setup
    # ------------------------------------------------------------------

    def _init_driver(self):
        """Initialize Chrome WebDriver with anti-detection options."""
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
            )
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            logger.info(
                "Ensure ChromeDriver is installed. "
                "Run: pip install webdriver-manager"
            )
            raise

    def _quit_driver(self):
        """Safely close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("WebDriver closed")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _login(self, email: str, password: str):
        """Log in to LinkedIn with the provided credentials."""
        logger.info("Logging in to LinkedIn…")

        self.driver.get(LOGIN_URL)
        time.sleep(random.uniform(2, 4))

        try:
            wait = WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT)

            # Enter email
            email_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_input.clear()
            self._human_type(email_input, email)
            time.sleep(random.uniform(0.5, 1.5))

            # Enter password
            password_input = self.driver.find_element(By.ID, "password")
            password_input.clear()
            self._human_type(password_input, password)
            time.sleep(random.uniform(0.5, 1.5))

            # Click sign in
            sign_in_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit'], button[data-litms-control-urn='login-submit']"
            )
            sign_in_btn.click()

            # Wait for navigation to feed or challenge page
            time.sleep(5)

            current_url = self.driver.current_url
            if "checkpoint" in current_url or "challenge" in current_url:
                logger.warning(
                    "LinkedIn security challenge detected. "
                    "You may need to run in non-headless mode and "
                    "complete the verification manually."
                )
                # Give user time to complete challenge if running headful
                if not self.headless:
                    logger.info("Waiting 60 seconds for manual verification…")
                    time.sleep(60)

            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                logger.info("✓ Login successful")
            else:
                logger.warning(f"Login may not have succeeded. Current URL: {self.driver.current_url}")

        except TimeoutException:
            logger.error("Timeout during LinkedIn login")
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------

    def _scrape_keyword(self, keyword: str, location: Optional[str] = None) -> list[dict]:
        """Search for a keyword and scrape job listings across multiple pages."""
        jobs: list[dict] = []

        for page in range(MAX_PAGES_PER_KEYWORD):
            start = page * JOBS_PER_PAGE
            url = f"{JOBS_SEARCH_URL}?keywords={keyword}&start={start}"
            if location:
                url += f"&location={location}"

            logger.debug(f"  Page {page + 1}: {url}")

            try:
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))

                # Scroll to load lazy content
                self._scroll_page()

                # Find job cards
                job_cards = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.job-card-container, li.jobs-search-results__list-item, "
                    "div.scaffold-layout__list-item"
                )

                if not job_cards:
                    # Try alternative selectors
                    job_cards = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        "ul.jobs-search__results-list li, "
                        "div[data-job-id]"
                    )

                if not job_cards:
                    logger.debug(f"  No job cards found on page {page + 1}")
                    break

                for card in job_cards:
                    job = self._parse_job_card(card, keyword)
                    if job:
                        jobs.append(job)

                self._random_delay()

            except Exception as e:
                logger.error(f"  Error on page {page + 1}: {e}")
                break

        return jobs

    def _parse_job_card(self, card, keyword: str) -> Optional[dict]:
        """Extract job data from a single job card element."""
        try:
            # Click the card to load the detail pane
            try:
                card.click()
                time.sleep(random.uniform(1.5, 3))
            except Exception:
                pass  # Some cards don't need clicking

            # Job Title
            title = self._safe_text(
                card, "h3, a.job-card-list__title, "
                "strong, a.job-card-container__link"
            ) or "N/A"

            # Company Name
            company = self._safe_text(
                card, "h4 a, span.job-card-container__primary-description, "
                "h4.base-search-card__subtitle, a.job-card-container__company-name"
            ) or "N/A"

            # Location
            location = self._safe_text(
                card, "span.job-card-container__metadata-item, "
                "span.job-search-card__location, li.job-card-container__metadata-item"
            ) or "N/A"

            # Job URL
            url = ""
            try:
                link_el = card.find_element(
                    By.CSS_SELECTOR, "a.job-card-list__title, a.job-card-container__link, a"
                )
                url = link_el.get_attribute("href") or ""
            except NoSuchElementException:
                pass

            # Job Description (from detail pane)
            description = self._get_job_description()

            # Recruiter Name (from detail pane)
            recruiter = self._get_recruiter_name()

            return {
                "Job Title": title.strip(),
                "Company Name": company.strip(),
                "Recruiter Name": recruiter,
                "Location": location.strip(),
                "Job Description": description[:1000],
                "Keyword": keyword,
                "URL": url.split("?")[0] if url else "",  # Clean tracking params
            }

        except Exception as e:
            logger.debug(f"  Error parsing job card: {e}")
            return None

    def _get_job_description(self) -> str:
        """Try to extract the job description from the detail panel."""
        selectors = [
            "div.jobs-description__content",
            "div.show-more-less-html__markup",
            "div.jobs-box__html-content",
            "section.show-more-less-html",
            "div#job-details",
        ]
        self.driver.implicitly_wait(0)
        description = "N/A"
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text:
                    description = re.sub(r"\s+", " ", text)
                    break
            except NoSuchElementException:
                continue
        self.driver.implicitly_wait(10)
        return description

    def _get_recruiter_name(self) -> str:
        """Try to find the recruiter/hiring manager name."""
        selectors = [
            "div.hirer-card__hirer-information a span",
            "a.jobs-poster__name",
            "span.jobs-poster__name",
            "div.hiring-team-header a",
        ]
        self.driver.implicitly_wait(0)
        name_out = "N/A"
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                name = el.text.strip()
                if name:
                    name_out = name
                    break
            except NoSuchElementException:
                continue
        self.driver.implicitly_wait(10)
        return name_out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _human_type(self, element, text: str):
        """Type text with random delays to mimic human behavior."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def _scroll_page(self):
        """Scroll down the page to trigger lazy loading."""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            for _ in range(3):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            pass

    def _safe_text(self, parent, selector: str) -> Optional[str]:
        """Safely extract text from the first matching child element."""
        self.driver.implicitly_wait(0)
        text_out = None
        for sel in selector.split(","):
            try:
                el = parent.find_element(By.CSS_SELECTOR, sel.strip())
                text_out = el.text.strip()
                break
            except NoSuchElementException:
                continue
        self.driver.implicitly_wait(10)
        return text_out

    @staticmethod
    def _random_delay():
        """Wait a random amount of time to avoid rate-limiting."""
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("LinkedIn Scraper")
    print("=" * 40)
    print("Ensure LINKEDIN_EMAIL and LINKEDIN_PASSWORD are set in your .env file.")
    print()

    scraper = LinkedInScraper(headless=False)
    results = scraper.run()
    print(f"\n✓ Scraped {len(results)} LinkedIn jobs → output/linkedin_jobs.csv")
