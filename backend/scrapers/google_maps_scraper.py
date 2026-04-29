"""
Google Maps Scraper Module (v2 - Robust Rewrite)
=================================================
A completely rewritten Google Maps scraper with:
  - JavaScript-based data extraction (immune to CSS class name changes)
  - Attribute-based selectors (stable, not class-based)
  - Multi-stage fallback extraction strategy
  - Click-into-listing extraction for deep data
  - Headless and non-headless support

Usage:
    from scrapers.google_maps_scraper import GoogleMapsScraper
    scraper = GoogleMapsScraper()
    scraper.run(location="Dubai", niche="gyms")
"""

import os
import re
import sys
import time
import random
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus, urlencode

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.logger import setup_logger
from utils.csv_handler import write_csv, write_json, append_csv, ensure_output_dir

logger = setup_logger("google_maps_scraper")


# ---------------------------------------------------------------------------
# Selector constants  (attribute-based = stable across Google UI updates)
# ---------------------------------------------------------------------------
FEED_SELECTORS = [
    "div[role='feed']",
    "div[aria-label*='Results']",
    "div[aria-label*='result']",
]

# These are the clickable result cards in the sidebar
RESULT_ITEM_SELECTORS = [
    "a[href*='/maps/place/']",         # Most stable — href never changes
    "[jsaction*='placeCard']",
    "div[jsaction*='mouseover:pane']",
]

# Detail-panel selectors (shown after clicking a result)
DETAIL_SELECTORS = {
    "name":    ["h1", "h1[class*='fontHeadlineLarge']"],
    "category": ["button[jsaction*='category']", "[aria-label*='Category']"],
    "rating":   ["span[aria-hidden='true'][class*='fontDisplay']",
                 "div[class*='fontBodyMedium'] span[aria-hidden='true']"],
    "reviews":  ["span[aria-label*='reviews']", "button[aria-label*='reviews'] span"],
    # Address: target the inner text div, NOT the button wrapper (which contains the icon glyph)
    "address":  [
        "button[data-tooltip='Copy address'] div.Io6YTe",
        "button[data-tooltip='Copy address'] .fontBodyMedium",
        "[data-item-id='address'] .fontBodyMedium",
        "button[aria-label*='Address:'] .fontBodyMedium",
    ],
    "phone":    ["button[data-tooltip='Copy phone number']",
                 "[data-item-id^='phone']",
                 "a[href^='tel:']"],
    "website":  ["a[data-tooltip='Open website']",
                 "a[href*='http'][aria-label*='website' i]",
                 "a[data-item-id='authority']"],
}


