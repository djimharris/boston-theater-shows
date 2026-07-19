"""Orchestrator that runs all scrapers and collects results."""

import logging
import time
from datetime import datetime, timezone

from scraper.models import Show, ScraperStatus
from scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Runs all registered scrapers, isolating failures and collecting metadata."""

    def __init__(self, scraper_classes: list[type]):
        self.scraper_classes = scraper_classes
        self.shows: list[Show] = []
        self.statuses: list[ScraperStatus] = []

    def run_all(self) -> tuple[list[Show], list[ScraperStatus]]:
        """Execute all scrapers sequentially.

        Each scraper runs in its own try/except so one failure
        doesn't prevent others from completing.
        """
        self.shows = []
        self.statuses = []

        for scraper_cls in self.scraper_classes:
            scraper = scraper_cls()
            theater_name = scraper.THEATER_NAME
            url = scraper.BASE_URL

            logger.info(f"Scraping: {theater_name}")
            start_time = time.time()
            timestamp = datetime.now(timezone.utc).isoformat()

            try:
                scraped_shows = scraper.scrape()

                # Validate and filter
                valid_shows = []
                for show in scraped_shows:
                    if show.is_valid():
                        valid_shows.append(show)
                    else:
                        errors = show.validate()
                        logger.warning(
                            f"[{theater_name}] Invalid show '{show.title}': {errors}"
                        )

                self.shows.extend(valid_shows)
                duration = time.time() - start_time

                self.statuses.append(
                    ScraperStatus(
                        theater_name=theater_name,
                        url=url,
                        success=True,
                        shows_found=len(valid_shows),
                        timestamp=timestamp,
                        duration_seconds=round(duration, 2),
                    )
                )
                logger.info(
                    f"  -> {len(valid_shows)} shows found in {duration:.1f}s"
                )

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"  -> FAILED: {error_msg}")

                self.statuses.append(
                    ScraperStatus(
                        theater_name=theater_name,
                        url=url,
                        success=False,
                        shows_found=0,
                        timestamp=timestamp,
                        error_message=error_msg,
                        duration_seconds=round(duration, 2),
                    )
                )

        return self.shows, self.statuses

    def to_shows_json(self) -> dict:
        """Serialize all shows to the output JSON structure."""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_shows": len(self.shows),
            "shows": [show.to_dict() for show in self.shows],
        }

    def to_status_json(self) -> dict:
        """Serialize scraping metadata to the status JSON structure."""
        successful = sum(1 for s in self.statuses if s.success)
        failed = sum(1 for s in self.statuses if not s.success)

        return {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "total_sites": len(self.statuses),
            "successful": successful,
            "failed": failed,
            "deferred_sites": [
                {
                    "name": "Citizens Bank Opera House",
                    "url": "https://www.citizensoperahouse.com/events/",
                    "reason": "Requires headless browser (JavaScript-rendered content)",
                },
                {
                    "name": "OvationTix",
                    "url": "https://ci.ovationtix.com/34432",
                    "reason": "Requires headless browser (JavaScript-rendered content)",
                },
            ],
            "sites": [status.to_dict() for status in self.statuses],
        }
