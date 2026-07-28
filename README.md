# Universal Product Tracker

Track product pages over time: scrape **title**, **price**, and **availability**, store history in **SQLite**, export **CSV**, and optionally send **email alerts** when the price changes.

Uses **Playwright**. Prefers **JSON-LD** Product schema, with **Open Graph / CSS** as a fallback.

## Features

- Enter a product URL (CLI or small Flask UI)
- Scrape title, price, availability
- SQLite database with price history
- CSV export
- Email alerts on price change (when SMTP is configured)

## Project layout

```text
web-scraper/
  app/
    config.py      # paths + env settings
    db.py          # SQLite helpers
    scraper.py     # Playwright + JSON-LD / Open Graph
    alerts.py      # SMTP email
    export.py      # CSV export
    tracker.py     # scrape → save → alert
  cli.py           # terminal commands
  webapp.py        # Flask UI
  templates/       # HTML for the web UI
  data/            # SQLite DB (created at runtime)
  .env.example     # copy to .env for SMTP