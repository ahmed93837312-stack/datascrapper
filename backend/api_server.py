"""
DataScrap Agent — FastAPI Server
==================================
REST API server that bridges the Next.js frontend with the Python scrapers.
Provides endpoints for triggering scrapes, checking progress, downloading
CSV files, and fetching dashboard stats.

Usage:
    uvicorn api_server:app --reload --port 8000

Endpoints:
    POST /api/scrape/{module}   — Start a scraper (upwork | linkedin | directories)
    GET  /api/status/{module}   — Get scraping progress
    GET  /api/download/{module} — Download CSV file
    GET  /api/stats             — Get dashboard statistics
    GET  /api/preview/{module}  — Preview CSV data (first 50 rows)
"""

import os
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from utils.csv_handler import read_csv, get_row_count, csv_exists, get_csv_path
from utils.logger import setup_logger

logger = setup_logger("api_server")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DataScrap Agent API",
    description="REST API for the DataScrap lead generation agent",
    version="1.0.0",
)

# CORS — allow the Next.js frontend (development and production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Railway deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

class ScraperStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# In-memory state for each scraper module
scraper_state: dict[str, dict] = {
    "upwork": {
        "status": ScraperStatus.IDLE,
        "progress": 0,
        "total": 0,
        "message": "",
        "started_at": None,
        "completed_at": None,
        "error": None,
    },
    "linkedin": {
        "status": ScraperStatus.IDLE,
        "progress": 0,
        "total": 0,
        "message": "",
        "started_at": None,
        "completed_at": None,
        "error": None,
    },
    "directories": {
        "status": ScraperStatus.IDLE,
        "progress": 0,
        "total": 0,
        "message": "",
        "started_at": None,
        "completed_at": None,
        "error": None,
    },
    "google_maps": {
        "status": ScraperStatus.IDLE,
        "progress": 0,
        "total": 0,
        "message": "",
        "started_at": None,
        "completed_at": None,
        "error": None,
    },
}

# Map module names to CSV filenames
CSV_FILES = {
    "upwork": "upwork_jobs.csv",
    "linkedin": "linkedin_jobs.csv",
    "directories": "local_directories.csv",
    "google_maps": "google_maps_master.csv",
}

# Module lock to prevent concurrent runs of the same module
module_locks: dict[str, threading.Lock] = {
    "upwork": threading.Lock(),
    "linkedin": threading.Lock(),
    "directories": threading.Lock(),
    "google_maps": threading.Lock(),
}


# ---------------------------------------------------------------------------
# Scraper thread runners
# ---------------------------------------------------------------------------

def _make_progress_callback(module: str):
    """Create a progress callback bound to a specific module."""
    def callback(current: int, total: int, message: Optional[str] = None):
        scraper_state[module]["progress"] = current
        scraper_state[module]["total"] = total
        if message:
            scraper_state[module]["message"] = message
        else:
            pct = int((current / total) * 100) if total > 0 else 0
            scraper_state[module]["message"] = f"Processing {current}/{total} ({pct}%)"
    return callback


def _run_scraper_thread(module: str, **kwargs):
    """Run a scraper in a background thread."""
    state = scraper_state[module]
    state["status"] = ScraperStatus.RUNNING
    state["progress"] = 0
    state["total"] = 0
    state["error"] = None
    state["started_at"] = datetime.now().isoformat()
    state["completed_at"] = None
    state["message"] = "Initializing…"

    try:
        if module == "upwork":
            from scrapers.upwork_scraper import UpworkScraper
            keywords_str = kwargs.get("keywords")
            keywords = [k.strip() for k in keywords_str.split(",")] if keywords_str else None
            scraper = UpworkScraper(progress_callback=_make_progress_callback(module))
            scraper.run(keywords=keywords)

        elif module == "linkedin":
            from scrapers.linkedin_scraper import LinkedInScraper
            keywords_str = kwargs.get("keywords")
            keywords = [k.strip() for k in keywords_str.split(",")] if keywords_str else None
            location = kwargs.get("location")
            scraper = LinkedInScraper(
                progress_callback=_make_progress_callback(module),
                headless=True,
            )
            scraper.run(keywords=keywords, location=location)

        elif module == "directories":
            from scrapers.directories_scraper import DirectoriesScraper
            niches_str = kwargs.get("niches")
            niches = [n.strip() for n in niches_str.split(",")] if niches_str else None
            scraper = DirectoriesScraper(progress_callback=_make_progress_callback(module))
            scraper.run(niches=niches)

        elif module == "google_maps":
            from scrapers.google_maps_scraper import GoogleMapsScraper
            location = kwargs.get("location") or "New York"
            niche    = kwargs.get("niche") or "restaurants"
            scraper  = GoogleMapsScraper(progress_callback=_make_progress_callback(module))
            if kwargs.get("max_results"):
                scraper.max_results = int(kwargs["max_results"])
            scraper.run(location=location, niche=niche)

        state["status"] = ScraperStatus.COMPLETED
        state["message"] = "Scraping completed successfully"
        state["completed_at"] = datetime.now().isoformat()
        logger.info(f"[{module}] Scraping completed")

    except Exception as e:
        state["status"] = ScraperStatus.FAILED
        state["error"] = str(e)
        state["message"] = f"Failed: {e}"
        state["completed_at"] = datetime.now().isoformat()
        logger.error(f"[{module}] Scraping failed: {e}")

    finally:
        module_locks[module].release()


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "DataScrap Agent API", "version": "1.0.0"}


