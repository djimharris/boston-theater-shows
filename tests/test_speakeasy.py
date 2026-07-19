"""Tests for the SpeakEasy Stage scraper."""

import pytest
import responses
from scraper.scrapers.speakeasy import SpeakeasyScraper


SAMPLE_HTML = """
<html>
<body>
<div class="shows-list">
    <article class="show-item">
        <img data-src="https://speakeasystage.com/images/cabaret.jpg" alt="Cabaret">
        <h3><a href="/shows/2026/09/cabaret/">Cabaret</a></h3>
        <p class="dates">September 5 - October 4, 2026</p>
        <p>The Tony-winning musical set in a Berlin nightclub during the rise of Nazism.</p>
        <a href="https://tickets.speakeasystage.com/cabaret" class="buy-tickets">Buy Tickets</a>
    </article>
    <article class="show-item">
        <img src="https://speakeasystage.com/images/fun-home.jpg" alt="Fun Home">
        <h3><a href="/shows/2026/11/fun-home/">Fun Home</a></h3>
        <p class="dates">November 14 - December 12, 2026</p>
        <p>A groundbreaking musical based on Alison Bechdel's graphic memoir.</p>
        <a href="https://tickets.speakeasystage.com/fun-home" class="buy-tickets">Buy Tickets</a>
    </article>
</div>
</body>
</html>
"""


class TestSpeakeasyScraper:
    @responses.activate
    def test_scrape_returns_shows(self):
        responses.add(
            responses.GET,
            "https://speakeasystage.com/shows/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = SpeakeasyScraper()
        shows = scraper.scrape()

        assert len(shows) == 2

    @responses.activate
    def test_show_fields_populated(self):
        responses.add(
            responses.GET,
            "https://speakeasystage.com/shows/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = SpeakeasyScraper()
        shows = scraper.scrape()
        show = shows[0]

        assert show.title == "Cabaret"
        assert show.theater_name == "SpeakEasy Stage Company"
        assert show.start_date == "2026-09-05"
        assert show.end_date == "2026-10-04"
        assert "/cabaret/" in show.show_url

    @responses.activate
    def test_lazy_loaded_images(self):
        """Images with data-src (lazy loading) should be captured."""
        responses.add(
            responses.GET,
            "https://speakeasystage.com/shows/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = SpeakeasyScraper()
        shows = scraper.scrape()

        assert "cabaret.jpg" in shows[0].image_url

    @responses.activate
    def test_all_shows_valid(self):
        responses.add(
            responses.GET,
            "https://speakeasystage.com/shows/",
            body=SAMPLE_HTML,
            status=200,
        )

        scraper = SpeakeasyScraper()
        shows = scraper.scrape()

        for show in shows:
            assert show.is_valid()

    @responses.activate
    def test_skips_non_show_headings(self):
        html = """
        <html><body>
        <article>
            <h3>Subscribe Now</h3>
            <p>Get your season pass today</p>
        </article>
        <article>
            <h3><a href="/shows/2026/09/real-show/">Real Show</a></h3>
            <p>October 1 - 30, 2026</p>
            <p>A real theater production.</p>
        </article>
        </body></html>
        """
        responses.add(
            responses.GET,
            "https://speakeasystage.com/shows/",
            body=html,
            status=200,
        )

        scraper = SpeakeasyScraper()
        shows = scraper.scrape()

        # "Subscribe Now" should be skipped
        assert all("subscribe" not in s.title.lower() for s in shows)
