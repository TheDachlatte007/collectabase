# Technology Stack

**Analysis Date:** 2026-03-16

## Languages

**Primary:**
- Python 3.11 - Backend API, CLI tools, web scraping, price tracking
- TypeScript 5.9.3 - Frontend type safety
- JavaScript (ES modules) - Frontend runtime
- HTML/CSS - Frontend markup and styling

**Secondary:**
- SQL - SQLite database schema and migrations
- Bash - Shell scripts for Docker entrypoint

## Runtime

**Environment:**
- Python 3.11 (backend) - FastAPI server
- Node.js 18-alpine (frontend build) - Development and production build process
- Docker 20.10+ (containerized deployment)

**Package Manager:**
- npm - Frontend dependencies
- pip - Python backend dependencies
- Lockfile: `frontend/package-lock.json` (present), `backend/requirements.txt` pinned versions

## Frameworks

**Core:**
- FastAPI 0.109.0 - Backend REST API framework
- Uvicorn 0.27.0 - ASGI server for FastAPI
- Vue.js 3.4.0 - Frontend SPA framework
- Vue Router 4.2.0 - Frontend routing
- Pinia 3.0.4 - State management for Vue

**Build/Dev:**
- Vite 5.0.0 - Frontend build tool and dev server
- TypeScript 5.9.3 - Type checking and transpilation
- @vitejs/plugin-vue 5.0.0 - Vue integration for Vite

**Database:**
- SQLAlchemy 2.0.25+ - Python ORM and database abstraction
- Alembic 1.13.1 - Database schema migrations
- SQLite - Local persistent database (file-based)

## Key Dependencies

**Backend HTTP & Web:**
- httpx 0.26.0 - Async HTTP client for external API calls (replaces requests)
- beautifulsoup4 4.12.3 - HTML parsing for web scraping (PriceCharting catalog)
- python-multipart 0.0.6 - Form data parsing for file uploads

**Backend Configuration:**
- python-dotenv 1.0.0 - Environment variable loading from `.env` files

**Backend Scheduling:**
- apscheduler 3.10.4 - APScheduler for background price updates and collection value snapshots

**Frontend Data Visualization:**
- chart.js 4.4.0 - Chart rendering library
- vue-chartjs 5.3.0 - Vue integration for Chart.js

**Frontend Features:**
- @zxing/browser 0.1.5 - QR code / barcode scanner

## Configuration

**Environment:**
- Location: `/b/Code/collectabase/stack.env` (Docker defaults)
- `.env` files in root and `backend/` directory (local development)
- Environment variables configured via Docker compose or UI settings page

**Key Variables:**
- `DATABASE_URL` - SQLite database path (default: `sqlite:////app/data/games.db`)
- `UPLOADS_DIR` - Directory for cover image uploads (default: `/app/uploads`)
- `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET` - IGDB game metadata API credentials
- `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET` - eBay Browse API credentials (alias variants: EBAY_APP_ID, EBAY_APPID, EBAY_CLIENTID, EBAY_SECRET, EBAY_CLIENTSECRET, EBAY_SECRET_KEY)
- `RAWG_API_KEY` (or `RAWG_KEY`) - RAWG game database API
- `PRICECHARTING_TOKEN` (or `PRICE_CHARTING_TOKEN`) - PriceCharting API token for price lookups
- `UPCITEMDB_API_KEY` - UPC/barcode lookup API (optional)
- `COMICVINE_API_KEY` - Comic Vine API for comic book metadata (optional)
- `ADMIN_API_KEY` (or `COLLECTABASE_ADMIN_KEY`) - Remote admin access key
- `TZ` - Timezone (default: `Europe/Berlin`)

**Build Configuration:**
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/vite.config.js` - Vite build configuration (proxy to `/api` → localhost:8000)
- `backend/alembic.ini` - Alembic migration configuration

## Platform Requirements

**Development:**
- Python 3.11+
- Node.js 18+
- Docker (for containerized development/deployment)
- Git (for version control)
- Virtual environment (`/b/Code/collectabase/.venv`)

**Production:**
- Docker engine with Docker Compose
- 8GB+ RAM recommended (for background price scraping)
- Persistent volume for SQLite database (`/app/data/`)
- Persistent volume for image uploads (`/app/uploads/`)

**Deployment:**
- Docker multi-stage build: Node.js 18-alpine (frontend) → Python 3.11-slim (backend)
- Exposed port: 8000 (API + static frontend)
- Stateless backend (SQLite stored in volumes)
- Health check: `curl` configured in Docker

---

*Stack analysis: 2026-03-16*
