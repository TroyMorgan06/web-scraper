# Universal Product Tracker

Track product pages over time: scrape **title**, **price**, and **availability**, store history in **SQLite**, export **CSV**, and optionally send **email alerts** when the price changes.

Uses **Playwright** (not Selenium). Prefers **JSON-LD** Product schema, with **Open Graph / CSS** as a fallback.

## Features

- Enter a product URL (desktop app, CLI, or Flask UI)
- Scrape title, price, availability
- SQLite database with price history
- CSV export
- Email alerts on price change (when SMTP is configured)
- Windows desktop `.exe` build for portfolio / download pages

## Project layout

```text
web-scraper/
  app/                 # core logic (shared by all UIs)
  gui.py               # desktop Tkinter app
  cli.py               # terminal commands
  webapp.py            # Flask UI
  templates/           # HTML for Flask
  build_exe.ps1        # package Windows app
  data/                # SQLite DB (created at runtime)
  .env.example
```

## Setup (development)

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chromium
```

Optional email alerts: copy `.env.example` to `.env` and fill in SMTP values (Gmail app password).

## Desktop app

```bash
python gui.py
```

### Build a Windows executable (for your website download)

```powershell
.\.venv\Scripts\Activate.ps1
.\build_exe.ps1
```

Output folder:

```text
dist/ProductTracker/
  ProductTracker.exe
  ms-playwright/     # Chromium used by Playwright
  data/              # DB created here when the app runs
```

Zip the entire `ProductTracker` folder and host that zip on your site. Users unzip and run `ProductTracker.exe`.

**Note:** This is an “app folder,” not a tiny single-file exe, because Playwright needs Chromium alongside the program.

## CLI usage

```bash
python cli.py add "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
python cli.py list
python cli.py check
python cli.py check --no-email
python cli.py history
python cli.py export
```

## Web UI (Flask)

```bash
python webapp.py
```

Open http://127.0.0.1:5000

## How scraping works

1. Playwright opens the page in headless Chromium
2. BeautifulSoup parses the HTML
3. Prefer `application/ld+json` Product schema
4. Fall back to Open Graph / common price selectors

**Good demo URL:** [books.toscrape.com](https://books.toscrape.com/) product pages.

## Design notes

- Core logic lives in `app/` so CLI, Flask, and the desktop app share one code path
- Secrets stay in `.env` (gitignored); DB files under `data/` are gitignored
- Email is skipped cleanly when SMTP env vars are unset
