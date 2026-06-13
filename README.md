# 🕷 DataHarvest — Production Web Scraper Dashboard

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **production-grade** web scraping platform with a real-time dashboard. Scrape job listings, products, and news — then filter, search, export, and schedule with a clean REST API and dark-mode dashboard.

---

## 📸 Dashboard Preview

```
┌─────────────────────────────────────────────────────────────────────┐
│  🕷 DataHarvest     ○ Dashboard  ⚙ Jobs  🗃 Items  📤 Export        │
├─────────────────────────────────────────────────────────────────────┤
│  📊 Dashboard                            [⟳ Refresh] [＋ New Job]  │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  4,231   │ │   127    │ │   891    │ │    3     │ │    1     │ │
│  │  Items   │ │  Today   │ │  Week    │ │  Active  │ │  Failed  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│                                                                     │
│  Activity (7d)          ││ Top Sources                             │
│  ▂▄▆█▅▃▇               ││  hackernews     ████████░ 2,103        │
│                          ││  books_to_scrape ████░░░░  847        │
│                          ││  hackernews_news ██░░░░░░  412        │
├─────────────────────────────────────────────────────────────────────┤
│  Recent Items                                                       │
│  Senior Python Dev · hackernews · TechCorp · Remote    2m ago      │
│  Clean Code (book) · books_to_scrape · £14.99 · ★4.0  5m ago      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                            │
│                    HTML / CSS / Vanilla JS                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP (REST)
┌──────────────────────────▼──────────────────────────────────────────┐
│                      FastAPI Application                            │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │  /api/v1/    │   │  /api/v1/    │   │  Background Tasks    │   │
│  │  jobs/       │   │  items/      │   │  (APScheduler)       │   │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘   │
│         │                  │                        │               │
│  ┌──────▼────────────────────────────────────────────────────────┐ │
│  │                    Service Layer                               │ │
│  │  ScraperService · ExportService · SchedulerService            │ │
│  └──────┬────────────────────────────────────────────────────────┘ │
│         │                                                           │
│  ┌──────▼────────────────────────────────────────────────────────┐ │
│  │                  Repository Layer                              │ │
│  │  ScrapeJobRepository · ScrapedItemRepository                  │ │
│  └──────┬────────────────────────────────────────────────────────┘ │
└─────────│───────────────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────┐   ┌────────────────────────────────┐
│         PostgreSQL             │   │       Scraper Engine           │
│                                │   │                                │
│  scrape_jobs                   │   │  BaseScraper                   │
│  scraped_items                 │   │  ├── HackerNewsJobsScraper     │
│    └ content_hash (dedup)      │   │  ├── BooksScraper              │
│                                │   │  ├── HackerNewsNewsScraper     │
└────────────────────────────────┘   │  └── SeleniumBaseScraper       │
                                     │       (for JS-heavy pages)     │
                                     │                                │
                                     │  Retry: tenacity (3 attempts)  │
                                     │  Dedup: SHA-256 hash           │
                                     └────────────────────────────────┘
```

---

## 📁 Project Structure

```
scraper-dashboard/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── jobs.py          # CRUD + trigger endpoints
│   │       └── items.py         # Filter, paginate, export
│   ├── core/
│   │   ├── config.py            # Pydantic-settings env management
│   │   └── logging.py           # Loguru structured logging
│   ├── database/
│   │   ├── session.py           # SQLAlchemy engine + get_db()
│   │   └── repository.py        # Data access layer (repository pattern)
│   ├── models/
│   │   ├── scrape_job.py        # ScrapeJob ORM model
│   │   └── scraped_item.py      # ScrapedItem ORM model (with hash dedup)
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── scrapers/
│   │   ├── base.py              # BaseScraper (retry, logging, hashing)
│   │   ├── jobs_scraper.py      # HackerNews jobs
│   │   ├── products_scraper.py  # Books to Scrape (multi-page)
│   │   ├── news_scraper.py      # HN top stories (concurrent API calls)
│   │   ├── selenium_scraper.py  # Selenium base + Indeed example
│   │   └── __init__.py          # Scraper factory / registry
│   ├── services/
│   │   ├── scraper_service.py   # Orchestration / business logic
│   │   ├── export_service.py    # CSV + Excel export
│   │   └── scheduler.py         # APScheduler integration
│   └── main.py                  # FastAPI app + lifespan
├── frontend/
│   └── templates/
│       └── index.html           # Full SPA dashboard (no build step)
├── tests/
│   ├── api/test_api.py          # FastAPI endpoint tests
│   └── scrapers/test_scrapers.py# Scraper unit tests
├── scripts/
│   ├── seed.py                  # Create demo jobs
│   └── migrations.py            # Alembic migration notes
├── logs/                        # Rotated log files (created at runtime)
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Option A — Docker (recommended)

```bash
git clone https://github.com/yourname/scraper-dashboard.git
cd scraper-dashboard

cp .env.example .env
docker-compose up -d

# Seed demo jobs
docker-compose exec app python scripts/seed.py

# Dashboard → http://localhost:8000
# API docs  → http://localhost:8000/api/docs
```

### Option B — Local development

```bash
# 1. Create & activate virtualenv
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Postgres (or update .env to point at your instance)
docker run -d --name pg \
  -e POSTGRES_USER=scraper_user \
  -e POSTGRES_PASSWORD=scraper_pass \
  -e POSTGRES_DB=scraper_db \
  -p 5432:5432 postgres:16-alpine