class GoogleMapsScraper:
    """
    Robust Google Maps scraper.

    Strategy:
    1. Navigate to maps search URL
    2. Handle consent popup
    3. Wait for the results sidebar to appear
    4. Collect all result card links (stable href-based)
    5. For each card: click it, wait for detail panel, extract with attribute selectors
    6. Try email extraction from website URL
    7. Save to CSV + master dataset
    """

    def __init__(self, progress_callback: Optional[callable] = None):
        self.progress_callback = progress_callback
        self.driver: Optional[webdriver.Chrome] = None
        self.results: List[Dict[str, Any]] = []

        from dotenv import load_dotenv
        load_dotenv()

        self.headless      = os.getenv("GOOGLE_MAPS_HEADLESS", "true").lower() == "true"
        self.proxy_list    = [p.strip() for p in os.getenv("PROXY_LIST", "").split(",") if p.strip()]
        self.enable_email  = os.getenv("ENABLE_EMAIL_EXTRACT", "true").lower() == "true"
        self.master_file   = "google_maps_master.csv"
        self.max_results   = int(os.getenv("GOOGLE_MAPS_MAX_RESULTS", "100"))

    # ------------------------------------------------------------------
    # Driver lifecycle
    # ------------------------------------------------------------------
    def _init_driver(self):
        """Initialise Chrome with anti-detection flags."""
        from webdriver_manager.chrome import ChromeDriverManager

        ua_string = self._random_ua()

        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1440,900")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--lang=en-US,en")
        opts.add_argument(f"--user-agent={ua_string}")
        opts.add_argument("--disable-extensions")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            opts.add_argument(f"--proxy-server={proxy}")
            logger.info(f"Using proxy: {proxy}")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)

        # Patch navigator.webdriver
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        self.driver.set_page_load_timeout(60)
        self.driver.implicitly_wait(0)   # We use explicit waits everywhere
        logger.info("Chrome WebDriver initialised.")

    def _quit_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            logger.info("WebDriver closed.")

    @staticmethod
    def _random_ua() -> str:
        """Try fake_useragent, fall back to a hardcoded modern UA."""
        try:
            from fake_useragent import UserAgent
            return UserAgent().chrome
        except Exception:
            return (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )

    # ------------------------------------------------------------------
    # Consent & captcha handling
    # ------------------------------------------------------------------
    def _handle_consent(self):
        """Click past Google's 'Before you continue' consent screen."""
        try:
            WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form[action*='consent']"))
            )
        except TimeoutException:
            return  # No consent screen — great

        accept_xpaths = [
            "//button[.//div[contains(text(), 'Accept all')]]",
            "//button[contains(., 'Accept all')]",
            "//button[contains(., 'I agree')]",
            "//button[contains(., 'Agree')]",
            "//button[@id='L2AGLb']",
        ]
        for xpath in accept_xpaths:
            try:
                btn = self.driver.find_element(By.XPATH, xpath)
                if btn.is_displayed():
                    btn.click()
                    logger.info(f"Consent dismissed via: {xpath}")
                    time.sleep(2)
                    return
            except Exception:
                continue
        logger.warning("Consent screen found but could not dismiss it.")

    def _handle_app_prompt(self):
        """
        Dismiss the 'Open the Google Maps app?' popup that appears in headless Chrome.
        We click 'Keep using web' so the search results remain accessible.
        """
        try:
            # Wait briefly for the modal to appear
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                    "//*[contains(text(), 'Open the Google Maps app') or "
                    "contains(text(), 'Keep using web')]"
                ))
            )
        except TimeoutException:
            return  # No prompt — all good

        # Try clicking 'Keep using web'
        xpaths = [
            "//button[contains(., 'Keep using web')]",
            "//button[contains(., 'keep using')]",
            "//button[contains(@aria-label, 'Keep using web')]",
            # Fallback: click the first dialog button that is NOT 'Continue'
        ]
        for xpath in xpaths:
            try:
                btn = self.driver.find_element(By.XPATH, xpath)
                if btn.is_displayed():
                    btn.click()
                    logger.info("'Open Maps app' prompt dismissed (clicked 'Keep using web').")
                    time.sleep(1)
                    return
            except Exception:
                continue

        # Last resort: press Escape
        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            logger.info("'Open Maps app' prompt dismissed via Escape.")
            time.sleep(1)
        except Exception:
            pass

    def _check_captcha(self) -> bool:
        url = self.driver.current_url
        if "google.com/sorry" in url or "recaptcha" in url.lower():
            logger.error("CAPTCHA / rate-limit page detected.")
            if not self.headless:
                input("Solve the CAPTCHA in the browser, then press Enter here...")
                return True
            return False
        return True

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _navigate_to_search(self, location: str, niche: str) -> bool:
        query = f"{niche} in {location}"
        url   = f"https://www.google.com/maps/search/{quote_plus(query)}/"
        logger.info(f"Navigating to: {url}")

        try:
            self.driver.get(url)
        except Exception as e:
            logger.error(f"Page load failed: {e}")
            return False

        self._handle_consent()
        time.sleep(2)
        self._handle_app_prompt()
        time.sleep(1)
        return self._check_captcha()

    # ------------------------------------------------------------------
    # Waiting helpers
    # ------------------------------------------------------------------
    def _wait_for(self, selectors: List[str], timeout: int = 20) -> Optional[Any]:
        """Wait until any of the selectors produce at least one element."""
        end = time.time() + timeout
        while time.time() < end:
            for sel in selectors:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if els:
                        return els[0]
                except Exception:
                    pass
            time.sleep(0.5)
        return None

    def _find_first(self, selectors: List[str]) -> Optional[Any]:
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                return el
            except NoSuchElementException:
                continue
        return None

    def _find_all(self, selectors: List[str]) -> List[Any]:
        for sel in selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    return els
            except Exception:
                continue
        return []

    # ------------------------------------------------------------------
    # Collect result links from the sidebar
    # ------------------------------------------------------------------
    def _collect_result_links(self) -> List[str]:
        """
        Scroll the results sidebar and collect all place links.
        Returns a deduplicated list of /maps/place/... URLs.
        """
        logger.info("Waiting for results sidebar to load...")

        # Wait for at least one result card link to appear
        anchor = self._wait_for(["a[href*='/maps/place/']", "a.hfpxzc"], timeout=25)
        if not anchor:
            logger.error("Timed out waiting for result cards. Page may be blocked or search returned nothing.")
            self._save_debug_screenshot("no_results_found")
            return []

        # Identify the scrollable feed container
        feed = self._wait_for(FEED_SELECTORS, timeout=10)

        links: List[str] = []
        seen:  set        = set()
        no_new_count      = 0

        logger.info(f"Scrolling to collect up to {self.max_results} results...")

        for scroll_pass in range(50):          # Safety cap
            # Collect current links
            raw_els = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/'], a.hfpxzc")
            new_found = False
            for el in raw_els:
                try:
                    href = el.get_attribute("href")
                    if href and href not in seen:
                        # Only accept real place links (not photos etc.)
                        if "/maps/place/" in href:
                            seen.add(href)
                            links.append(href)
                            new_found = True
                except StaleElementReferenceException:
                    continue

            logger.info(f"  Scroll pass {scroll_pass+1}: {len(links)} unique links collected.")

            if len(links) >= self.max_results:
                logger.info(f"Hit max_results cap ({self.max_results}).")
                break

            # Check end-of-list marker
            page_src = self.driver.page_source
            if "You've reached the end of the list" in page_src or \
               "you've reached the end" in page_src.lower():
                logger.info("Reached end of results list.")
                break

            # Scroll the feed (or the page body as a fallback)
            if not new_found:
                no_new_count += 1
                if no_new_count >= 4:
                    logger.info("No new results after 4 scrolls — stopping.")
                    break
            else:
                no_new_count = 0

            if feed:
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollBy(0, 1200);", feed
                    )
                except Exception:
                    feed = None   # Feed went stale — fall back to body scroll
            else:
                self.driver.execute_script("window.scrollBy(0, 1200);")

            time.sleep(random.uniform(1.5, 2.5))

        logger.info(f"Collected {len(links)} result links.")
        return links[:self.max_results]

    # ------------------------------------------------------------------
    # Extract data from an individual listing
    # ------------------------------------------------------------------
    def _extract_text(self, selectors: List[str]) -> str:
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip() or el.get_attribute("aria-label") or ""
                if text:
                    return text
            except Exception:
                continue
        return "N/A"

    def _extract_href(self, selectors: List[str]) -> str:
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                val = el.get_attribute("href") or el.get_attribute("data-value") or ""
                if val:
                    return val.strip()
            except Exception:
                continue
        return "N/A"

    def _extract_listing_data(self, link: str, index: int, total: int) -> Optional[Dict[str, Any]]:
        """Navigate to a listing link and extract all available fields."""
        try:
            self.driver.get(link)
        except Exception as e:
            logger.warning(f"  [{index}/{total}] Failed to load listing: {e}")
            return None

        # Wait until the business name (h1) appears
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except TimeoutException:
            logger.warning(f"  [{index}/{total}] Timed out waiting for listing detail panel.")
            return None

        time.sleep(random.uniform(1.0, 2.0))

        name     = self._extract_text(DETAIL_SELECTORS["name"])
        category = self._extract_text(DETAIL_SELECTORS["category"])
        rating   = self._extract_text(DETAIL_SELECTORS["rating"])
        reviews  = self._extract_text(DETAIL_SELECTORS["reviews"])
        address  = self._extract_address()
        phone    = self._extract_phone()
        website  = self._extract_href(DETAIL_SELECTORS["website"])

        # Clean up fields
        rating   = re.split(r"[\n(]", rating)[0].strip()
        reviews  = re.sub(r"[^\d]", "", reviews) or "N/A"
        # Strip Google Maps private-use icon glyphs (e.g. \ue0c8) then clean
        address  = re.sub(r"[\ue000-\uf8ff]", "", address).split("\n")[0].strip()
        if website and "google.com" in website:
            website = "N/A"

        email = "N/A"
        if self.enable_email and website and website != "N/A":
            email = self._harvest_email(website)

        record = {
            "Business Name":   name,
            "Category":        category,
            "Rating":          rating,
            "Reviews":         reviews,
            "Phone Number":    phone,
            "Website URL":     website,
            "Email":           email,
            "Full Address":    address,
            "Scraped Date":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Google Maps Link": link,
        }

        logger.info(f"  [{index}/{total}] OK  {name} | {phone} | {rating} stars | {reviews} reviews")
        return record

    def _extract_phone(self) -> str:
        """Extract phone using multiple methods."""
        # 1. Stable data-item-id attribute
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "[data-item-id^='phone:tel:']")
            val = el.get_attribute("data-item-id") or ""
            phone = val.replace("phone:tel:", "").strip()
            if phone:
                return phone
        except NoSuchElementException:
            pass

        # 2. tel: href
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "a[href^='tel:']")
            href = el.get_attribute("href") or ""
            phone = href.replace("tel:", "").strip()
            if phone:
                return phone
        except NoSuchElementException:
            pass

        # 3. aria-label containing phone-like content
        try:
            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                label = btn.get_attribute("aria-label") or ""
                if re.search(r"\+?\d[\d\s\-\(\)]{7,}", label):
                    match = re.search(r"\+?[\d\s\-\(\)]{8,}", label)
                    if match:
                        return match.group().strip()
        except Exception:
            pass

        return "N/A"

    def _extract_address(self) -> str:
        """
        Extract address using the aria-label attribute of the 'Copy address' button.
        This avoids the icon glyph (\\ue0c8) that appears in the .text property.
        Falls back to reading child div text content.
        """
        # Method 1: aria-label on the copy-address button (most reliable - no icon glyph)
        for selector in [
            "button[data-tooltip='Copy address']",
            "button[aria-label*='Address:']",
        ]:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                label = el.get_attribute("aria-label") or ""
                # aria-label looks like: "Address: Sheikh Zayed Rd, Dubai"
                if ":" in label:
                    label = label.split(":", 1)[1].strip()
                if label:
                    return label
            except NoSuchElementException:
                continue

        # Method 2: inner div with class Io6YTe (Google's address text container)
        for selector in [
            "button[data-tooltip='Copy address'] div.Io6YTe",
            "button[data-tooltip='Copy address'] .fontBodyMedium",
            "[data-item-id='address'] .fontBodyMedium",
        ]:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = el.text.strip()
                if text:
                    return re.sub(r"[\ue000-\uf8ff]", "", text).strip()
            except NoSuchElementException:
                continue

        # Method 3: JavaScript innerText from the address button
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "button[data-tooltip='Copy address']")
            text = self.driver.execute_script("return arguments[0].innerText;", el) or ""
            text = re.sub(r"[\ue000-\uf8ff]", "", text).strip()
            if text:
                return text
        except Exception:
            pass

        return "N/A"

    # ------------------------------------------------------------------
    # Email harvesting
    # ------------------------------------------------------------------
    def _harvest_email(self, url: str) -> str:
        """Fetch a business website and find the first real email address."""
        if not url or url == "N/A":
            return "N/A"
        try:
            if not url.startswith("http"):
                url = "https://" + url
            headers = {"User-Agent": self._random_ua(), "Accept-Language": "en-US,en;q=0.9"}
            r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
            if r.status_code != 200:
                # Try /contact page
                base = url.rstrip("/")
                r = requests.get(f"{base}/contact", headers=headers, timeout=8)
                if r.status_code != 200:
                    return "N/A"

            text   = r.text
            emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
            junk   = {"example", "sentry", "wix", "png", "jpg", "jpeg", "svg",
                      "yourdomain", "domain.com", "email.com", "test."}
            filtered = [
                e for e in emails
                if not any(j in e.lower() for j in junk) and len(e) < 80
            ]
            return filtered[0] if filtered else "N/A"
        except Exception:
            return "N/A"

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------
    def _save_debug_screenshot(self, tag: str = "debug"):
        try:
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                f"gmaps_{tag}_{int(time.time())}.png"
            )
            self.driver.save_screenshot(path)
            logger.info(f"Debug screenshot saved: {path}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save(self, data: List[Dict], niche: str, location: str):
        if not data:
            logger.warning("No data to save.")
            return

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_q   = re.sub(r"[^\w]", "_", f"{niche}_{location}").lower()
        headers  = list(data[0].keys())

        write_csv(f"gmaps_{safe_q}_{ts}.csv", headers, data)
        write_json(f"gmaps_{safe_q}_{ts}.json", data)
        append_csv(self.master_file, headers, data)

        logger.info(f"Saved {len(data)} records.")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def run(self, location: str = "New York", niche: str = "restaurants") -> List[Dict]:
        logger.info(f"Starting Google Maps Scraper for '{niche}' in '{location}'")

        try:
            self._init_driver()

            if not self._navigate_to_search(location, niche):
                logger.error("Navigation failed — blocked or CAPTCHA.")
                return []

            links = self._collect_result_links()
            if not links:
                logger.warning("No result links found. Check debug screenshot.")
                return []

            logger.info(f"Extracting data from {len(links)} listings...")
            data: List[Dict] = []

            for i, link in enumerate(links, 1):
                if self.progress_callback:
                    self.progress_callback(i, len(links), f"Extracting listing {i}/{len(links)}...")

                record = self._extract_listing_data(link, i, len(links))
                if record:
                    data.append(record)

                # Brief cool-down every 10 listings
                if i % 10 == 0:
                    time.sleep(random.uniform(2, 4))

            self.results = data
            self._save(data, niche, location)
            logger.info(f"Scraping complete. Found {len(data)} listings.")
            return data

        except Exception as e:
            logger.exception(f"Critical error: {e}")
            return []
        finally:
            self._quit_driver()


if __name__ == "__main__":
    scraper = GoogleMapsScraper()
    results = scraper.run(location="Dubai", niche="gyms")
    print(f"\nTotal leads: {len(results)}")
    for r in results[:5]:
        print(r)
