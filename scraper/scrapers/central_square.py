"""Scraper for Central Square Theater."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class CentralSquareScraper(BaseScraper):
    """Scrapes shows from centralsquaretheater.org/shows-events/

    The page has a simple structure inside .entry-content:
      - h2 elements are show titles (with <a> links to detail pages)
      - h3 elements immediately following are date ranges
      - No images on listing page
    """

    THEATER_NAME = "Central Square Theater"
    BASE_URL = "https://www.centralsquaretheater.org/shows-events/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        # Find all h2 elements that are show titles
        # First h2 is a tagline, skip it
        content = soup.find(class_='entry-content')
        if not content:
            content = soup

        h2_elements = content.find_all('h2')

        for h2 in h2_elements:
            try:
                show = self._parse_show(h2)
                if show and show.is_valid():
                    shows.append(show)
            except Exception as e:
                logger.debug(f"Failed to parse show from h2: {e}")
                continue

        return shows

    def _parse_show(self, h2):
        """Parse a show from an h2 element and its following h3 sibling."""
        title = clean_text(h2.get_text())
        if not title or len(title) < 3:
            return None

        # Skip non-show headings
        skip_keywords = ['epic stories', 'season', 'subscribe', 'donate',
                        'ticket', 'about', 'contact']
        if any(kw in title.lower() for kw in skip_keywords):
            return None

        # Show URL from link in h2
        link = h2.find('a')
        show_url = ""
        if link and link.get('href'):
            show_url = self.resolve_url(link['href'])

        # Date from the next h3 sibling
        next_h3 = h2.find_next('h3')
        if not next_h3:
            return None

        date_text = clean_text(next_h3.get_text())
        if not date_text:
            return None

        # Verify it looks like a date
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        if not re.search(month_pattern, date_text, re.IGNORECASE):
            return None

        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Description — look for a p element after the h3
        description = ""
        next_p = next_h3.find_next('p')
        if next_p:
            # Make sure this p is before the next h2 (belongs to this show)
            next_h2 = h2.find_next('h2')
            if next_h2 is None or next_p.sourceline < next_h2.sourceline:
                text = next_p.get_text().strip()
                if text and len(text) > 20:
                    description = truncate_description(text)

        return self._make_show(
            title=title,
            start_date=start_date,
            end_date=end_date,
            show_url=show_url or self.BASE_URL,
            description=description,
            image_url="",
            ticket_url="",
        )
