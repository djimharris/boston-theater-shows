"""Entry point for the scraper. Runs all scrapers and writes output JSON files."""

import json
import logging
import os
import sys

from scraper.models import Show
from scraper.orchestrator import ScraperOrchestrator
from scraper.scrapers import ALL_SCRAPERS


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting scraper with {len(ALL_SCRAPERS)} registered sites")

    orchestrator = ScraperOrchestrator(ALL_SCRAPERS)
    orchestrator.run_all()

    # Merge manual entries
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    manual_path = os.path.join(data_dir, "manual_shows.json")
    if os.path.exists(manual_path):
        try:
            with open(manual_path, "r", encoding="utf-8") as f:
                manual_entries = json.load(f)
            added = 0
            for entry in manual_entries:
                show = Show(
                    title=entry.get("title", ""),
                    theater_name=entry.get("theater_name", ""),
                    start_date=entry.get("start_date", ""),
                    end_date=entry.get("end_date", ""),
                    show_url=entry.get("show_url", ""),
                    description=entry.get("description", ""),
                    image_url=entry.get("image_url", ""),
                    ticket_url=entry.get("ticket_url", ""),
                )
                if show.is_valid():
                    orchestrator.shows.append(show)
                    added += 1
                else:
                    logger.warning(f"Skipping invalid manual entry: {entry.get('title', '?')}")
            if added:
                logger.info(f"Added {added} manual show(s)")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse manual_shows.json: {e}")

    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Write shows.json
    shows_path = os.path.join(data_dir, "shows.json")
    with open(shows_path, "w", encoding="utf-8") as f:
        json.dump(orchestrator.to_shows_json(), f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote {orchestrator.to_shows_json()['total_shows']} shows to {shows_path}")

    # Write status.json
    status_path = os.path.join(data_dir, "status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(orchestrator.to_status_json(), f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote status to {status_path}")

    # Report summary
    status_data = orchestrator.to_status_json()
    logger.info(
        f"Done: {status_data['successful']}/{status_data['total_sites']} sites successful, "
        f"{orchestrator.to_shows_json()['total_shows']} total shows"
    )

    # Exit with error code if all scrapers failed
    if status_data["successful"] == 0:
        logger.error("All scrapers failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