# 4. Configure environment
cp .env.example .env   # edit as needed

# 5. Seed demo jobs
python scripts/seed.py

# 6. Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` for the dashboard.

---

## 🔌 REST API Reference

Base URL: `/api/v1`

### Scrape Jobs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs/` | List all jobs |
| `POST` | `/jobs/` | Create a new job |
| `GET` | `/jobs/{id}` | Get a specific job |
| `PATCH` | `/jobs/{id}` | Update job config |
| `DELETE` | `/jobs/{id}` | Delete job + items |
| `POST` | `/jobs/{id}/run` | Trigger job (background) |

**Create job payload:**
```json
{
  "name": "Tech Jobs Daily",
  "url": "https://news.ycombinator.com/item?id=40224213",
  "job_type": "jobs",
  "is_scheduled": true,
  "schedule_interval_hours": 12,
  "use_selenium": false
}
```

### Scraped Items

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/items/` | List with filters + pagination |
| `GET` | `/items/stats` | Dashboard statistics |
| `GET` | `/items/export` | Download CSV or Excel |

**Query parameters for `/items/`:**
```
q           – full-text search (title, description, company, location)
job_id      – filter by job
source      – filter by scraper source
category    – jobs / products / technology
location    – filter by location
company     – filter by company
min_price   – min price (products)
max_price   – max price (products)
page        – page number (default 1)
page_size   – results per page (max 100, default 20)
```

**Export:**
```
GET /api/v1/items/export?format=csv
GET /api/v1/items/export?format=excel&job_id=1
```

---

## ⚙️ Scraper Configuration

### Job Types & Default Sources

| Type | Default Source | Scraper |
|------|----------------|---------|
| `jobs` | HackerNews Who's Hiring | `HackerNewsJobsScraper` |
| `products` | books.toscrape.com | `BooksScraper` (5 pages) |
| `news` | HackerNews Top Stories | `HackerNewsNewsScraper` (concurrent) |

### Adding a Custom Scraper

```python
# app/scrapers/my_scraper.py
from app.scrapers.base import BaseScraper

class MyScraper(BaseScraper):
    SOURCE_NAME = "my_site"
    DEFAULT_CATEGORY = "jobs"

    def scrape(self):
        soup = self.fetch_page(self.url)   # auto-retry, logging built in
        items = []
        for card in soup.select(".job-card"):
            items.append(self.build_item(
                title=card.select_one("h2").text,
                url=card.select_one("a")["href"],
                company=card.select_one(".company").text,
            ))
        return items  # hashing + dedup handled by framework
```

Then register it in `app/scrapers/__init__.py`.

---

## 🧪 Running Tests

```bash
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html
```

Tests use SQLite in-memory — no Postgres required for the test suite.

---

## 📋 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `DEBUG` | `false` | Enable debug logging |
| `SCRAPE_TIMEOUT` | `30` | HTTP timeout per request |
| `SCRAPE_RETRY_ATTEMPTS` | `3` | Max retries on failure |
| `SCRAPE_RETRY_DELAY` | `5` | Seconds between retries |
| `SCHEDULER_ENABLED` | `true` | Enable APScheduler |
| `DEFAULT_SCRAPE_INTERVAL_HOURS` | `6` | Default schedule interval |
| `SELENIUM_HEADLESS` | `true` | Headless Chrome mode |
| `ALLOWED_ORIGINS` | `localhost:*` | CORS origins |

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Start with DB admin UI (Adminer on :8080)
docker-compose --profile tools up -d

# Scale app workers
docker-compose up -d --scale app=3

# Rebuild after code changes
docker-compose up -d --build
```

---

## 🔮 Scaling Roadmap

| Enhancement | Description |
|-------------|-------------|
| **Celery + Redis** | Replace BackgroundTasks with distributed task queue |
| **Proxy rotation** | Integrate rotating proxies to avoid IP blocks |
| **Anti-bot bypass** | Playwright + stealth plugins for JS-heavy targets |
| **Vector search** | pgvector for semantic item similarity |
| **Webhook alerts** | Notify Slack/email on scrape completion or failure |
| **Data enrichment** | Post-scrape LLM enrichment (company info, category) |
| **Multi-tenant** | User auth, per-user jobs with JWT |
| **Kubernetes** | Helm chart for k8s deployment |
| **Prometheus metrics** | `/metrics` endpoint for observability |
| **S3 export** | Direct export to S3 / GCS buckets |

---

## 📊 Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| DB | PostgreSQL 16 |
| Validation | Pydantic v2 |
| Scraping | BeautifulSoup4 + requests + Selenium |
| Scheduling | APScheduler |
| Retry logic | tenacity |
| Export | openpyxl (Excel) + csv |
| Logging | loguru |
| Testing | pytest + httpx |
| Container | Docker + docker-compose |
| Frontend | Vanilla JS SPA (zero build step) |

---

## 📄 License

MIT — free to use in portfolio projects, client work, and products.

---

*Built as a production-ready engineering portfolio project demonstrating clean architecture, service layer separation, repository pattern, async background tasks, and full-stack delivery.*
