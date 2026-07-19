# Architecture

## Overview

The Boston Theater Show Aggregator is a static web application with a Python-based scraping backend. It follows a clear separation between data collection (Python) and presentation (HTML/CSS/JS).

```
┌──────────────────────────────┐     ┌──────────────────────────────┐
│   GitHub Actions (Cron)       │     │   GitHub Pages (Static)       │
│                               │     │                               │
│   Python Scrapers             │     │   Vanilla HTML/CSS/JS         │
│         │                     │     │         │                     │
│   data/shows.json  ───────────┼─────┼──> fetch('./data/shows.json') │
│   data/status.json ───────────┼─────┼──> fetch('./data/status.json')│
│                               │     │                               │
└──────────────────────────────┘     └──────────────────────────────┘
```

## Directory Structure

```
showscraper/
├── .github/workflows/scrape.yml   # CI/CD pipeline
├── scraper/                       # Python backend
│   ├── main.py                    # Entry point
│   ├── models.py                  # Data classes (Show, ScraperStatus)
│   ├── orchestrator.py            # Runs all scrapers
│   ├── base_scraper.py            # Abstract base class
│   ├── utils.py                   # Shared utilities
│   └── scrapers/                  # One file per theater
│       ├── __init__.py            # Scraper registry
│       └── *.py                   # Individual scrapers
├── frontend/                      # Static frontend
│   ├── index.html                 # Single-page shell
│   ├── css/styles.css             # All styles
│   └── js/                        # Modular JavaScript
├── data/                          # Generated output (committed by CI)
├── tests/                         # Unit tests
└── requirements.txt               # Python dependencies
```

## Backend Architecture

### Class Hierarchy

```
BaseScraper (abstract)
├── THEATER_NAME, BASE_URL (class constants)
├── fetch_page(url) → BeautifulSoup
├── resolve_url(relative) → absolute URL
├── _make_show(...) → Show
└── abstract scrape() → list[Show]

HuntingtonScraper(BaseScraper)
LyricStageScraper(BaseScraper)
BostonTheatreSceneScraper(BaseScraper)  # handles pagination
EmersonScraper(BaseScraper)              # Tribe Events plugin
CentralSquareScraper(BaseScraper)        # two-step (list → detail)
SpeakeasyScraper(BaseScraper)
BostonPlaywrightsScraper(BaseScraper)
ARTScraper(BaseScraper)
ApollinaireScraper(BaseScraper)
WheelockScraper(BaseScraper)
FootlightScraper(BaseScraper)            # two-step (list → detail)
```

### Data Flow

1. `main.py` imports `ALL_SCRAPERS` from the registry
2. `ScraperOrchestrator` instantiates each scraper class
3. Each scraper's `scrape()` is called in sequence (within try/except)
4. Results are validated and serialized to JSON
5. Output is written to `data/shows.json` and `data/status.json`

### Key Design Decisions

- **Sequential execution**: Simpler than async; total time ~30-60s is fine for daily cron
- **Error isolation**: One scraper failure doesn't stop others
- **Retry logic**: 3 attempts with exponential backoff per HTTP request
- **Politeness**: 1-second delay between requests to the same site
- **Validation**: Shows must pass validation before inclusion in output

### Adding a New Scraper

```python
# scraper/scrapers/new_theater.py
from scraper.base_scraper import BaseScraper
from scraper.models import Show

class NewTheaterScraper(BaseScraper):
    THEATER_NAME = "New Theater"
    BASE_URL = "https://newtheater.org/shows/"

    def scrape(self) -> list[Show]:
        soup = self.fetch_page(self.BASE_URL)
        shows = []
        # Parse HTML and create Show objects
        for card in soup.select('.show-card'):
            # ... extraction logic ...
            shows.append(self._make_show(...))
        return shows
```

Then add to `scraper/scrapers/__init__.py`:
```python
from scraper.scrapers.new_theater import NewTheaterScraper
ALL_SCRAPERS = [..., NewTheaterScraper]
```

## Frontend Architecture

### Module Responsibilities

| Module | Role |
|--------|------|
| `app.js` | State management, data fetching, view coordination |
| `filters.js` | Date range and theater filtering logic |
| `cardView.js` | Card grid DOM generation |
| `calendarView.js` | Gantt-style calendar rendering |
| `status.js` | Status bar and per-site status table |

### State Management

```javascript
App.state = {
    shows: [],           // All shows from JSON
    filteredShows: [],   // After applying filters
    currentView: 'card', // 'card' or 'calendar'
    status: null,        // Status metadata
    filters: {
        startDate: '',
        endDate: '',
        theaters: []
    }
}
```

### Data Flow

1. `app.js` fetches both JSON files on page load
2. Default filters are applied (today → end of next month)
3. Active view is rendered with filtered data
4. Filter changes trigger re-filter + re-render

### Responsive Design

- **Desktop (≥768px)**: Multi-column card grid, full calendar
- **Mobile (<768px)**: Single-column cards, horizontally scrollable calendar
- CSS Grid with `auto-fill` and `minmax()` for fluid responsiveness

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
schedule: '0 10 * * *'  # 6 AM ET daily

Jobs:
1. scrape:
   - Checkout → Python setup → Install deps → Run scraper → Commit data → Push
2. deploy (depends on scrape):
   - Checkout → Copy data/ into frontend/ → Deploy to GitHub Pages
```

### Deployment Strategy

- The `frontend/` directory is the deployable artifact
- `data/` is copied into `frontend/data/` at deploy time
- GitHub Pages serves `frontend/` as the site root
- `workflow_dispatch` allows manual re-runs

## Data Schemas

### shows.json

```json
{
  "generated_at": "ISO datetime",
  "total_shows": 42,
  "shows": [{
    "title": "string (required)",
    "theater_name": "string (required)",
    "start_date": "YYYY-MM-DD (required)",
    "end_date": "YYYY-MM-DD (required)",
    "show_url": "URL (required)",
    "description": "string (optional, max 200 chars)",
    "image_url": "URL (optional)",
    "ticket_url": "URL (optional)"
  }]
}
```

### status.json

```json
{
  "last_run": "ISO datetime",
  "total_sites": 11,
  "successful": 10,
  "failed": 1,
  "deferred_sites": [{ "name": "", "url": "", "reason": "" }],
  "sites": [{
    "theater_name": "",
    "url": "",
    "success": true,
    "shows_found": 4,
    "timestamp": "",
    "duration_seconds": 1.2,
    "error_message": ""
  }]
}
```

## Testing Strategy

- **Unit tests per scraper**: Mock HTML → verify parsed Show objects
- **Model tests**: Validation, serialization
- **Utility tests**: Date parsing (the hardest component)
- **Orchestrator tests**: Error isolation, output structure
- **Library**: pytest + responses (HTTP mocking)
- **Fixture approach**: Representative HTML snippets in `tests/fixtures/`
