"""Tests for the Huntington Theatre scraper."""

import pytest
import responses
from scraper.scrapers.huntington import HuntingtonScraper


SAMPLE_HTML = """
<html>
<body>
<div class="c-event-card">
    <img src="/media/images/purpose-hero.jpg" alt="Purpose">
    <h3 class="c-col-title">Purpose</h3>
    <a class="c-event-card__link" href="/whats-on/purpose/">Purpose</a>
    <p class="c-event-card__date">September 10 - October 11, 2026</p>
    <p class="c-event-card__description">A powerful new play exploring themes of identity and belonging.</p>
    <a class="c-book-btn" href="https://tickets.huntingtontheatre.org/purpose">Buy Tickets</a>
</div>
<div class="c-event-card">
    <img src="/media/images/garden-hero.jpg" alt="The Garden">
    <h3 class="c-col-title">The Garden</h3>
    <a class="c-event-card__link" href="/whats-on/the-garden/">The Garden</a>
    <p class="c-event-card__date">November 5 - December 20, 2026</p>
    <p class="c-event-card__description">A heartwarming story about community and growth.</p>
    <a class="c-book-btn" href="https://tickets.huntingtontheatre.org/garden">Buy Tickets</a>
</div>
</body>
</html>
"""


class TestHuntingtonScraper:
    @responses.activate
    def test_scrape_returns_shows(self):
        responses.add(
            responses.GET,
            "https://www.huntingtontheatre.org/plays-and-events/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = HuntingtonScraper()
        shows = scraper.scrape()

        assert len(shows) == 2

    @responses.activate
    def test_show_fields_populated(self):
        responses.add(
            responses.GET,
            "https://www.huntingtontheatre.org/plays-and-events/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = HuntingtonScraper()
        shows = scraper.scrape()
        show = shows[0]

        assert show.title == "Purpose"
        assert show.theater_name == "Huntington Theatre"
        assert show.start_date == "2026-09-10"
        assert show.end_date == "2026-10-11"
        assert "/whats-on/purpose/" in show.show_url
        assert show.description != ""
        assert show.image_url != ""

    @responses.activate
    def test_ticket_url_extracted(self):
        responses.add(
            responses.GET,
            "https://www.huntingtontheatre.org/plays-and-events/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = HuntingtonScraper()
        shows = scraper.scrape()

        assert "tickets.huntingtontheatre.org" in shows[0].ticket_url

    @responses.activate
    def test_all_shows_valid(self):
        responses.add(
            responses.GET,
            "https://www.huntingtontheatre.org/plays-and-events/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = HuntingtonScraper()
        shows = scraper.scrape()

        for show in shows:
            assert show.is_valid(), f"Show '{show.title}' is invalid: {show.validate()}"

    @responses.activate
    def test_handles_empty_page(self):
        responses.add(
            responses.GET,
            "https://www.huntingtontheatre.org/plays-and-events/",
            body="<html><body><p>No shows currently</p></body></html>",
            status=200,
        )

        scraper = HuntingtonScraper()
        shows = scraper.scrape()

        assert shows == []

    @responses.activate
    def test_handles_missing_dates(self):
        html = """
        <html><body>
        <article>
            <h3><a href="/shows/test/">Test Show</a></h3>
            <p>No dates listed here.</p>
        </article>
        </body></html>
        """
        responses.add(
            responses.GET,
            "https://www.huntingtontheatre.org/plays-and-events/",
            body=html,
            status=200,
        )

        scraper = HuntingtonScraper()
        shows = scraper.scrape()

        # Show without dates should be skipped
        assert shows == []
