"""Tests for the Show and ScraperStatus data models."""

import pytest
from scraper.models import Show, ScraperStatus


class TestShow:
    def test_valid_show(self):
        show = Show(
            title="Hamilton",
            theater_name="Huntington Theatre",
            start_date="2026-09-01",
            end_date="2026-09-30",
            show_url="https://example.com/hamilton",
        )
        assert show.is_valid()
        assert show.validate() == []

    def test_missing_title(self):
        show = Show(
            title="",
            theater_name="Theater",
            start_date="2026-09-01",
            end_date="2026-09-30",
            show_url="https://example.com",
        )
        assert not show.is_valid()
        errors = show.validate()
        assert "title is required" in errors

    def test_missing_theater_name(self):
        show = Show(
            title="Show",
            theater_name="",
            start_date="2026-09-01",
            end_date="2026-09-30",
            show_url="https://example.com",
        )
        assert not show.is_valid()
        assert "theater_name is required" in show.validate()

    def test_missing_dates(self):
        show = Show(
            title="Show",
            theater_name="Theater",
            start_date="",
            end_date="",
            show_url="https://example.com",
        )
        errors = show.validate()
        assert "start_date is required" in errors
        assert "end_date is required" in errors

    def test_invalid_date_format(self):
        show = Show(
            title="Show",
            theater_name="Theater",
            start_date="September 10, 2026",
            end_date="2026-09-30",
            show_url="https://example.com",
        )
        errors = show.validate()
        assert any("start_date must be YYYY-MM-DD" in e for e in errors)

    def test_end_before_start(self):
        show = Show(
            title="Show",
            theater_name="Theater",
            start_date="2026-10-01",
            end_date="2026-09-01",
            show_url="https://example.com",
        )
        errors = show.validate()
        assert "end_date cannot be before start_date" in errors

    def test_missing_show_url(self):
        show = Show(
            title="Show",
            theater_name="Theater",
            start_date="2026-09-01",
            end_date="2026-09-30",
            show_url="",
        )
        errors = show.validate()
        assert "show_url is required" in errors

    def test_to_dict(self):
        show = Show(
            title="Hamilton",
            theater_name="Huntington Theatre",
            start_date="2026-09-01",
            end_date="2026-09-30",
            show_url="https://example.com/hamilton",
            description="A musical",
            image_url="https://example.com/img.jpg",
            ticket_url="https://tickets.example.com",
        )
        d = show.to_dict()
        assert d["title"] == "Hamilton"
        assert d["theater_name"] == "Huntington Theatre"
        assert d["start_date"] == "2026-09-01"
        assert d["end_date"] == "2026-09-30"
        assert d["show_url"] == "https://example.com/hamilton"
        assert d["description"] == "A musical"
        assert d["image_url"] == "https://example.com/img.jpg"
        assert d["ticket_url"] == "https://tickets.example.com"

    def test_optional_fields_default_empty(self):
        show = Show(
            title="Show",
            theater_name="Theater",
            start_date="2026-09-01",
            end_date="2026-09-30",
            show_url="https://example.com",
        )
        assert show.description == ""
        assert show.image_url == ""
        assert show.ticket_url == ""

    def test_same_start_end_date_valid(self):
        """Single-day shows should be valid."""
        show = Show(
            title="One Night Only",
            theater_name="Theater",
            start_date="2026-09-15",
            end_date="2026-09-15",
            show_url="https://example.com",
        )
        assert show.is_valid()


class TestScraperStatus:
    def test_success_status(self):
        status = ScraperStatus(
            theater_name="Huntington Theatre",
            url="https://example.com",
            success=True,
            shows_found=5,
            timestamp="2026-07-18T10:00:00Z",
            duration_seconds=1.5,
        )
        d = status.to_dict()
        assert d["success"] is True
        assert d["shows_found"] == 5
        assert d["error_message"] == ""

    def test_failure_status(self):
        status = ScraperStatus(
            theater_name="Failed Theater",
            url="https://example.com",
            success=False,
            shows_found=0,
            timestamp="2026-07-18T10:00:00Z",
            error_message="ConnectionError: timed out",
            duration_seconds=30.0,
        )
        d = status.to_dict()
        assert d["success"] is False
        assert d["error_message"] == "ConnectionError: timed out"
