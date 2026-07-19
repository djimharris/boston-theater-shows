"""Tests for utility functions, especially date parsing."""

import pytest
from scraper.utils import parse_date_range, resolve_url, clean_text, truncate_description


class TestParseDateRange:
    """Test the various date formats encountered across theater sites."""

    def test_full_date_range(self):
        start, end = parse_date_range("September 10 - October 11, 2026")
        assert start == "2026-09-10"
        assert end == "2026-10-11"

    def test_same_month_range(self):
        start, end = parse_date_range("November 5 - 22, 2026")
        assert start == "2026-11-05"
        assert end == "2026-11-22"

    def test_en_dash_separator(self):
        start, end = parse_date_range("Sep 10 \u2013 Oct 11, 2026")
        assert start == "2026-09-10"
        assert end == "2026-10-11"

    def test_em_dash_separator(self):
        start, end = parse_date_range("Sep 10 \u2014 Oct 11, 2026")
        assert start == "2026-09-10"
        assert end == "2026-10-11"

    def test_single_date(self):
        start, end = parse_date_range("October 7, 2026")
        assert start == "2026-10-07"
        assert end == "2026-10-07"

    def test_date_with_time_stripped(self):
        start, end = parse_date_range("October 7, 2026 at 8:00 pm")
        assert start == "2026-10-07"
        assert end == "2026-10-07"

    def test_abbreviated_months(self):
        start, end = parse_date_range("Jan 15 - Feb 20, 2026")
        assert start == "2026-01-15"
        assert end == "2026-02-20"

    def test_no_year_uses_reference(self):
        start, end = parse_date_range("March 5 - April 10", reference_year=2027)
        assert start == "2027-03-05"
        assert end == "2027-04-10"

    def test_through_separator(self):
        start, end = parse_date_range("January 10 through February 5, 2026")
        assert start == "2026-01-10"
        assert end == "2026-02-05"

    def test_cross_year_range(self):
        """A range like Dec 2026 - Jan 2027."""
        start, end = parse_date_range("December 15, 2026 - January 10, 2027")
        assert start == "2026-12-15"
        assert end == "2027-01-10"

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            parse_date_range("not a date at all")

    def test_whitespace_handling(self):
        start, end = parse_date_range("  September 10  -  October 11, 2026  ")
        assert start == "2026-09-10"
        assert end == "2026-10-11"

    def test_day_of_week_prefix_stripped(self):
        start, end = parse_date_range("Friday, October 7, 2026")
        assert start == "2026-10-07"
        assert end == "2026-10-07"


class TestResolveUrl:
    def test_absolute_url_unchanged(self):
        result = resolve_url("https://base.com/", "https://other.com/page")
        assert result == "https://other.com/page"

    def test_relative_url_resolved(self):
        result = resolve_url("https://base.com/path/", "/shows/my-show")
        assert result == "https://base.com/shows/my-show"

    def test_relative_path(self):
        result = resolve_url("https://base.com/path/page", "other-page")
        assert result == "https://base.com/path/other-page"

    def test_protocol_relative(self):
        result = resolve_url("https://base.com/", "//cdn.example.com/img.jpg")
        assert result == "https://cdn.example.com/img.jpg"

    def test_empty_url_returns_empty(self):
        result = resolve_url("https://base.com/", "")
        assert result == ""

    def test_none_url_returns_empty(self):
        result = resolve_url("https://base.com/", None)
        assert result == ""


class TestCleanText:
    def test_collapses_whitespace(self):
        assert clean_text("hello   world") == "hello world"

    def test_strips_leading_trailing(self):
        assert clean_text("  hello  ") == "hello"

    def test_handles_newlines(self):
        assert clean_text("line1\n  line2\n") == "line1 line2"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_none_returns_empty(self):
        assert clean_text(None) == ""


class TestTruncateDescription:
    def test_short_text_unchanged(self):
        text = "A short description."
        assert truncate_description(text, 200) == text

    def test_long_text_truncated_at_word(self):
        text = "This is a " + "very " * 50 + "long description."
        result = truncate_description(text, 50)
        assert len(result) <= 55  # Allow for "..."
        assert result.endswith("...")

    def test_respects_max_length(self):
        text = "word " * 100
        result = truncate_description(text, 30)
        # Should be at or near 30 chars (word boundary + ...)
        assert len(result) <= 35

    def test_empty_string(self):
        assert truncate_description("") == ""

    def test_exact_length_unchanged(self):
        text = "x" * 200
        result = truncate_description(text, 200)
        assert result == text
