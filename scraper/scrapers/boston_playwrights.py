"""Scraper for Boston Playwrights' Theatre."""

import logging
import re
from datetime import date

from scraper.base_scraper import BaseScraper
from scraper.models import Show
from scraper.utils import parse_date_range, clean_text, truncate_description

logger = logging.getLogger(__name__)


class BostonPlaywrightsScraper(BaseScraper):
    """Scrapes shows from bostonplaywrights.org

    Dynamically discovers the current season URL from the homepage navigation,
    then parses the season page for shows. Falls back to a constructed URL
    based on the academic year pattern (/our-YY-YY-season).
    """

    THEATER_NAME = "Boston Playwrights' Theatre"
    BASE_URL = "https://www.bostonplaywrights.org"

    def scrape(self) -> list[Show]:
        season_url = self._get_season_url()
        logger.debug(f"Using season URL: {season_url}")
        soup = self.fetch_page(season_url)
        shows = []
        seen_titles = set()

        # Shows are typically in sections with h4 titles on Squarespace
        sections = self._find_show_sections(soup)

        for section in sections:
            try:
                show = self._parse_section(section)
                if show and show.is_valid():
                    key = show.title.lower().strip()
                    if key not in seen_titles:
                        seen_titles.add(key)
                        shows.append(show)
            except Exception as e:
                logger.debug(f"Failed to parse section: {e}")
                continue

        return shows

    def _get_season_url(self):
        """Discover the current season URL from the homepage navigation."""
        try:
            homepage = self.fetch_page(self.BASE_URL)
            # Look for a nav link containing "season" in href
            for a in homepage.find_all('a', href=True):
                href = a['href']
                text = a.get_text().lower()
                if 'season' in href and 'past' not in href and 'our' in text:
                    url = self.resolve_url(href)
                    logger.info(f"Discovered season page: {url}")
                    return url
        except Exception as e:
            logger.warning(f"Failed to discover season URL from homepage: {e}")

        # Fallback: construct URL from current academic year
        today = date.today()
        if today.month >= 9:
            start_year = today.year % 100
            end_year = (today.year + 1) % 100
        else:
            start_year = (today.year - 1) % 100
            end_year = today.year % 100
        fallback = f"{self.BASE_URL}/our-{start_year}-{end_year:02d}-season"
        logger.info(f"Using constructed season URL: {fallback}")
        return fallback

    def _find_show_sections(self, soup):
        """Find show sections — each show is a distinct block with heading."""
        sections = []

        # Try to find explicit section containers
        blocks = soup.select(
            '.sqs-block-content, .show-block, article, '
            'section, [class*="content-block"]'
        )

        if blocks:
            # Filter to blocks that contain a heading and date-like text
            for block in blocks:
                heading = block.find(['h2', 'h3', 'h4'])
                if heading and self._has_date_text(block):
                    sections.append(block)
        else:
            # Fallback: group content by h4 headings
            for heading in soup.find_all(['h4', 'h3', 'h2']):
                text = heading.get_text().strip()
                if text and len(text) > 2 and not self._is_navigation(text):
                    # Collect siblings until next heading
                    section_content = self._collect_section(heading)
                    if section_content:
                        sections.append(section_content)

        return sections

    def _collect_section(self, heading):
        """Collect heading and subsequent siblings as a virtual section."""
        from bs4 import Tag, BeautifulSoup

        # Create a container with the heading and following elements
        parts = [str(heading)]
        for sibling in heading.find_next_siblings():
            if sibling.name in ['h2', 'h3', 'h4']:
                break
            parts.append(str(sibling))
            if len(parts) > 20:  # Safety limit
                break

        html = ''.join(parts)
        return BeautifulSoup(html, 'lxml')

    def _parse_section(self, section):
        """Parse a show section."""
        # Title
        title_elem = section.find(['h4', 'h3', 'h2'])
        if not title_elem:
            return None

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            return None

        # Skip non-show headings and generic labels
        if self._is_navigation(title) or title.lower() in ('description', 'details', 'synopsis'):
            return None

        # Date range
        date_text = self._find_date_text(section)
        if not date_text:
            return None

        try:
            start_date, end_date = parse_date_range(date_text)
        except (ValueError, TypeError):
            return None

        # URL — look for OvationTix link or internal link
        show_url = self.BASE_URL
        ticket_url = ""
        for a in section.find_all('a'):
            href = a.get('href', '')
            text = a.get_text().lower()
            if 'ovationtix' in href or 'ticket' in text:
                ticket_url = href
            elif 'bostonplaywrights' in href:
                show_url = href

        # Image
        img = section.find('img')
        image_url = ""
        if img:
            src = img.get('src') or img.get('data-src')
            if src:
                image_url = self.resolve_url(src)

        # Description — first substantive paragraph
        description = ""
        for p in section.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 40 and not self._is_date_like(text):
                description = truncate_description(text)
                break

        return self._make_show(
            title=title,
            start_date=start_date,
            end_date=end_date,
            show_url=show_url,
            description=description,
            image_url=image_url,
            ticket_url=ticket_url,
        )

    def _find_date_text(self, section):
        """Find date-like text in a section."""
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

        for elem in section.find_all(['p', 'span', 'div', 'strong', 'em', 'h5', 'h6']):
            text = elem.get_text().strip()
            if re.search(month_pattern, text, re.IGNORECASE) and re.search(r'\d', text):
                if len(text) < 100:
                    # Extract just the date portion
                    date_match = re.search(
                        rf'({month_pattern}\s+\d{{1,2}})\s*[-–—]\s*({month_pattern}\s+\d{{1,2}}[,\s]*\d{{4}}|\d{{1,2}}[,\s]*\d{{4}})',
                        text, re.IGNORECASE
                    )
                    if date_match:
                        return date_match.group(0)
                    # Simpler patterns
                    simple_match = re.search(
                        rf'{month_pattern}\s+\d{{1,2}}.*?\d{{4}}',
                        text, re.IGNORECASE
                    )
                    if simple_match:
                        return clean_text(simple_match.group(0))
                    if len(text) < 60:
                        return clean_text(text)

        return None

    def _has_date_text(self, block):
        """Check if a block contains date-like text."""
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        text = block.get_text()
        return bool(re.search(month_pattern, text, re.IGNORECASE))

    def _is_navigation(self, text):
        """Check if text is likely a navigation element rather than a show title."""
        nav_keywords = ['season', 'subscribe', 'donate', 'about', 'contact',
                       'menu', 'home', 'news', 'gallery', 'board']
        return text.lower().strip() in nav_keywords

    def _is_date_like(self, text):
        month_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        return bool(re.search(month_pattern, text, re.IGNORECASE)) and len(text) < 60
