"""Tests for the ScraperOrchestrator."""

import pytest
from unittest.mock import patch, MagicMock

from scraper.orchestrator import ScraperOrchestrator
from scraper.base_scraper import BaseScraper
from scraper.models import Show


class MockSuccessScraper(BaseScraper):
    THEATER_NAME = "Success Theater"
    BASE_URL = "https://success.example.com"

    def scrape(self):
        return [
            Show(
                title="Good Show",
                theater_name=self.THEATER_NAME,
                start_date="2026-09-01",
                end_date="2026-09-30",
                show_url="https://success.example.com/show",
            )
        ]


class MockFailScraper(BaseScraper):
    THEATER_NAME = "Fail Theater"
    BASE_URL = "https://fail.example.com"

    def scrape(self):
        raise ConnectionError("Connection refused")


class MockMultiShowScraper(BaseScraper):
    THEATER_NAME = "Multi Theater"
    BASE_URL = "https://multi.example.com"

    def scrape(self):
        return [
            Show(
                title=f"Show {i}",
                theater_name=self.THEATER_NAME,
                start_date="2026-09-01",
                end_date="2026-09-30",
                show_url=f"https://multi.example.com/show-{i}",
            )
            for i in range(3)
        ]


class MockInvalidShowScraper(BaseScraper):
    THEATER_NAME = "Invalid Theater"
    BASE_URL = "https://invalid.example.com"

    def scrape(self):
        return [
            Show(
                title="",  # Invalid: empty title
                theater_name=self.THEATER_NAME,
                start_date="2026-09-01",
                end_date="2026-09-30",
                show_url="https://invalid.example.com/show",
            ),
            Show(
                title="Valid Show",
                theater_name=self.THEATER_NAME,
                start_date="2026-09-01",
                end_date="2026-09-30",
                show_url="https://invalid.example.com/valid",
            ),
        ]


class TestScraperOrchestrator:
    def test_run_all_success(self):
        orchestrator = ScraperOrchestrator([MockSuccessScraper])
        shows, statuses = orchestrator.run_all()

        assert len(shows) == 1
        assert shows[0].title == "Good Show"
        assert len(statuses) == 1
        assert statuses[0].success is True
        assert statuses[0].shows_found == 1

    def test_one_failure_doesnt_stop_others(self):
        orchestrator = ScraperOrchestrator([
            MockFailScraper, MockSuccessScraper
        ])
        shows, statuses = orchestrator.run_all()

        assert len(shows) == 1  # Only from success scraper
        assert len(statuses) == 2
        assert statuses[0].success is False
        assert "ConnectionError" in statuses[0].error_message
        assert statuses[1].success is True

    def test_multiple_scrapers(self):
        orchestrator = ScraperOrchestrator([
            MockSuccessScraper, MockMultiShowScraper
        ])
        shows, statuses = orchestrator.run_all()

        assert len(shows) == 4  # 1 + 3
        assert all(s.success for s in statuses)

    def test_invalid_shows_filtered(self):
        orchestrator = ScraperOrchestrator([MockInvalidShowScraper])
        shows, statuses = orchestrator.run_all()

        assert len(shows) == 1  # Only the valid one
        assert shows[0].title == "Valid Show"
        assert statuses[0].shows_found == 1

    def test_status_records_timing(self):
        orchestrator = ScraperOrchestrator([MockSuccessScraper])
        shows, statuses = orchestrator.run_all()

        assert statuses[0].duration_seconds >= 0

    def test_to_shows_json_structure(self):
        orchestrator = ScraperOrchestrator([MockSuccessScraper])
        orchestrator.run_all()
        result = orchestrator.to_shows_json()

        assert "generated_at" in result
        assert result["total_shows"] == 1
        assert "shows" in result
        assert result["shows"][0]["title"] == "Good Show"

    def test_to_status_json_structure(self):
        orchestrator = ScraperOrchestrator([MockSuccessScraper, MockFailScraper])
        orchestrator.run_all()
        result = orchestrator.to_status_json()

        assert "last_run" in result
        assert result["total_sites"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert "deferred_sites" in result
        assert len(result["deferred_sites"]) == 2
        assert "sites" in result

    def test_empty_scraper_list(self):
        orchestrator = ScraperOrchestrator([])
        shows, statuses = orchestrator.run_all()

        assert shows == []
        assert statuses == []

    def test_all_scrapers_fail(self):
        orchestrator = ScraperOrchestrator([MockFailScraper, MockFailScraper])
        shows, statuses = orchestrator.run_all()

        assert len(shows) == 0
        assert all(not s.success for s in statuses)
