# MSc Application Dates Scraper Dashboard
 
A Django application that scrapes Greek (and other) university MSc programme websites for application open dates, deadlines, and apply links, then presents the results in a searchable staff dashboard. Scraping is powered by an LLM (via ScrapeGraphAI) with Playwright/Chromium for rendering and pdfplumber/python-docx for parsing PDF and Word attachments.
 
The scraping engine itself (`services/scraper.py`) is documented in detail in its own README — see [`README.md`](http://github.com/faethonAnt/MSc_date_scraper/blob/main/README.md). This document covers the surrounding Django project: how it's structured, how to run it with Docker, and how the web UI ties into the scraper.
 
---
 
## Architecture
 
```
┌──────────────────────────────┐        ┌──────────────────────┐
│      scraper container       │        │     db container     │
│     (Django + Gunicorn)      │◄──────►│     PostgreSQL 16    │
│                              │        └──────────────────────┘
│  - core/    (auth, dashboard)│
│  - data/    (Programme model,│
│              views, forms)   │
│  - services/                 │
│      scraper.py  (scraping)  │
│      services.py (API sync)  │
│                              │
│  Playwright + Chromium       │
│  (bundled in image)          │
└──────────────────────────────┘
```
 
- **`core`** — authentication (staff-only login) and the top-level dashboard page.
- **`data`** — the `Programme` model, the `ScraperRunForm` model for the scraper parameters, the results table/filters, CSV/JSON export, and the scraper run/stop/status/log-stream endpoints.
- **`services`** — the scraper engine (`scraper.py`), the external programmes API sync (`services.py`), and the `results/` output folder (`pass1_results.json`, `pass2_results.json`, `results.json`, `results.csv`, `errors.json`, `scraper.log`).
The scraper runs **in-process** inside the same Gunicorn worker (kicked off in a background thread from `post_scraper`), not as a separate worker container
 
---
 
## Tech stack
 
| Layer | Technology |
|---|---|
| Web framework | Django 6 |
| WSGI server | Gunicorn (gthread worker) |
| Database | PostgreSQL 16 |
| Scraping | ScrapeGraphAI + Playwright (Chromium) |
| LLM | OpenAI-compatible API (default model: `openai/gpt-4.1-nano`) |
| PDF/DOCX parsing | pdfplumber, python-docx |
| Static files | WhiteNoise |
| Containerisation | Docker + Docker Compose |
 
---
 
## Prerequisites
 
- Docker and Docker Compose
- An OpenAI-compatible API key (for the LLM extraction step)
- Access to the programmes source API (`API_URL`) used by `services.sync_programmes`
---
 
## Setup
 
1. **Clone the repo** and move into the project root (where `docker-compose.yml` lives).
2. **Create your `.env` file** from the dummy template and fill in real values:
```dotenv
   POSTGRES_DB=<your_db_name>
   POSTGRES_USER=<your_db_user>
   POSTGRES_PASSWORD=<your_db_password>
   POSTGRES_PORT=5432
 
   DJANGO_DEBUG=False
   DJANGO_SECRET_KEY=<generate-a-real-secret-key>
   DJANGO_ALLOWED_HOSTS=*
 
   API_URL=<your_api_url>
   OPENAI_API_KEY=<api_key>
```
 
  
3. **Build and start the stack:**
```bash
   docker compose up --build -d
```
 
   This will:
   - Start Postgres and wait for it to report healthy.
   - Build the Django image (installing Python deps and Chromium via Playwright).
   - Run migrations, collect static files, and start Gunicorn on port `8000`.
4. **Create a staff user** (required — all dashboard/scraper views are gated behind `is_staff`):
```bash
   docker compose exec scraper python manage.py createsuperuser
```
 
5. **Log in** at `http://localhost:8000/login/` with that account, then visit the dashboard at `http://localhost:8000/`.
---
 
## Environment variables
 
| Variable | Used by | Description |
|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Django, Postgres container | Database credentials |
| `POSTGRES_PORT` | Django | Database port |
| `DJANGO_DEBUG` | Django | `True`/`False` — keep `False` outside local dev |
| `DJANGO_SECRET_KEY` | Django | Must be a real, private secret in any non-local environment |
| `DJANGO_ALLOWED_HOSTS` | Django | Comma-separated hostnames, or `*` |
| `API_URL` | `services.services.fetch_programmes_data`, `sync_programmes` | Source API that supplies the current MSc programme list |
| `OPENAI_API_KEY` | `services.scraper.get_graph_config` | LLM key used by ScrapeGraphAI for every extraction call |
 
---
 
## Using the app
 
### Dashboard (`/`)
Landing page for staff users (redirects to `/login/` if not authenticated as staff).
 
### Results (`/results/`)
Searchable, filterable, paginated table of all programmes: free-text search, university/city/topic filters, and status filters (`found`, `missing`, `error`, `open`, `closed`, `rolling`, `coming_soon`). Supports CSV (`/results/export/csv/`) and JSON (`/results/export/json/`) export of the current filtered set.
 
### Scraper (`/scraper/`)
Form-driven trigger for a scraper run (`POST /scraper/run/`). Only one run can be active at a time — a second `POST` while `_scraper_state["running"]` is `True` returns `409 Conflict`. Before launching the scraper it first syncs the local `Programme` table against `API_URL` via `sync_programmes`.
 
Progress is visible two ways:
- `GET /scraper/status/` — polls the in-memory `_scraper_state` dict (`running`, `result`, `error`).
- `GET /scraper/log/stream/` — a Server-Sent Events stream that tails `services/results/scraper.log` line by line, with lightweight CSS classes applied per line (created/updated/skipped/error/progress/found/etc.) for colour-coding in the UI.
A run in progress can be cancelled with `POST /scraper/stop/`, which sets a cooperative shutdown flag (`request_shutdown()` → `_shutdown = True` inside the scraper module) rather than killing the thread — in-flight tasks finish and progress is saved before the run ends.
 
### Sync (`/sync/`)
Manually trigger a sync of the local `Programme` table against the external programmes API, independent of running the scraper (`POST /sync/run/`).
 
---
 
## URL reference
 
| Path | View | Purpose |
|---|---|---|
| `/` | `core.views.dashboard` | Dashboard landing page |
| `/login/`, `/logout/` | Django auth views | Staff login/logout |
| `/results/` | `data.views.programmes_view` | Filterable results table (full page) |
| `/results/table/` | `data.views.programmes_table` | Results table partial (for HTMX-style refresh) |
| `/results/export/csv/` | `data.views.export_csv` | Download filtered results as CSV |
| `/results/export/json/` | `data.views.export_json` | Download filtered results as JSON |
| `/scraper/` | `data.views.scraper_view` | Scraper control page |
| `/scraper/run/` | `data.views.post_scraper` | Start a scraper run |
| `/scraper/status/` | `data.views.scraper_status` | Current run state (partial) |
| `/scraper/log/stream/` | `data.views.scraper_log_stream` | Live log tail (SSE) |
| `/scraper/stop/` | `data.views.scraper_stop` | Request cooperative shutdown of the current run |
| `/sync/` | `data.views.sync_view` | Sync control page |
| `/sync/run/` | `data.views.sync_programmes_view` | Trigger a manual sync |
| `/admin/` | Django admin | Standard Django admin site |
 
All `data` and `core` dashboard views require an authenticated **staff** user.
 
## Notes on the scraper thread
 
`post_scraper` launches `run_scraper(args)` in a **background daemon thread** inside the running Gunicorn worker, not a separate process or container. This has two practical implications for deployment:
 
- **Use exactly one Gunicorn worker** (as the provided Compose command does: `--workers 1 --threads 6`) so that `_scraper_state` — a plain in-process dict — stays consistent. With multiple workers, each would have its own copy of `_scraper_state`, and the status/log endpoints could talk to a different worker than the one running the scrape.
- **`--timeout 1800`** is set generously on Gunicorn because the request that starts the scraper (`POST /scraper/run/`) returns almost immediately (the scrape itself runs in a background thread), but other long-lived requests — notably the SSE log stream — need a high timeout to stay open.
 
---
 
## Scraper output volume
 
`services/results/` is mounted as a Docker volume (`./services/results:/app/services/results`) so scraper output persists across container rebuilds/restarts. Back this up or add it to your `.gitignore` as appropriate — it contains raw scrape data, not just final results.
 
---
