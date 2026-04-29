"""
Local Directories Scraper Module
=================================
Scrapes business listings from Yellow Pages (U.S.), Yelp (U.S.),
and Canada411 (Canada) for targeted niches.

Target directories:
    - YellowPages.com (U.S.)
    - Yelp.com (U.S.)
    - Canada411.ca (Canada)

Niches: logistics, retail, healthcare, education

Fields extracted:
    - Business Name
    - Industry
    - Phone
    - Email (if available)
    - Website
    - Location

Output: output/local_directories.csv

Usage:
    from scrapers.directories_scraper import DirectoriesScraper
    scraper = DirectoriesScraper()
    scraper.run()
"""

import os
import re
import sys
import time
import random
from typing import Optional
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.logger import setup_logger
from utils.csv_handler import write_csv

logger = setup_logger("directories_scraper")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NICHES = ["logistics", "retail", "healthcare", "education"]

# Default search locations
US_LOCATIONS = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX"]
CA_LOCATIONS = ["Toronto, ON", "Vancouver, BC", "Montreal, QC"]

OUTPUT_FILE = "local_directories.csv"

CSV_HEADERS = [
    "Business Name",
    "Industry",
    "Phone",
    "Email",
    "Website",
    "Location",
    "Source",
]

MIN_DELAY = 3.0
MAX_DELAY = 7.0
MAX_PAGES = 2  # Pages per niche + location combo

