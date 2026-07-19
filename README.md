# Boston Theater Show Aggregator

A web application that scrapes Boston-area theater websites daily and presents upcoming shows in a clean, filterable interface. View shows as cards or on a Gantt-style calendar.

## Live Site

Once deployed, your site will be available at: `https://<your-username>.github.io/<repo-name>/`

## Features

- **Card View**: Browse shows with images, descriptions, dates, and ticket links
- **Calendar View**: Gantt-style month view with color-coded bars per theater
- **Date Filtering**: Filter by date range (defaults to the next month)
- **Theater Filtering**: Show/hide specific theaters
- **Status Dashboard**: See which sites were successfully scraped
- **Mobile Friendly**: Responsive design works on phones and tablets
- **Daily Updates**: GitHub Actions scrapes all sites once per day

## Supported Theaters

| Theater | Website |
|---------|---------|
| Huntington Theatre | huntingtontheatre.org |
| Lyric Stage Company | lyricstage.com |
| Boston Theatre Scene | bostontheatrescene.com |
| Emerson Colonial Theatre | emersontheatres.org |
| Central Square Theater | centralsquaretheater.org |
| SpeakEasy Stage Company | speakeasystage.com |
| Boston Playwrights' Theatre | bostonplaywrights.org |
| American Repertory Theater | americanrepertorytheater.org |
| Apollinaire Theatre Company | apollinairetheatre.com |
| Wheelock Family Theatre | wheelockfamilytheatre.org |
| Footlight Club | footlight.org |

### Additional Venues (Manual Visit)

These sites require JavaScript rendering and are linked directly in the app:

- [Citizens Bank Opera House](https://www.citizensoperahouse.com/events/)
- [OvationTix Shows](https://ci.ovationtix.com/34432)

## Setup & Deployment

### Prerequisites

- A GitHub account
- Python 3.11+ (for local development/testing)

### Step 1: Create GitHub Repository

1. Create a new **public** repository on GitHub
2. Clone it locally or push this code to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Pages**
3. Under "Source", select **GitHub Actions**
4. Save

### Step 3: Run the Scraper

The scraper runs automatically every day at 6:00 AM ET. To trigger it manually:

1. Go to the **Actions** tab in your repository
2. Select "Scrape Boston Theater Shows" workflow
3. Click **Run workflow** > **Run workflow**
4. Wait for both jobs (scrape + deploy) to complete
5. Visit your Pages URL to see the site

### Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the scraper locally
python -m scraper.main

# Run tests
pytest tests/ -v

# Preview the frontend (after running scraper to generate data/)
cd frontend
python -m http.server 8000
# Visit http://localhost:8000
```

## How It Works

1. **Daily at 6 AM ET**: GitHub Actions triggers the scraper
2. **Scraper runs**: Python fetches each theater's website and parses show data
3. **Data saved**: Results are saved as `data/shows.json` and `data/status.json`
4. **Site deployed**: The frontend is deployed to GitHub Pages with fresh data
5. **You browse**: Open the site on any device to see what's playing

## Adding a New Theater

1. Create a new file in `scraper/scrapers/` (copy an existing one as template)
2. Implement the `scrape()` method for the new site's HTML structure
3. Add the class to `ALL_SCRAPERS` in `scraper/scrapers/__init__.py`
4. Add a test in `tests/`
5. Push — the next scraper run will include the new theater

## Troubleshooting

- **No shows displayed?** Check the status bar at the bottom of the page. If all sites failed, there may be a network issue with the GitHub Actions runner.
- **Stale data?** Go to Actions tab and manually trigger the workflow.
- **Site not loading?** Ensure GitHub Pages is enabled and the deploy job completed successfully.
- **Scraper failing for a site?** Theater websites change structure periodically. Check the scraper's selectors against the current HTML.
