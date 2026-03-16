# External Integrations

**Analysis Date:** 2026-03-16

## APIs & External Services

**Game/Media Metadata:**
- IGDB (Internet Game Database) - Primary game metadata source
  - SDK/Client: Custom httpx-based client in `backend/services/lookup_service.py`
  - Auth: `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET` environment variables
  - Used for: Game title lookups, release date, publisher/developer, genre, cover art

- RAWG (Rawg.io) - Game database with store links
  - SDK/Client: Custom httpx-based client in `backend/services/price/providers/rawg.py`
  - Auth: `RAWG_API_KEY` or `RAWG_KEY` environment variable
  - Used for: Game reference data, digital store links (Steam, GOG, Epic, etc.)

- Comic Vine (Wikia) - Comic metadata API
  - SDK/Client: Custom httpx-based client in `backend/services/lookup_service.py`
  - Auth: `COMICVINE_API_KEY` environment variable
  - Used for: Comic book metadata (title, publisher, issue number)

**Barcode/UPC Lookup:**
- UPCItemDB - Barcode and product database
  - SDK/Client: Custom httpx-based client in `backend/services/lookup_service.py`
  - Auth: `UPCITEMDB_API_KEY` environment variable (optional)
  - Used for: Barcode/UPC lookups to identify products

**Pricing & Market Data:**
- eBay Browse API - Live marketplace prices
  - SDK/Client: Custom async httpx client in `backend/services/price/providers/ebay.py`
  - Auth: OAuth 2.0 (client credentials) via `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`
  - Supports alternate env var names: EBAY_APP_ID, EBAY_APPID, EBAY_CLIENTID, EBAY_SECRET, EBAY_CLIENTSECRET, EBAY_SECRET_KEY
  - Token caching: `_EBAY_TOKEN_CACHE` with auto-refresh (60 second buffer)
  - Endpoint: `https://api.ebay.com/buy/browse/v1/item_summary/search`
  - Marketplace: EBAY_DE (German marketplace)
  - Used for: Real-time used game prices (median of filtered listings)
  - Filtering: Excludes bundles, consoles, accessories, defective items by title keyword matching

- PriceCharting - Retro game price aggregator
  - SDK/Client: Web scraping (BeautifulSoup) + optional REST API in `backend/services/price/providers/pricecharting.py`
  - Auth: `PRICECHARTING_TOKEN` or `PRICE_CHARTING_TOKEN` (optional for REST API)
  - REST API Endpoint: `https://www.pricecharting.com/api/product`
  - Scrape Endpoints: `https://www.pricecharting.com/search-products`
  - Used for: Local retro game prices (loose, CIB, new condition), catalog scraping
  - Supports: Video games, board games, comics, Funko figures

- Currency Exchange - EUR/USD conversion
  - Source: External API call in `backend/services/price/utils.py`
  - Used for: Convert USD prices (eBay, RAWG) to EUR for European pricing consistency

## Data Storage

**Databases:**
- SQLite (File-based)
  - Connection: `sqlite:////app/data/games.db` (Docker) or local path in development
  - ORM: SQLAlchemy 2.0.25+ with declarative models
  - Migrations: Alembic 1.13.1 with versioned migrations in `backend/alembic/versions/`
  - Schema location: `backend/db/models.py` and `backend/alembic/versions/98e0da0f0c11_initial_schema.py`
  - Tables:
    - `games` - User game collection
    - `platforms` - Gaming platforms/consoles
    - `item_images` - Cover art and additional images
    - `price_history` - Historical price tracking (PriceCharting, eBay, RAWG sources)
    - `price_catalog` - Local PriceCharting catalog cache (indexed by platform, title, pricecharting_id)
    - `value_history` - Daily snapshots of collection value (games vs hardware)
    - `app_meta` - Application settings and configuration store

**File Storage:**
- Local filesystem
  - Location: `/app/uploads/` (Docker) or local `uploads/` directory
  - Contents: User-uploaded and scraped cover images
  - Format: JPEG/PNG, organized by game ID
  - Served via: FastAPI static file mount at `/uploads`

**Caching:**
- In-memory:
  - eBay OAuth token cache: `_EBAY_TOKEN_CACHE` dict in `backend/services/price/providers/ebay.py`
  - Currency rate cache: Single-value cache for EUR/USD exchange rate

## Authentication & Identity

**Auth Provider:**
- Custom (no external auth service)
- Implementation: Admin API key in headers for protected endpoints
- Location: `backend/api/security.py`
- Methods:
  - Local-only access: Admin actions blocked for non-localhost clients without API key
  - Admin API Key: `ADMIN_API_KEY` or `COLLECTABASE_ADMIN_KEY` environment variable
  - Used for: Protecting admin operations (settings changes, scheduled jobs)
- No user authentication; single-admin model

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry, Rollbar integration)
- Logging: Python `logging` module to console and `backend/error.log`

**Logs:**
- Location: `backend/error.log` (error logs)
- Levels: INFO, WARNING, ERROR from APScheduler and background jobs
- Format: Timestamp + module + message

## CI/CD & Deployment

**Hosting:**
- Docker + Docker Compose (self-hosted containerization)
- Dockerfile: Multi-stage build (Node.js 18 → Python 3.11-slim)
- Entrypoint: `entrypoint.sh` runs Alembic migrations then Uvicorn

**CI Pipeline:**
- GitHub Actions workflow (source location: `.github/workflows/` - not fully explored)
- Can configure GitHub Actions cron schedule for automated price updates (detected in settings)

**Local Development:**
- `npm run dev` - Frontend dev server (Vite on port 3000, proxy to API)
- `python backend/main.py` - Backend dev server (Uvicorn on port 8000)
- `cli.py` - Command-line tool for imports/exports

## Environment Configuration

**Required env vars (for external integrations):**
- `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET` - Game metadata lookups (conditional: required for IGDB API)
- `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET` - eBay price fetching (conditional: required for eBay Browse)
- `RAWG_API_KEY` - RAWG game references (optional)
- `PRICECHARTING_TOKEN` - PriceCharting REST API (optional; scraping works without token)
- `DATABASE_URL` - SQLite path (default provided)
- `UPLOADS_DIR` - Image storage path (default provided)

**Secrets location:**
- `.env` and `backend/.env` files (development)
- Docker environment variables or `.env` file mounted at runtime
- Note: Never committed to git (see `.gitignore`)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- eBay API token refresh - Automatic OAuth token refresh every ~59 minutes
- PriceCharting scraping - No webhook; polling-based via scheduled jobs

## Scheduled Background Jobs

**APScheduler Integration:**
- Framework: APScheduler 3.10.4 AsyncIOScheduler
- Configuration: `backend/scheduler.py`
- Jobs:
  1. `scheduled_price_update` - Runs every N hours (configurable via `apscheduler_interval` setting)
     - Scrapes PriceCharting catalog for owned platforms
     - Updates owned game prices from local catalog cache
     - Logs results to `backend/error.log`
  2. `snapshot_collection_value` - Daily snapshot
     - Records total collection value, game vs hardware breakdown
     - Stores in `value_history` table
- Enable/disable: Via Settings UI (writes to `app_meta` table)
- Alternative: GitHub Actions cron for distributed scheduling

---

*Integration audit: 2026-03-16*