class DirectoriesScraper:
    """
    Scrapes business listings from Yellow Pages, Yelp, and Canada411.
    Results from all three sources are merged into a single CSV.
    Uses Selenium to bypass 403 protections, and BeautifulSoup for fast parsing.
    """

    def __init__(self, progress_callback: Optional[callable] = None, headless: bool = True):
        """
        Args:
            progress_callback: Optional function(current, total) for progress updates.
            headless: Run browser invisibly by default.
        """
        self.progress_callback = progress_callback
        self.headless = headless
        self.driver = None
        self.results: list[dict] = []

        # Total tasks = niches × (US dirs × US locations + CA dirs × CA locations)
        self._total_tasks = len(NICHES) * (
            len(US_LOCATIONS) * 2 + len(CA_LOCATIONS)  # YP + Yelp for each US loc, Canada411 for CA
        )
        self._completed = 0

    def _init_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-blink-features=AutomationControlled")
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
            self.driver.implicitly_wait(5)
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise

    def _quit_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def run(self, niches: Optional[list[str]] = None) -> list[dict]:
        """
        Execute the full directories scraping pipeline.

        Returns:
            List of dicts (one per business listing).
        """
        run_niches = niches if niches else NICHES
        
        # Recalculate total tasks based on actual niches provided
        self._total_tasks = len(run_niches) * (
            len(US_LOCATIONS) * 2 + len(CA_LOCATIONS)
        )
        self._completed = 0

        logger.info("=" * 60)
        logger.info("Local Directories Scraper (Selenium Edition) — Starting")
        logger.info(f"Niches: {', '.join(run_niches)}")
        logger.info(f"US Locations: {', '.join(US_LOCATIONS)}")
        logger.info(f"CA Locations: {', '.join(CA_LOCATIONS)}")
        logger.info("=" * 60)

        self.results = []

        try:
            self._init_driver()

            for niche in run_niches:
                logger.info(f"--- Niche: {niche} ---")

                # Yellow Pages (US)
                for location in US_LOCATIONS:
                    self._tick_progress()
                    logger.info(f"  YellowPages: {niche} in {location}")
                    try:
                        yp_results = self._scrape_yellowpages(niche, location)
                        self.results.extend(yp_results)
                        logger.info(f"    -> {len(yp_results)} listings")
                    except Exception as e:
                        logger.error(f"    Error: {e}")
                    self._random_delay()

                # Yelp (US)
                for location in US_LOCATIONS:
                    self._tick_progress()
                    logger.info(f"  Yelp: {niche} in {location}")
                    try:
                        yelp_results = self._scrape_yelp(niche, location)
                        self.results.extend(yelp_results)
                        logger.info(f"    -> {len(yelp_results)} listings")
                    except Exception as e:
                        logger.error(f"    Error: {e}")
                    self._random_delay()

                # Canada411 (Canada)
                for location in CA_LOCATIONS:
                    self._tick_progress()
                    logger.info(f"  Canada411: {niche} in {location}")
                    try:
                        ca_results = self._scrape_canada411(niche, location)
                        self.results.extend(ca_results)
                        logger.info(f"    -> {len(ca_results)} listings")
                    except Exception as e:
                        logger.error(f"    Error: {e}")
                    self._random_delay()

        finally:
            self._quit_driver()

        # De-duplicate by business name + phone
        seen: set[str] = set()
        unique = []
        for biz in self.results:
            key = f"{biz.get('Business Name', '')}-{biz.get('Phone', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(biz)
        self.results = unique

        # Write CSV
        if self.results:
            write_csv(OUTPUT_FILE, CSV_HEADERS, self.results)
        else:
            logger.warning("No results found — CSV not created.")

        logger.info(f"Directories Scraper — Done. Total unique listings: {len(self.results)}")
        return self.results

    # ------------------------------------------------------------------
    # Yellow Pages
    # ------------------------------------------------------------------

    def _scrape_yellowpages(self, niche: str, location: str) -> list[dict]:
        """Scrape YellowPages.com search results."""
        listings: list[dict] = []

        for page in range(1, MAX_PAGES + 1):
            url = (
                f"https://www.yellowpages.com/search"
                f"?search_terms={quote_plus(niche)}"
                f"&geo_location_terms={quote_plus(location)}"
                f"&page={page}"
            )

            try:
                self.driver.get(url)
                time.sleep(random.uniform(2.0, 4.0)) # Let JS load
            except Exception as e:
                logger.debug(f"    YP page {page} request failed: {e}")
                break

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # YellowPages uses div.result elements
            results = soup.select("div.result, div.search-result, div.v-card")

            if not results:
                # Try organic results
                results = soup.select("div.organic div.srp-listing")

            if not results:
                logger.debug(f"    No YP results on page {page}")
                break

            for card in results:
                listing = self._parse_yp_card(card, niche, location)
                if listing:
                    listings.append(listing)

            time.sleep(random.uniform(1.5, 3.0))

        return listings

    def _parse_yp_card(self, card, niche: str, location: str) -> Optional[dict]:
        """Parse a single Yellow Pages listing card."""
        try:
            # Business Name
            name_el = card.select_one(
                "a.business-name, h2.n a, span.business-name, a[class*='business-name']"
            )
            name = name_el.get_text(strip=True) if name_el else None
            if not name:
                return None

            # Phone
            phone_el = card.select_one(
                "div.phones, div.phone, a[href^='tel:']"
            )
            phone = phone_el.get_text(strip=True) if phone_el else "N/A"

            # Website
            website = "N/A"
            website_el = card.select_one(
                "a.track-visit-website, a[href*='website'], a.website-link"
            )
            if website_el:
                website = website_el.get("href", "N/A")
                # YP sometimes uses redirect URLs
                if "yellowpages.com" in website:
                    website = "N/A"

            # Address / Location
            addr_el = card.select_one(
                "div.adr, p.adr, span.locality, div.street-address"
            )
            addr = addr_el.get_text(strip=True) if addr_el else location

            # Categories
            cat_el = card.select_one("div.categories, span.categories")
            categories = cat_el.get_text(strip=True) if cat_el else niche

            # Email (rarely available on YP)
            email = self._extract_email_from_element(card)

            return {
                "Business Name": name,
                "Industry": categories[:100],
                "Phone": self._clean_phone(phone),
                "Email": email,
                "Website": website,
                "Location": addr[:200],
                "Source": "YellowPages",
            }

        except Exception as e:
            logger.debug(f"    Error parsing YP card: {e}")
            return None

    # ------------------------------------------------------------------
    # Yelp
    # ------------------------------------------------------------------

    def _scrape_yelp(self, niche: str, location: str) -> list[dict]:
        """Scrape Yelp.com search results."""
        listings: list[dict] = []

        for page in range(MAX_PAGES):
            start = page * 10
            url = (
                f"https://www.yelp.com/search"
                f"?find_desc={quote_plus(niche)}"
                f"&find_loc={quote_plus(location)}"
                f"&start={start}"
            )

            try:
                self.driver.get(url)
                time.sleep(random.uniform(2.0, 4.0)) # Let JS load
            except Exception as e:
                logger.debug(f"    Yelp page {page + 1} request failed: {e}")
                break

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Yelp uses various container selectors for search results
            results = soup.select(
                "div[data-testid='serp-ia-card'], "
                "li.border-color--default, "
                "div.container__09f24__FeTO6"
            )

            if not results:
                # Broader fallback
                results = soup.select("div.search-result, div.arrange-unit")

            if not results:
                logger.debug(f"    No Yelp results on page {page + 1}")
                break

            for card in results:
                listing = self._parse_yelp_card(card, niche, location)
                if listing:
                    listings.append(listing)

            time.sleep(random.uniform(2.0, 4.0))

        return listings

    def _parse_yelp_card(self, card, niche: str, location: str) -> Optional[dict]:
        """Parse a single Yelp listing card."""
        try:
            # Business Name — typically in an <a> with a specific pattern
            name_el = card.select_one(
                "a[href*='/biz/'] span, h3 a span, a.css-19v1rkv, "
                "h3 span a, a[name] span"
            )
            if not name_el:
                name_el = card.select_one("a[href*='/biz/']")
            name = name_el.get_text(strip=True) if name_el else None
            if not name or len(name) < 2:
                return None

            # Remove leading numbers (Yelp adds rank numbers)
            name = re.sub(r"^\d+\.\s*", "", name)

            # Phone
            phone_el = card.select_one("p[class*='phone'], span[class*='phone']")
            phone = phone_el.get_text(strip=True) if phone_el else "N/A"

            # Location / Address
            addr_parts = card.select("span[class*='address'], address span")
            addr = ", ".join(p.get_text(strip=True) for p in addr_parts) if addr_parts else location

            # Category
            cat_el = card.select_one("span[class*='category'], p[class*='category']")
            category = cat_el.get_text(strip=True) if cat_el else niche

            # Website & email are not typically on Yelp search results
            email = self._extract_email_from_element(card)

            return {
                "Business Name": name,
                "Industry": category[:100] if category else niche,
                "Phone": self._clean_phone(phone),
                "Email": email,
                "Website": "N/A",  # Yelp does not show website in search results
                "Location": addr[:200] if addr else location,
                "Source": "Yelp",
            }

        except Exception as e:
            logger.debug(f"    Error parsing Yelp card: {e}")
            return None

    # ------------------------------------------------------------------
    # Canada411
    # ------------------------------------------------------------------

    def _scrape_canada411(self, niche: str, location: str) -> list[dict]:
        """Scrape Canada411.ca business listings."""
        listings: list[dict] = []

        # Canada411 uses separate city and province
        city, province = self._split_ca_location(location)

        for page in range(1, MAX_PAGES + 1):
            url = (
                f"https://www.canada411.ca/search/si/{page}/"
                f"?what={quote_plus(niche)}"
                f"&where={quote_plus(location)}"
            )

            try:
                self.driver.get(url)
                time.sleep(random.uniform(2.0, 4.0)) # Let JS load
            except Exception as e:
                logger.debug(f"    Canada411 page {page} request failed: {e}")
                break

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Canada411 listing containers
            results = soup.select(
                "div.listing__content, div.c411Listing, "
                "div.listing, li.jsResultsList"
            )

            if not results:
                results = soup.select("div.vcard, div[class*='listing']")

            if not results:
                logger.debug(f"    No Canada411 results on page {page}")
                break

            for card in results:
                listing = self._parse_canada411_card(card, niche, location)
                if listing:
                    listings.append(listing)

            time.sleep(random.uniform(2.0, 4.0))

        return listings

    def _parse_canada411_card(self, card, niche: str, location: str) -> Optional[dict]:
        """Parse a single Canada411 listing card."""
        try:
            # Business Name
            name_el = card.select_one(
                "h2.listing__name a, span.listing__name, "
                "a.listing__name--link, h2 a"
            )
            name = name_el.get_text(strip=True) if name_el else None
            if not name:
                return None

            # Phone
            phone_el = card.select_one(
                "a.listing__phone, span.listing__phone, a[href^='tel:']"
            )
            phone = phone_el.get_text(strip=True) if phone_el else "N/A"

            # Address
            addr_el = card.select_one(
                "span.listing__address, div.listing__address, address"
            )
            addr = addr_el.get_text(strip=True) if addr_el else location

            # Website
            website = "N/A"
            web_el = card.select_one("a.listing__website, a[class*='website']")
            if web_el:
                website = web_el.get("href", "N/A")

            # Category
            cat_el = card.select_one("span.listing__category, div.listing__category")
            category = cat_el.get_text(strip=True) if cat_el else niche

            email = self._extract_email_from_element(card)

            return {
                "Business Name": name,
                "Industry": category[:100],
                "Phone": self._clean_phone(phone),
                "Email": email,
                "Website": website,
                "Location": addr[:200],
                "Source": "Canada411",
            }

        except Exception as e:
            logger.debug(f"    Error parsing Canada411 card: {e}")
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tick_progress(self):
        """Update progress counter and call the progress callback."""
        self._completed += 1
        if self.progress_callback:
            self.progress_callback(self._completed, self._total_tasks)

    @staticmethod
    def _extract_email_from_element(element) -> str:
        """Try to find an email address within an HTML element."""
        # Check mailto: links
        mailto = element.select_one("a[href^='mailto:']")
        if mailto:
            email = mailto.get("href", "").replace("mailto:", "").strip()
            if email:
                return email

        # Regex scan the element text
        text = element.get_text()
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(pattern, text)
        return match.group(0) if match else "N/A"

    @staticmethod
    def _clean_phone(phone: str) -> str:
        """Clean and normalize a phone number string."""
        if not phone or phone == "N/A":
            return "N/A"
        # Keep only digits, spaces, hyphens, parens, and plus sign
        cleaned = re.sub(r"[^\d\s\-\(\)\+]", "", phone).strip()
        return cleaned if cleaned else "N/A"

    @staticmethod
    def _split_ca_location(location: str) -> tuple[str, str]:
        """Split 'Toronto, ON' into ('Toronto', 'ON')."""
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 2:
            return parts[0], parts[1]
        return location, ""

    @staticmethod
    def _random_delay():
        """Wait a random amount of time between requests."""
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    scraper = DirectoriesScraper(headless=False)
    results = scraper.run()
    if results:
        print(f"\n> Scraped {len(results)} directory listings -> output/local_directories.csv")
    else:
        print("\\n> No results found.")
