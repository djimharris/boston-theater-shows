"""Scraper for Boston Theatre Scene — aggregator site with pagination."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class BostonTheatreSceneScraper(BaseScraper):
    """Scrapes shows from bostontheatrescene.com/shows-and-events/

    This is itself an aggregator with many shows listed in a paginated grid.
    Each card has title, producer, venue, dates, and image.
    Pagination is handled by following 'next' links.
    """

    THEATER_NAME = "Boston Theatre Scene"
    BASE_URL = "https://www.bostontheatrescene.com/shows-and-events/"
    MAX_PAGES = 5  # Safety limit to avoid infinite pagination

    def scrape(self) -> list[Show]:
        shows = []
        seen_titles = set()
        url = self.BASE_URL
        pages_scraped = 0

        while url and pages_scraped < self.MAX_PAGES:
            soup = self.fetch_page(url)
            page_shows = self._parse_page(soup)
            for show in page_shows:
                if show.title not in seen_titles:
                    shows.append(show)
                    seen_titles.add(show.title)
            pages_scraped += 1

            # Find next page link
            url = self._find_next_page(soup)
            if url:
                logger.debug(f"Following pagination to: {url}")

        return shows

    def _parse_page(self, soup):
        """Parse a single page of show listings."""
        shows = []

        # The site uses .c-event-card__wrapper for each show card
        cards = soup.select('.c-event-card__wrapper')

        if not cards:
            # Fallback for layout changes
            cards = self._find_show_blocks(soup)

        for card in cards:
            try:
                show = self._parse_card(card)
                if show and show.is_valid():
                    shows.append(show)
            except Exception as e:
                logger.debug(f"Failed to parse card: {e}")
                continue

        return shows

    def _find_show_blocks(self, soup):
        """Fallback: find blocks with h3 headings."""
        blocks = []
        for heading in soup.find_all('h3'):
            text = heading.get_text().strip()
            if text and len(text) > 2:
                parent = heading.parent
                if parent:
                    blocks.append(parent)
        return blocks

    def _parse_card(self, card):
        """Parse one show card."""
        # Title from h3.c-event-card__title
        title_elem = card.find('h3', class_=re.compile(r'event-card__title'))
        if not title_elem:
            title_elem = card.find(['h3', 'h2', 'h4'])
        if not title_elem:
            return None

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            return None

        # URL from .c-event-card__permalink
        show_url = ""
        permalink = card.find('a', class_=re.compile(r'event-card__permalink'))
        if permalink and permalink.get('href'):
            show_url = self.resolve_url(permalink['href'])
        else:
            link = title_elem.find('a') or card.find('a')
            if link and link.get('href'):
                show_url = self.resolve_url(link['href'])

        # Dates from time.c-event-card__daterange
        date_text = None
        time_elem = card.find('time', class_=re.compile(r'event-card__daterange'))
        if time_elem:
            date_text = clean_text(time_elem.get_text())
        if not date_text:
            date_text = self._find_date_text(card)
        if not date_text:
            return None

        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Image (lazy-loaded)
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

        # Description from presenter + venue
        description = ""
        presenter = card.find(class_=re.compile(r'event-card__presenter'))
        venue = card.find(class_=re.compile(r'event-card__venue'))
        parts = []
        if presenter:
            parts.append(clean_text(presenter.get_text()))
        if venue:
            parts.append(clean_text(venue.get_text()))
        if parts:
            description = truncate_description(' — '.join(parts))

        # Ticket/buy link from buttons area
        ticket_url = ""
        buttons = card.find(class_=re.compile(r'event-card__buttons'))
        if buttons:
            for a in buttons.find_all('a', href=True):
                text = a.get_text().lower()
                if 'ticket' in text or 'buy' in text:
                    ticket_url = self.resolve_url(a['href'])
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

    def _find_date_text(self, card):
        """Find date range text in a card."""
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

        for elem in card.find_all(['span', 'p', 'div', 'strong', 'time', 'em']):
            text = elem.get_text().strip()
            if re.search(month_pattern, text, re.IGNORECASE) and re.search(r'\d', text):
                if len(text) < 80:
                    return clean_text(text)
        return None

    def _find_next_page(self, soup):
        """Find the 'next page' link for pagination."""
        # Common pagination patterns
        next_link = soup.find('a', string=re.compile(r'next|›|»', re.IGNORECASE))
        if not next_link:
            next_link = soup.find('a', class_=re.compile(r'next', re.IGNORECASE))
        if not next_link:
            next_link = soup.find('a', rel='next')

        if next_link and next_link.get('href'):
            return self.resolve_url(next_link['href'])
        return None

    def _is_date_like(self, text):
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        return bool(re.search(month_pattern, text, re.IGNORECASE)) and len(text) < 60
