"""Data models for the show scraper."""

from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Show:
    """Represents a single theater show with all relevant metadata."""

    title: str
    theater_name: str
    start_date: str  # ISO format YYYY-MM-DD
    end_date: str  # ISO format YYYY-MM-DD
    show_url: str
    description: str = ""
    image_url: str = ""
    ticket_url: str = ""

    def validate(self) -> list[str]:
        """Validate required fields and date formats. Returns list of error messages."""
        errors = []

        if not self.title or not self.title.strip():
            errors.append("title is required")
        if not self.theater_name or not self.theater_name.strip():
            errors.append("theater_name is required")
        if not self.show_url or not self.show_url.strip():
            errors.append("show_url is required")

        for date_field in ("start_date", "end_date"):
            value = getattr(self, date_field)
            if not value:
                errors.append(f"{date_field} is required")
            else:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"{date_field} must be YYYY-MM-DD format, got '{value}'")

        if self.start_date and self.end_date:
            try:
                start = datetime.strptime(self.start_date, "%Y-%m-%d")
                end = datetime.strptime(self.end_date, "%Y-%m-%d")
                if end < start:
                    errors.append("end_date cannot be before start_date")
            except ValueError:
                pass  # Already caught above

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScraperStatus:
    """Records the outcome of a single scraper run."""

    theater_name: str
    url: str
    success: bool
    shows_found: int
    timestamp: str  # ISO datetime
    error_message: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)
