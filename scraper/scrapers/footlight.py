"""Scraper for Footlight Club (two-step: list page + blog detail pages)."""

import logging
import re

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class FootlightScraper(BaseScraper):
    """Scrapes shows from footlight.org/shows

    Squarespace-based site with a list page linking to blog-style detail
    pages for each show. The list page has titles and date ranges.
    Detail pages have full descriptions.
    """

    THEATER_NAME = "Footlight Club"
    BASE_URL = "https://www.footlight.org/shows"
    MAX_DETAIL_PAGES = 10

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []

        # Find show entries on the listing page
        entries = self._find_entries(soup)
        detail_count = 0

        for entry in entries:
            try:
                title, date_text, detail_url = self._parse_entry(entry)
                if not title or not date_text:
                    continue

                try:
                    start_date, end_date = parse_date_range(date_text)
                except (ValueError, TypeError):
                    continue

                # Optionally fetch detail page
                description = ""
                image_url = ""
                if detail_url and detail_count < self.MAX_DETAIL_PAGES:
                    description, image_url = self._fetch_detail(detail_url)
                    detail_count += 1

                show = self._make_show(
                    title=title,
                    start_date=start_date,
                    end_date=end_date,
                    show_url=detail_url or self.BASE_URL,
                    description=description,
                    image_url=image_url,
                )
                if show.is_valid():
                    shows.append(show)

            except Exception as e:
                logger.debug(f"Failed to parse entry: {e}")
                continue

        return shows

    def _find_entries(self, soup):
        """Find show entries on the listing page."""
        # Squarespace blog list patterns
        entries = soup.select(
            '.blog-item, .summary-item, article, '
            '[class*="blog-entry"], [class*="summary-content"], '
            '.list-item, .collection-item'
        )

        if not entries:
            # Fallback: look for link blocks that contain show info
            entries = []
            for link_block in soup.find_all('a', href=True):
                text = link_block.get_text().strip()
                href = link_block.get('href', '')
                # Show links typically go to blog posts
                if '/blog/' in href or '/shows/' in href:
                    parent = link_block.parent
                    if parent and parent not in entries:
                        entries.append(parent)

        return entries

    def _parse_entry(self, entry):
        """Parse a list entry for title, date, and detail URL."""
        # Title — from heading or strong link text
        title_elem = entry.find(['h2', 'h3', 'h4'])
        title = ""
        if title_elem:
            title = clean_text(title_elem.get_text())
        else:
            # Try the first significant link text
            for a in entry.find_all('a'):
                text = a.get_text().strip()
                if text and len(text) > 3 and text.lower() not in ('read more', 'more'):
                    title = clean_text(text)
                    break

        if not title:
            return None, None, None

        # Detail URL
        detail_url = ""
        for a in entry.find_all('a'):
            href = a.get('href', '')
            if href and href != '#' and '/blog/' in href or '/shows/' in href:
                detail_url = self.resolve_url(href)
                break
        if not detail_url:
            link = entry.find('a', href=True)
            if link:
                detail_url = self.resolve_url(link['href'])

        # Date text
        date_text = self._find_date_text(entry)

        return title, date_text, detail_url

    def _find_date_text(self, entry):
        """Find date text in an entry."""
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

        for elem in entry.find_all(['p', 'span', 'div', 'time', 'em', 'strong']):
            text = elem.get_text().strip()
            if re.search(month_pattern, text, re.IGNORECASE) and re.search(r'\d', text):
                if len(text) < 80:
                    return clean_text(text)

        # Check the full entry text as last resort
        full_text = entry.get_text()
        match = re.search(
            rf'({month_pattern}\s+\d{{1,2}})\s*[-–]\s*(\d{{1,2}}[,\s]*\d{{4}})',
            full_text, re.IGNORECASE
        )
        if match:
            return match.group(0)

        return None

    def _fetch_detail(self, url):
        """Fetch a detail page for description and image."""
        try:
            soup = self.fetch_page(url)

            # Description
            description = ""
            # Squarespace blog content
            content = soup.find(class_=re.compile(r'blog-item-content|entry-content|sqs-block-content', re.IGNORECASE))
            if content:
                for p in content.find_all('p'):
                    text = p.get_text().strip()
                    if text and len(text) > 40:
                        description = truncate_description(text)
                        break
            if not description:
                for p in soup.find_all('p'):
                    text = p.get_text().strip()
                    if text and len(text) > 50:
                        description = truncate_description(text)
                        break

            # Image
            image_url = ""
            # Look for main content image
            img = soup.find('img', class_=re.compile(r'featured|blog|content', re.IGNORECASE))
            if not img:
                content_area = soup.find(class_=re.compile(r'content|entry|blog', re.IGNORECASE))
                if content_area:
                    img = content_area.find('img')
            if img:
                src = img.get('src') or img.get('data-src')
                if src and 'logo' not in src.lower():
                    image_url = self.resolve_url(src)

            return description, image_url

        except Exception as e:
            logger.debug(f"Failed to fetch detail page {url}: {e}")
            return "", ""
