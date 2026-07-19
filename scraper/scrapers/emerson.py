"""Scraper for Emerson Colonial Theatre (uses Tribe Events plugin)."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class EmersonScraper(BaseScraper):
    """Scrapes shows from emersontheatres.org/

    This site uses The Events Calendar (Tribe Events) WordPress plugin,
    which provides well-known CSS class patterns.
    """

    THEATER_NAME = "Emerson Colonial Theatre"
    BASE_URL = "https://emersontheatres.org/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        # Tribe Events event rows (skips month separator headers)
        cards = soup.select('.tribe-events-calendar-list__event-row')

        if not cards:
            # Fallback: select article elements directly
            cards = soup.select('article.tribe-events-calendar-list__event')

        if not cards:
            cards = self._find_show_blocks(soup)

        for card in cards:
            try:
                show = self._parse_card(card)
                if show and show.is_valid():
                    # Deduplicate by title
                    if not any(s.title == show.title for s in shows):
                        shows.append(show)
            except Exception as e:
                logger.debug(f"Failed to parse card: {e}")
                continue

        return shows

    def _find_show_blocks(self, soup):
        """Fallback: find show blocks from headings."""
        blocks = []
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            link = heading.find('a')
            if link and link.get('href'):
                parent = heading.parent
                if parent and parent not in blocks:
                    blocks.append(parent)
        return blocks

    def _parse_card(self, card):
        """Parse a Tribe Events event row."""
        # Title from h4 (event rows use h4, not h3)
        title_elem = card.find('h4')
        if not title_elem:
            title_elem = card.find('h3')
        if not title_elem:
            return None

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            return None

        # Skip generic page elements
        if title.lower() in ('events', 'upcoming events', 'past events'):
            return None

        # URL from link in title
        link = title_elem.find('a')
        show_url = ""
        if link and link.get('href'):
            show_url = self.resolve_url(link['href'])

        # Date from time element with datetime attribute
        date_text = self._find_tribe_date(card)
        if not date_text:
            return None

        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Image
        img = card.find('img')
        image_url = ""
        if img:
            src = img.get('src') or img.get('data-src')
            if src and 'placeholder' not in src.lower():
                image_url = self.resolve_url(src)

        # Description
        description = ""
        desc_elem = card.find(class_=re.compile(r'description', re.IGNORECASE))
        if desc_elem:
            description = truncate_description(desc_elem.get_text())

        # Ticket link
        ticket_url = ""
        for a in card.find_all('a'):
            text = a.get_text().lower()
            href = a.get('href', '')
            if 'ticket' in text or 'ticket' in href:
                ticket_url = self.resolve_url(href)
                break

        return self._make_show(
            title=title,
            start_date=start_date,
            end_date=end_date,
            show_url=show_url or self.BASE_URL,
            description=description,
            image_url=image_url,
            ticket_url=ticket_url,
        )

    def _find_tribe_date(self, card):
        """Extract date from Tribe Events markup.

        The event row has a date-tag time (just weekday+day) and a datetime time
        inside the article (full date text like "October 7, 2026 at 8:00 pm").
        We want the latter — identified by class containing 'datetime'.
        """
        # Look for the full datetime element (inside the article, not the date-tag)
        datetime_elem = card.find(class_=re.compile(r'event-datetime|__datetime', re.IGNORECASE))
        if datetime_elem:
            text = clean_text(datetime_elem.get_text())
            # Strip time portions: "October 7, 2026 at 8:00 pm" -> "October 7, 2026"
            text = re.sub(r'\s+at\s+\d{1,2}:\d{2}\s*(?:am|pm)?', '', text, flags=re.IGNORECASE)
            return text

        # Fallback: find time elements with a datetime attribute containing a full date
        for time_elem in card.find_all('time'):
            dt = time_elem.get('datetime', '')
            text = clean_text(time_elem.get_text())
            # Skip the date-tag (just has weekday + day number, no month name)
            month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
            if re.search(month_pattern, text, re.IGNORECASE):
                # Strip time portions
                text = re.sub(r'\s+at\s+\d{1,2}:\d{2}\s*(?:am|pm)?', '', text, flags=re.IGNORECASE)
                return text

        return None
