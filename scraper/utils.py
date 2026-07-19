"""Utility functions for date parsing, URL resolution, and text processing."""

import re
from datetime import datetime
from urllib.parse import urljoin

from dateutil import parser as dateutil_parser


def parse_date_range(text: str, reference_year: int = None) -> tuple[str, str]:
    """Parse a date range string into (start_date, end_date) in YYYY-MM-DD format.

    Handles formats like:
      - "September 10 - October 11, 2026"
      - "Nov 5 - 22, 2026" (same month)
      - "September 10 – October 11, 2026" (en-dash)
      - "October 7, 2026" (single date)
      - "Sep 10 - Oct 11" (no year — uses reference_year or current year)
      - "September 2026" (whole month)
    """
    if reference_year is None:
        reference_year = datetime.now().year

    text = text.strip()
    # Normalize dashes: en-dash, em-dash, and variations with spaces
    text = re.sub(r"\s*[–—-]+\s*", " - ", text)
    # Remove "through" / "thru" as separators
    text = re.sub(r"\s+(?:through|thru)\s+", " - ", text, flags=re.IGNORECASE)

    # Check if it's a range (contains separator)
    if " - " in text:
        parts = text.split(" - ", 1)
        start_text = parts[0].strip()
        end_text = parts[1].strip()

        # Detect "same month" pattern: end_text is just a day number (possibly with year)
        # e.g., "November 5 - 22, 2026" → start="November 5", end="22, 2026"
        # We need to prepend the month from start_text to end_text
        month_names = (
            "January|February|March|April|May|June|July|August|"
            "September|October|November|December|"
            "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
        )
        start_month_match = re.match(rf"({month_names})\s+\d", start_text, re.IGNORECASE)
        end_has_month = re.search(rf"({month_names})", end_text, re.IGNORECASE)

        if start_month_match and not end_has_month:
            # End text lacks a month — prepend start's month
            month_name = start_month_match.group(1)
            end_text = f"{month_name} {end_text}"

        # Parse end date first (more likely to have the year)
        end_date = _parse_single_date(end_text, reference_year)

        # If start date lacks a year, use end date's year
        start_date = _parse_single_date(start_text, end_date.year)

        # If start lacks a month (e.g., "5 - 22, November 2026"), use end's month
        # This is handled by checking if start_text is just a number
        if re.match(r"^\d{1,2}$", start_text):
            start_date = start_date.replace(month=end_date.month)

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    else:
        # Single date — start and end are the same
        date = _parse_single_date(text, reference_year)
        return date.strftime("%Y-%m-%d"), date.strftime("%Y-%m-%d")


def _parse_single_date(text: str, default_year: int) -> datetime:
    """Parse a single date string, filling in default_year if not present."""
    text = text.strip()
    # Remove day-of-week prefixes
    text = re.sub(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Remove time components for date-only parsing
    text = re.sub(r"\s+at\s+\d+[:\d]*\s*[ap]m", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\d{1,2}:\d{2}\s*[ap]m", "", text, flags=re.IGNORECASE)

    # Handle "Month Year" format (e.g., "September 2026")
    month_year_match = re.match(
        r"^(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(\d{4})$",
        text,
        re.IGNORECASE,
    )
    if month_year_match:
        return dateutil_parser.parse(f"1 {text}")

    try:
        parsed = dateutil_parser.parse(text, default=datetime(default_year, 1, 1))
        return parsed
    except (ValueError, OverflowError):
        # Last resort: try with just the year appended
        try:
            return dateutil_parser.parse(
                f"{text} {default_year}", default=datetime(default_year, 1, 1)
            )
        except (ValueError, OverflowError):
            raise ValueError(f"Cannot parse date: '{text}'")


def resolve_url(base_url: str, relative_url: str) -> str:
    """Resolve a relative or absolute URL against a base URL."""
    if not relative_url:
        return ""
    if relative_url.startswith(("http://", "https://")):
        return relative_url
    if relative_url.startswith("//"):
        return "https:" + relative_url
    return urljoin(base_url, relative_url)


def clean_text(text: str) -> str:
    """Strip extra whitespace and normalize unicode."""
    if not text:
        return ""
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_description(text: str, max_length: int = 200) -> str:
    """Truncate at word boundary with ellipsis."""
    text = clean_text(text)
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(" ", 1)[0]
    return truncated.rstrip(".,;:!?") + "..."
