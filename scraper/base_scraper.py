"""Abstract base class for all theater scrapers."""

import logging
import time
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scraper.models import Show
from scraper.utils import resolve_url, clean_text, truncate_description, parse_date_range

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class providing common scraping infrastructure.

    Subclasses must define THEATER_NAME, BASE_URL, and implement scrape().
    """

    THEATER_NAME: str = ""
    BASE_URL: str = ""

    # Configuration
    TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds between retries
    POLITENESS_DELAY = 1  # seconds between requests to same site

    def __init__(self, session: requests.Session = None):
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "BostonTheaterAggregator/1.0 "
                    "(+https://github.com/showscraper; educational project)"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self._last_request_time = 0

    @abstractmethod
    def scrape(self) -> list[Show]:
        """Fetch and parse shows from this theater's website.

        Returns a list of validated Show objects.
        Must be implemented by each subclass.
        """
        pass

    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch a URL and return a parsed BeautifulSoup object.

        Includes retry logic, timeout handling, and politeness delays.
        """
        self._wait_for_politeness()

        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.debug(f"[{self.THEATER_NAME}] Fetching {url} (attempt {attempt})")
                response = self.session.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                self._last_request_time = time.time()
                return BeautifulSoup(response.text, "lxml")
            except requests.RequestException as e:
                last_error = e
                logger.warning(
                    f"[{self.THEATER_NAME}] Attempt {attempt} failed for {url}: {e}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * attempt)

        raise last_error

    def resolve_url(self, relative_url: str) -> str:
        """Resolve a relative URL against this scraper's BASE_URL."""
        return resolve_url(self.BASE_URL, relative_url)

    def _wait_for_politeness(self):
        """Ensure minimum delay between requests to the same site."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.POLITENESS_DELAY:
            time.sleep(self.POLITENESS_DELAY - elapsed)

    def _make_show(
        self,
        title: str,
        start_date: str,
        end_date: str,
        show_url: str,
        description: str = "",
        image_url: str = "",
        ticket_url: str = "",
    ) -> Show:
        """Helper to create a Show with this scraper's theater name and text cleaning."""
        return Show(
            title=clean_text(title),
            theater_name=self.THEATER_NAME,
            start_date=start_date,
            end_date=end_date,
            show_url=show_url,
            description=truncate_description(description),
            image_url=image_url,
            ticket_url=ticket_url,
        )
