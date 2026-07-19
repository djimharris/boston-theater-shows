"""Scraper for SpeakEasy Stage Company."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class SpeakeasyScraper(BaseScraper):
    """Scrapes shows from speakeasystage.com/shows/

    Clean structure with article/card elements containing titles,
    dates, creator credits, descriptions, and images.
    """

    THEATER_NAME = "SpeakEasy Stage Company"
    BASE_URL = "https://speakeasystage.com/shows/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        # Try specific selectors first, then fallback
        cards = soup.select(
            'article, .show, .production, [class*="show-item"], '
            '[class*="production"], .entry'
        )

        if not cards:
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
        """Fallback: identify show blocks from heading patterns."""
        blocks = []
        for heading in soup.find_all(['h2', 'h3']):
            link = heading.find('a')
            if link and link.get('href') and '/shows/' in link.get('href', ''):
                parent = heading.parent
                if parent and parent not in blocks:
                    blocks.append(parent)
        return blocks

    def _parse_card(self, card):
        """Parse a show card element."""
        title_elem = card.find(['h2', 'h3', 'h4'])
        if not title_elem:
            return None

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            return None

        # Skip non-show headings
        skip_keywords = ['season', 'subscribe', 'donate', 'about', 'contact', 'menu']
        if any(kw in title.lower() for kw in skip_keywords):
            return None

        # URL
        link = title_elem.find('a') or card.find('a')
        show_url = ""
        if link and link.get('href'):
            href = link['href']
            if '/shows/' in href:
                show_url = self.resolve_url(href)

        # Date
        date_text = self._find_date_text(card)
        if not date_text:
            return None

        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Image (may be lazy-loaded)
        img = card.find('img')
        image_url = ""
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src and not src.endswith(('.svg', 'placeholder')):
                image_url = self.resolve_url(src)

        # Description
        description = ""
        for p in card.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 30 and not self._is_date_text(text):
                description = truncate_description(text)
                break

        # Ticket link
        ticket_url = ""
        for a in card.find_all('a'):
            text = a.get_text().lower()
            if 'ticket' in text or 'buy' in text or 'reserve' in text:
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
        """Extract date text from the card."""
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

        for elem in card.find_all(['span', 'p', 'div', 'strong', 'em', 'time', 'h5', 'h6']):
            text = elem.get_text().strip()
            if re.search(month_pattern, text, re.IGNORECASE) and re.search(r'\d', text):
                if len(text) < 80:
                    return clean_text(text)
        return None

    def _is_date_text(self, text):
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        return bool(re.search(month_pattern, text, re.IGNORECASE)) and len(text) < 60
