"""Scraper for Wheelock Family Theatre."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)

# Date regex patterns (en-dash, em-dash, hyphen)
MONTH_PATTERN = (
    r'(?:January|February|March|April|May|June|July|August|'
    r'September|October|November|December|'
    r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
)
DATE_RANGE_RE = re.compile(
    rf'({MONTH_PATTERN}\s+\d{{1,2}})\s*[\u2013\u2014-]+\s*'
    rf'(?:({MONTH_PATTERN})\s+)?(\d{{1,2}})[,\s]+(\d{{4}})',
    re.IGNORECASE
)


class WheelockScraper(BaseScraper):
    """Scrapes shows from wheelockfamilytheatre.org/performances/now-playing/

    The page uses .mk-text-block divs but layout is inconsistent —
    titles and dates may be in separate blocks. We use a two-pass approach:
    1. Find all h3 titles
    2. Find all date strings anywhere on the page
    3. Match them by DOM proximity
    """

    THEATER_NAME = "Wheelock Family Theatre"
    BASE_URL = "https://www.wheelockfamilytheatre.org/performances/now-playing/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        # Strategy: find blocks that contain BOTH an h3 title and date in siblings
        # AND blocks where title and date are in the same block text
        text_blocks = soup.find_all(class_=re.compile(r'mk-text-block'))

        if not text_blocks:
            return shows

        # First pass: find blocks with h3 + date (in same block or next block by index)
        seen_titles = set()
        for idx, block in enumerate(text_blocks):
            h3 = block.find('h3')
            if not h3:
                continue
            title = clean_text(h3.get_text())
            if not title or len(title) < 3:
                # Handle empty h3 followed by another h3 in same block
                next_h3 = h3.find_next_sibling('h3')
                if next_h3:
                    title = clean_text(next_h3.get_text())
                    h3 = next_h3
                if not title or len(title) < 3:
                    continue

            skip_exact = ['learn more', 'sign up', 'subscribe', 'donate',
                         'about us', 'contact us', 'updates',
                         'now playing', 'sign up for wheelock']
            title_lower = title.lower()
            if any(title_lower == kw or title_lower.startswith(kw + ' ') for kw in skip_exact):
                continue
            if 'experience the transformative' in title_lower:
                continue

            # Look for date in the block's own text
            block_text = block.get_text()
            date_text = self._extract_date(block_text)

            # If not in same block, check the next block(s) by list index
            if not date_text:
                for lookahead in range(1, 3):
                    if idx + lookahead < len(text_blocks):
                        next_text = text_blocks[idx + lookahead].get_text()
                        date_text = self._extract_date(next_text)
                        if date_text:
                            break

            # Also check sibling elements within this block
            if not date_text:
                for sib in h3.find_next_siblings():
                    if sib.name == 'h3':
                        break
                    text = sib.get_text().strip()
                    date_text = self._extract_date(text)
                    if date_text:
                        break

            if not date_text:
                continue

            try:
                start_date, end_date = parse_date_range(date_text)
            except (ValueError, TypeError):
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            # Description — look in subsequent blocks/siblings
            description = self._find_description(block, h3)

            # Links
            show_url = ""
            ticket_url = ""
            for a in block.find_all('a', href=True):
                href = a['href']
                text = a.get_text().lower()
                if 'ovationtix' in href or 'ticket' in text or 'purchase' in text:
                    ticket_url = self.resolve_url(href)
                elif 'wheelock' in href:
                    show_url = self.resolve_url(href)

            shows.append(self._make_show(
                title=title,
                start_date=start_date,
                end_date=end_date,
                show_url=show_url or self.BASE_URL,
                description=description,
                ticket_url=ticket_url,
            ))

        # Second pass: find blocks without h3 that have both title-like text and dates
        # These are the season preview blocks (Charlotte's Web, etc.)
        for block in text_blocks:
            if block.find('h3'):
                continue  # Already handled
            block_text = block.get_text().strip()
            if not block_text or len(block_text) < 10:
                continue

            # Check if block has a date
            date_text = self._extract_date(block_text)
            if not date_text:
                continue

            # First line is likely the title
            lines = [l.strip() for l in block_text.split('\n') if l.strip()]
            if not lines:
                continue

            title = lines[0]
            # Skip if the first line IS the date
            if DATE_RANGE_RE.search(title):
                continue
            # Skip if title is too short or a common non-title
            if len(title) < 3 or title.lower() in ('now playing', ''):
                continue

            if title in seen_titles:
                continue

            try:
                start_date, end_date = parse_date_range(date_text)
            except (ValueError, TypeError):
                continue

            seen_titles.add(title)
            shows.append(self._make_show(
                title=title,
                start_date=start_date,
                end_date=end_date,
                show_url=self.BASE_URL,
            ))

        return shows

    def _extract_date(self, text):
        """Extract a date range string from text using regex."""
        if not text:
            return None
        match = DATE_RANGE_RE.search(text)
        if match:
            return clean_text(match.group(0))
        return None

    def _find_description(self, block, h3):
        """Find description text after the date in siblings."""
        month_pattern = MONTH_PATTERN
        for sib in h3.find_next_siblings():
            if sib.name == 'h3':
                break
            text = sib.get_text().strip()
            # Skip the date block and short text
            if text and len(text) > 40 and not re.search(month_pattern, text[:30], re.IGNORECASE):
                return truncate_description(text)

        # Check next mk-text-block siblings
        next_blocks = block.find_next_siblings(class_=re.compile(r'mk-text-block'), limit=3)
        for nb in next_blocks:
            if nb.find('h3'):
                break
            text = nb.get_text().strip()
            if text and len(text) > 40 and not re.search(month_pattern, text[:30], re.IGNORECASE):
                return truncate_description(text)

        return ""