@app.post("/api/scrape/{module}")
async def start_scraper(
    module: str,
    location: Optional[str] = None,
    niche: Optional[str] = None,
    keywords: Optional[str] = None,
    niches: Optional[str] = None,
    max_results: Optional[int] = None,
):
    """
    Trigger a scraper module to run in the background.

    Path params:
        module: One of 'upwork', 'linkedin', 'directories', 'google_maps'
    """
    if module not in scraper_state:
        raise HTTPException(status_code=404, detail=f"Unknown module: {module}")

    # Check if already running
    if not module_locks[module].acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail=f"The {module} scraper is already running.",
        )

    # Launch scraper in background thread
    thread = threading.Thread(
        target=_run_scraper_thread,
        args=(module,),
        kwargs={
            "location": location,
            "niche": niche,
            "keywords": keywords,
            "niches": niches,
            "max_results": max_results,
        },
        daemon=True
    )
    thread.start()

    logger.info(f"[{module}] Scraper triggered")
    return {
        "status": "started",
        "module": module,
        "message": f"{module.capitalize()} scraper started",
    }


@app.get("/api/status/{module}")
async def get_status(module: str):
    """
    Get the current status and progress of a scraper module.
    """
    if module not in scraper_state:
        raise HTTPException(status_code=404, detail=f"Unknown module: {module}")

    state = scraper_state[module]

    # Calculate percentage
    pct = 0
    if state["total"] > 0:
        pct = int((state["progress"] / state["total"]) * 100)

    return {
        "module": module,
        "status": state["status"],
        "progress": state["progress"],
        "total": state["total"],
        "percentage": pct,
        "message": state["message"],
        "started_at": state["started_at"],
        "completed_at": state["completed_at"],
        "error": state["error"],
    }


@app.get("/api/download/{module}")
async def download_csv(module: str):
    """
    Download the CSV file for a completed scraper module.
    """
    if module not in CSV_FILES:
        raise HTTPException(status_code=404, detail=f"Unknown module: {module}")

    filename = CSV_FILES[module]
    filepath = get_csv_path(filename)

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"No CSV file found for {module}. Run the scraper first.",
        )

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/preview/{module}")
async def preview_data(module: str, limit: int = 50):
    """
    Preview the first N rows of a scraper's CSV output.

    Query params:
        limit: Number of rows to return (default 50, max 200)
    """
    if module not in CSV_FILES:
        raise HTTPException(status_code=404, detail=f"Unknown module: {module}")

    limit = min(limit, 200)
    filename = CSV_FILES[module]
    rows = read_csv(filename)

    return {
        "module": module,
        "total_rows": len(rows),
        "showing": min(limit, len(rows)),
        "data": rows[:limit],
    }


@app.get("/api/stats")
async def get_stats():
    """
    Get aggregate statistics for the dashboard.
    Returns row counts and status for each module.
    """
    stats = {}
    total_leads = 0

    for module, filename in CSV_FILES.items():
        count = get_row_count(filename) if csv_exists(filename) else 0
        total_leads += count
        stats[module] = {
            "leads": count,
            "has_data": csv_exists(filename),
            "status": scraper_state[module]["status"],
            "last_run": scraper_state[module].get("completed_at"),
        }

    return {
        "total_leads": total_leads,
        "modules": stats,
    }


# ---------------------------------------------------------------------------
# Run with: uvicorn api_server:app --reload --port 8000
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print()
    print("+----------------------------------------------+")
    print("|       DataScrap Agent -- API Server           |")
    print("|       http://localhost:8000                   |")
    print("|       Docs: http://localhost:8000/docs        |")
    print("+----------------------------------------------+")
    print()

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

