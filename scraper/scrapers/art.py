"""Scraper for American Repertory Theater (A.R.T.)."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class ARTScraper(BaseScraper):
    """Scrapes shows from americanrepertorytheater.org/shows-events/

    Server-rendered page with h4 cards, WordPress media URLs for images,
    date ranges in li elements, and venue information.
    """

    THEATER_NAME = "American Repertory Theater"
    BASE_URL = "https://americanrepertorytheater.org/shows-events/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        # ART uses card-like sections for each show
        cards = soup.select(
            'article, .show-card, [class*="production"], '
            '[class*="show-listing"], [class*="event-card"], '
            '.card, .entry'
        )

        if not cards:
            cards = self._find_show_blocks(soup)

        for card in cards:
            try:
                show = self._parse_card(card)
                if show and show.is_valid():
                    # Deduplicate
                    if not any(s.title == show.title for s in shows):
                        shows.append(show)
            except Exception as e:
                logger.debug(f"Failed to parse card: {e}")
                continue

        return shows

    def _find_show_blocks(self, soup):
        """Fallback: find blocks from h4 headings with links."""
        blocks = []
        for heading in soup.find_all(['h4', 'h3', 'h2']):
            link = heading.find('a')
            if link and link.get('href'):
                # Get a parent container that likely holds the full card
                parent = heading.parent
                # Try to get a higher-level container
                if parent and parent.parent:
                    grandparent = parent.parent
                    if grandparent not in blocks:
                        blocks.append(grandparent)
                elif parent:
                    blocks.append(parent)
        return blocks

    def _parse_card(self, card):
        """Parse a show card."""
        # Title from h4 (primary) or h3/h2
        title_elem = card.find(['h4', 'h3', 'h2'])
        if not title_elem:
            return None

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            return None

        # Skip non-show elements
        skip_words = ['subscribe', 'donate', 'membership', 'support', 'menu', 'search']
        if any(w in title.lower() for w in skip_words):
            return None

        # URL
        link = title_elem.find('a') or card.find('a')
        show_url = ""
        if link and link.get('href'):
            href = link['href']
            if 'americanrepertorytheater' in href or href.startswith('/'):
                show_url = self.resolve_url(href)

        # Dates — often in li elements or spans
        date_text = self._find_date_text(card)
        if not date_text:
            return None

        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Image — WordPress media URLs
        img = card.find('img')
        image_url = ""
        if img:
            src = img.get('src') or img.get('data-src') or img.get('srcset', '').split(' ')[0]
            if src and 'logo' not in src.lower():
                image_url = self.resolve_url(src)

        # Description
        description = ""
        for p in card.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 30 and not self._is_date_like(text):
                description = truncate_description(text)
                break

        # Venue info
        venue = ""
        for li in card.find_all('li'):
            text = li.get_text().strip()
            if 'theater' in text.lower() or 'loeb' in text.lower() or 'oberon' in text.lower():
                venue = clean_text(text)
                break

        if venue and description:
            description = f"{venue} | {description}"
        elif venue:
            description = venue

        # Ticket/booking link
        ticket_url = ""
        for a in card.find_all('a'):
            text = a.get_text().lower()
            if 'book' in text or 'ticket' in text or 'buy' in text:
                ticket_url = self.resolve_url(a.get('href', ''))
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
        """Find date text in card — ART often puts dates in li elements."""
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

        # Check li elements first (ART's common pattern)
        for li in card.find_all('li'):
            text = li.get_text().strip()
            if re.search(month_pattern, text, re.IGNORECASE) and re.search(r'\d', text):
                if len(text) < 60:
                    return clean_text(text)

        # Then check other elements
        for elem in card.find_all(['span', 'p', 'div', 'strong', 'time']):
            text = elem.get_text().strip()
            if re.search(month_pattern, text, re.IGNORECASE) and re.search(r'\d', text):
                if len(text) < 80:
                    return clean_text(text)

        return None

    def _is_date_like(self, text):
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        return bool(re.search(month_pattern, text, re.IGNORECASE)) and len(text) < 60
