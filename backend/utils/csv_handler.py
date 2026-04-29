"""
Shared CSV read/write utilities for all scraper modules.
Handles file creation, appending rows, and reading results.
"""

import csv
import os
from typing import Any

from .logger import setup_logger

logger = setup_logger("csv_handler")

# Base output directory (relative to backend/)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def ensure_output_dir() -> str:
    """Create the output directory if it doesn't exist. Returns the path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def write_csv(filename: str, headers: list[str], rows: list[dict[str, Any]]) -> str:
    """
    Write rows to a CSV file in the output directory.
    Overwrites any existing file with the same name.

    Args:
        filename: Name of the CSV file (e.g., 'upwork_jobs.csv').
        headers: List of column header names.
        rows: List of dicts, each representing one row.

    Returns:
        Full path to the written CSV file.
    """
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        logger.info(f"Wrote {len(rows)} rows to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to write CSV '{filename}': {e}")
        raise


def append_csv(filename: str, headers: list[str], rows: list[dict[str, Any]]) -> str:
    """
    Append rows to an existing CSV file, or create it if it doesn't exist.

    Args:
        filename: Name of the CSV file.
        headers: List of column header names.
        rows: List of dicts to append.

    Returns:
        Full path to the CSV file.
    """
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, filename)
    file_exists = os.path.isfile(filepath)

    try:
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            for row in rows:
                writer.writerow(row)

        logger.info(f"Appended {len(rows)} rows to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to append to CSV '{filename}': {e}")
        raise


def read_csv(filename: str) -> list[dict[str, str]]:
    """
    Read all rows from a CSV file in the output directory.

    Args:
        filename: Name of the CSV file.

    Returns:
        List of dicts, each representing one row.
    """
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not os.path.isfile(filepath):
        logger.warning(f"CSV file not found: {filepath}")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    except Exception as e:
        logger.error(f"Failed to read CSV '{filename}': {e}")
        return []


def get_row_count(filename: str) -> int:
    """Return the number of data rows in a CSV file (excluding header)."""
    return len(read_csv(filename))


def csv_exists(filename: str) -> bool:
    """Check if a CSV file exists in the output directory."""
    return os.path.isfile(os.path.join(OUTPUT_DIR, filename))


def get_csv_path(filename: str) -> str:
    """Get the full path to a CSV file in the output directory."""
    return os.path.join(OUTPUT_DIR, filename)


def write_json(filename: str, data: Any) -> str:
    """
    Write data to a JSON file in the output directory.
    
    Args:
        filename: Name of the JSON file.
        data: Data to write (usually a list of dicts).
        
    Returns:
        Full path to the written JSON file.
    """
    import json
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Wrote data to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to write JSON '{filename}': {e}")
        raise
