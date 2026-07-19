"""Scraper for Apollinaire Theatre Company."""

import logging
import re

from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class ApollinaireScraper(BaseScraper):
    """Scrapes shows from apollinairetheatre.com/productions/season.php

    Simple static page with:
      - h2 for show titles (skip the first which is a season greeting)
      - h6 for dates (format: "December 12, 2025-January 11, 2026")
      - p elements for descriptions/quotes
      - Links to OvationTix for tickets
    """

    THEATER_NAME = "Apollinaire Theatre Company"
    BASE_URL = "https://www.apollinairetheatre.com/productions/season.php"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        h2_elements = soup.find_all('h2')

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
        """Parse a show from an h2 title and its following elements."""
        title = clean_text(h2.get_text())
        if not title or len(title) < 3:
            return None

        # Skip non-show headings
        skip_keywords = ['thank you', 'season', 'subscribe', 'see three',
                        'join us', 'support', 'donate', 'welcome']
        if any(kw in title.lower() for kw in skip_keywords):
            return None

        # Find the h6 date element after this h2 (before next h2)
        next_h6 = h2.find_next('h6')
        next_h2 = h2.find_next('h2')

        if not next_h6:
            return None

        # Make sure the h6 belongs to this h2 (comes before the next h2)
        if next_h2 and next_h6.sourceline and next_h2.sourceline:
            if next_h6.sourceline > next_h2.sourceline:
                return None

        date_text = clean_text(next_h6.get_text())
        if not date_text:
            return None

        # Apollinaire uses format like "December 12, 2025-January 11, 2026"
        # or "February 20-March 22, 2026"
        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Description — first meaningful p after h6 but before next h2
        description = ""
        for sibling in next_h6.find_next_siblings(['p', 'h2']):
            if sibling.name == 'h2':
                break
            text = sibling.get_text().strip()
            if text and len(text) > 20:
                description = truncate_description(text)
                break

        # Ticket link — look for OvationTix links after this h2
        ticket_url = ""
        for sibling in h2.find_next_siblings(['a', 'p', 'h2']):
            if sibling.name == 'h2':
                break
            if sibling.name == 'a':
                href = sibling.get('href', '')
                if 'ovationtix' in href or 'ticket' in href.lower():
                    ticket_url = href
                    break
            elif sibling.name == 'p':
                link = sibling.find('a', href=True)
                if link:
                    href = link.get('href', '')
                    if 'ovationtix' in href or 'ticket' in href.lower():
                        ticket_url = href
                        break

        return self._make_show(
            title=title,
            start_date=start_date,
            end_date=end_date,
            show_url=self.BASE_URL,
            description=description,
            image_url="",
            ticket_url=ticket_url,
        )
