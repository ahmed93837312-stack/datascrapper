"""
DataScrap Agent — Main CLI Runner
===================================
Command-line interface to run individual or all scraper modules.

Usage:
    python main.py --upwork                  # Run Upwork scraper only
    python main.py --linkedin                # Run LinkedIn scraper only
    python main.py --directories             # Run directories scraper only
    python main.py --google-maps             # Run Google Maps scraper (interactive)
    python main.py --all                     # Run all scrapers sequentially
    python main.py --upwork --directories    # Run specific combination

Setup:
    1. Install dependencies:  pip install -r requirements.txt
    2. Copy .env.example → .env and fill in LinkedIn credentials
    3. Run:  python main.py --all
"""

import argparse
import sys
import time
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger("main")


def run_upwork():
    """Execute the Upwork scraper module."""
    from scrapers.upwork_scraper import UpworkScraper

    logger.info("Starting Upwork Scraper…")
    start = time.time()

    scraper = UpworkScraper()
    results = scraper.run()

    elapsed = time.time() - start
    logger.info(f"Upwork Scraper completed in {elapsed:.1f}s — {len(results)} jobs found.")
    return results


def run_linkedin():
    """Execute the LinkedIn scraper module."""
    from scrapers.linkedin_scraper import LinkedInScraper

    logger.info("Starting LinkedIn Scraper…")
    start = time.time()

    scraper = LinkedInScraper(headless=True)
    results = scraper.run()

    elapsed = time.time() - start
    logger.info(f"LinkedIn Scraper completed in {elapsed:.1f}s — {len(results)} jobs found.")
    return results


def run_directories():
    """Execute the Local Directories scraper module."""
    from scrapers.directories_scraper import DirectoriesScraper

    logger.info("Starting Directories Scraper…")
    start = time.time()

    scraper = DirectoriesScraper()
    results = scraper.run()

    elapsed = time.time() - start
    logger.info(f"Directories Scraper completed in {elapsed:.1f}s — {len(results)} listings found.")
    return results


def run_google_maps(location=None, niche=None):
    """Execute the Google Maps scraper module."""
    from scrapers.google_maps_scraper import GoogleMapsScraper

    if not location:
        location = input("Enter location (e.g. Dubai, New York): ").strip() or "Dubai"
    if not niche:
        niche = input("Enter niche (e.g. gyms, restaurants): ").strip() or "gyms"

    logger.info(f"Starting Google Maps Scraper for '{niche}' in '{location}'…")
    start = time.time()

    scraper = GoogleMapsScraper()
    results = scraper.run(location=location, niche=niche)

    elapsed = time.time() - start
    logger.info(f"Google Maps Scraper completed in {elapsed:.1f}s — {len(results)} listings found.")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="DataScrap Agent -- Scraper CLI Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --upwork              Run Upwork scraper
  python main.py --linkedin            Run LinkedIn scraper
  python main.py --directories         Run directories scraper
  python main.py --all                 Run all scrapers
  python main.py --upwork --linkedin   Run multiple scrapers
        """,
    )

    parser.add_argument(
        "--upwork", action="store_true", help="Run the Upwork job scraper"
    )
    parser.add_argument(
        "--linkedin", action="store_true", help="Run the LinkedIn job scraper"
    )
    parser.add_argument(
        "--directories", action="store_true", help="Run the local directories scraper"
    )
    parser.add_argument(
        "--google-maps", action="store_true", help="Run the Google Maps scraper"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all scrapers sequentially"
    )

    args = parser.parse_args()

    # If no flags are provided, show help
    if not any([args.upwork, args.linkedin, args.directories, args.google_maps, args.all]):
        parser.print_help()
        sys.exit(0)

    print()
    print("+----------------------------------------------+")
    print("|         DataScrap Agent v1.0                 |")
    print("|         Lead Generation Scraper              |")
    print("+----------------------------------------------+")
    print()

    total_start = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Session started at {timestamp}")

    summary = {}

    # --- Run selected scrapers ---
    if args.all or args.upwork:
        try:
            results = run_upwork()
            summary["Upwork"] = len(results)
        except Exception as e:
            logger.error(f"Upwork scraper failed: {e}")
            summary["Upwork"] = f"ERROR: {e}"

    if args.all or args.linkedin:
        try:
            results = run_linkedin()
            summary["LinkedIn"] = len(results)
        except Exception as e:
            logger.error(f"LinkedIn scraper failed: {e}")
            summary["LinkedIn"] = f"ERROR: {e}"

    if args.all or args.directories:
        try:
            results = run_directories()
            summary["Directories"] = len(results)
        except Exception as e:
            logger.error(f"Directories scraper failed: {e}")
            summary["Directories"] = f"ERROR: {e}"

    if args.google_maps:
        # Note: We don't run google-maps in --all by default because it requires input
        try:
            results = run_google_maps()
            summary["Google Maps"] = len(results)
        except Exception as e:
            logger.error(f"Google Maps scraper failed: {e}")
            summary["Google Maps"] = f"ERROR: {e}"

    # --- Print summary ---
    total_elapsed = time.time() - total_start

    print()
    print("+----------------------------------------------+")
    print("|              Scraping Summary                 |")
    print("+----------------------------------------------+")
    for module, count in summary.items():
        status = f"{count} leads" if isinstance(count, int) else str(count)
        print(f"|  {module:<15} | {status:<26} |")
    print("+----------------------------------------------+")
    print(f"|  Total Time      | {total_elapsed:.1f}s{' ' * (24 - len(f'{total_elapsed:.1f}s'))} |")
    print("+----------------------------------------------+")
    print()
    print("Output files saved to: backend/output/")
    print()


if __name__ == "__main__":
    main()
