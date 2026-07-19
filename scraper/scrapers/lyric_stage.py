"""Scraper for Lyric Stage Company of Boston."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class LyricStageScraper(BaseScraper):
    """Scrapes shows from lyricstage.com/whats-on/

    The page uses a grid layout inside .section-event_feed with cards that have:
      - h3 for show title
      - p.date-range for date text (format: "Sep 18 - Oct 18, 2026")
      - a[href*="/production/"] for more info link
      - Description in a p tag between title and dates
    Cards are identified by their Tailwind border classes.
    """

    THEATER_NAME = "Lyric Stage Company"
    BASE_URL = "https://www.lyricstage.com/whats-on/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        # Find the event feed section
        feed = soup.find(class_='section-event_feed')
        if not feed:
            # Fallback: search whole page
            feed = soup

        # Cards are divs with border styling containing h3 + date-range
        # Look for elements with the date-range class
        date_elems = feed.find_all(class_='date-range')

        if date_elems:
            # Each date-range is inside a card — walk up to card container
            for date_elem in date_elems:
                try:
                    show = self._parse_from_date_elem(date_elem)
                    if show and show.is_valid():
                        shows.append(show)
                except Exception as e:
                    logger.debug(f"Failed to parse card: {e}")
                    continue
        else:
            # Fallback: find h3 elements with nearby date patterns
            shows = self._fallback_parse(feed)

        return shows

    def _parse_from_date_elem(self, date_elem):
        """Parse a show card starting from the date-range element."""
        # Walk up to the card container (a div with border classes)
        card = date_elem
        for _ in range(5):
            card = card.parent
            if card is None:
                return None
            classes = card.get('class', [])
            # The card container has border styling
            if any('border' in c for c in classes) and any('h-full' in c or 'flex' in c for c in classes):
                break

        # Title from h3
        h3 = card.find('h3')
        if not h3:
            return None
        title = clean_text(h3.get_text())
        if not title:
            return None

        # Date from the date-range element
        date_text = clean_text(date_elem.get_text())
        if not date_text:
            return None

        # The date format uses a <span> for the dash, producing text like "Sep 18 - Oct 18, 2026"
        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # Description — p tag between title and dates
        description = ""
        for p in card.find_all('p'):
            text = p.get_text().strip()
            if text and 'date-range' not in ' '.join(p.get('class', [])) and len(text) > 10:
                description = truncate_description(text)
                break

        # Show URL from "More Info" link
        show_url = ""
        for a in card.find_all('a', href=True):
            href = a['href']
            if '/production/' in href:
                show_url = self.resolve_url(href)
                break

        # Image — look for img in the card's parent grid item
        image_url = ""
        # The image is typically in a sibling div to the card content
        grid_item = card.parent
        if grid_item:
            img = grid_item.find('img')
            if img:
                src = img.get('src') or img.get('data-src')
                if src:
                    image_url = self.resolve_url(src)

        return self._make_show(
            title=title,
            start_date=start_date,
            end_date=end_date,
            show_url=show_url or self.BASE_URL,
            description=description,
            image_url=image_url,
            ticket_url="",
        )

    def _fallback_parse(self, container):
        """Fallback parsing when date-range class is not found."""
        shows = []
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

        for h3 in container.find_all('h3'):
            title = clean_text(h3.get_text())
            if not title or len(title) < 3:
                continue

            # Look for date in nearby elements
            parent = h3.parent
            if not parent:
                continue

            date_text = None
            for elem in parent.find_all(['p', 'span']):
                text = elem.get_text().strip()
                if re.search(month_pattern, text, re.IGNORECASE) and re.search(r'\d', text):
                    if len(text) < 60:
                        date_text = clean_text(text)
                        break

            if not date_text:
                continue

            try:
                start_date, end_date = parse_date_range(date_text)
            except (ValueError, TypeError):
                continue

            show_url = ""
            for a in parent.find_all('a', href=True):
                if '/production/' in a['href']:
                    show_url = self.resolve_url(a['href'])
                    break

            show = self._make_show(
                title=title,
                start_date=start_date,
                end_date=end_date,
                show_url=show_url or self.BASE_URL,
            )
            if show.is_valid():
                shows.append(show)

        return shows
