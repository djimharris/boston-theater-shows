"""Scraper for Huntington Theatre Company."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class HuntingtonScraper(BaseScraper):
    """Scrapes shows from huntingtontheatre.org/plays-and-events/

    The page uses .c-event-card elements (the main show grid) with:
      - h3.c-col-title for show title
      - a.c-event-card__link for show URL
      - p.c-event-card__date for date text
      - figure img for show image
      - a.c-book-btn for ticket URL
    """

    THEATER_NAME = "Huntington Theatre"
    BASE_URL = "https://www.huntingtontheatre.org/plays-and-events/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        cards = soup.select('.c-event-card')
        if not cards:
            logger.warning("No .c-event-card elements found")
            return shows

        seen_titles = set()
        for card in cards:
            try:
                show = self._parse_card(card)
                if show and show.is_valid() and show.title not in seen_titles:
                    shows.append(show)
                    seen_titles.add(show.title)
            except Exception as e:
                logger.debug(f"Failed to parse card: {e}")
                continue

        return shows

    def _parse_card(self, card):
        """Parse a .c-event-card element."""
        # Title from h3
        title_elem = card.find('h3')
        if not title_elem:
            return None

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            return None

        # Show URL from a.c-event-card__link
        link = card.find('a', class_=re.compile(r'event-card__link'))
        show_url = ""
        if link and link.get('href'):
            show_url = self.resolve_url(link['href'])

        # Date from p.c-event-card__date
        date_elem = card.find('p', class_=re.compile(r'event-card__date'))
        if not date_elem:
            return None

        date_text = clean_text(date_elem.get_text())
        if not date_text:
            return None

        # Strip ordinal suffixes (e.g. "24th" -> "24")
        date_text = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', date_text)

        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Description
        description = ""
        desc_elem = card.find(class_=re.compile(r'event-card__description'))
        if desc_elem:
            description = truncate_description(desc_elem.get_text())

        # Image
        image_url = ""
        img = card.find('img')
        if img:
            src = img.get('data-srcset') or img.get('src') or img.get('data-src')
            if src:
                # data-srcset has multiple URLs; take the largest
                if ',' in src:
                    parts = [p.strip().split()[0] for p in src.split(',')]
                    src = parts[-1] if parts else src
                image_url = self.resolve_url(src)

        # Ticket URL from a.c-book-btn
        ticket_url = ""
        ticket_link = card.find('a', class_=re.compile(r'book-btn|btn'))
        if ticket_link and ticket_link.get('href'):
            ticket_url = self.resolve_url(ticket_link['href'])

        return self._make_show(
            title=title,
            start_date=start_date,
            end_date=end_date,
            show_url=show_url or self.BASE_URL,
            description=description,
            image_url=image_url,
            ticket_url=ticket_url,
        )
