# Architecture

**Analysis Date:** 2026-03-16

## Pattern Overview

**Overall:** Monolithic full-stack application with clear separation between backend API and frontend SPA. FastAPI backend serves a Vue 3 frontend, with background job scheduling and external service integrations.

**Key Characteristics:**
- Full-stack monolith (Python backend + Vue 3 frontend in single repo)
- RESTful API with modular route handlers
- Scheduled background jobs for price catalog scraping and updates
- Multi-source data lookup and enrichment (IGDB, Comic Vine, HobbyDB, MFC, eBay, PriceCharting)
- SQLAlchemy ORM with SQLite database and Alembic migrations

## Layers

**Presentation (Frontend):**
- Purpose: Vue 3 SPA providing rich, responsive UI for collection management
- Location: `frontend/src/`
- Contains: Vue components, stores, routers, API clients
- Depends on: API HTTP client (`frontend/src/api/http.js`)
- Used by: Browser users accessing the application

**API Gateway (Backend):**
- Purpose: FastAPI application serving all backend endpoints and routing requests
- Location: `backend/main.py`
- Contains: App initialization, router includes, static file mounting, startup/shutdown hooks
- Depends on: All route modules, database layer, services
- Used by: Frontend SPA making HTTP requests

**Route Handlers:**
- Purpose: REST endpoint implementations organized by resource
- Location: `backend/api/routes/`
- Contains: `games.py` (CRUD), `lookup.py` (metadata enrichment), `import_export.py` (data import/export), `stats.py` (analytics), `settings.py` (configuration)
- Depends on: Database layer, services, error handling
- Used by: API gateway

**Services (Business Logic):**
- Purpose: Reusable business logic isolated from HTTP concerns
- Location: `backend/services/`
- Contains: `lookup_service.py` (entity lookup and enrichment), price providers (`price/providers/`), catalog management (`price/catalog.py`)
- Depends on: Database, external APIs, utilities
- Used by: Route handlers, scheduler

**Data Access (Database):**
- Purpose: SQLAlchemy ORM models and session management
- Location: `backend/db/models.py`, `backend/db/session.py`, `backend/database.py`
- Contains: SQLAlchemy declarative models (Game, Platform, PriceHistory, etc.), connection pooling, legacy wrapper for backward compatibility
- Depends on: SQLAlchemy, SQLite driver
- Used by: Services, route handlers

**Background Jobs:**
- Purpose: Scheduled and manual long-running operations
- Location: `backend/scheduler.py`, `backend/jobs.py`, `backend/price_tracker.py`
- Contains: APScheduler configuration, job tracking, price update scheduling
- Depends on: Database, services, utilities
- Used by: Startup/shutdown events, API endpoints

**Frontend State Management:**
- Purpose: Centralized reactive state for game collection and UI
- Location: `frontend/src/stores/useGameStore.ts`
- Contains: Pinia store with games, platforms, loading states
- Depends on: API client
- Used by: All views and components needing data

## Data Flow

**Collection Display Flow:**

1. App mounts → `main.js` loads UI preferences → `App.vue` renders layout
2. View (e.g., `GamesList.vue`) mounts → calls `useGameStore().load()`
3. Store dispatches `gamesApi.list()` → HTTP GET `/api/games`
4. Backend handler `backend/api/routes/games.py::list_games()` queries database
5. Results returned as JSON → Store caches in Pinia state
6. Component computes filtered views (collection vs wishlist) → renders

**Game Enrichment Flow:**

1. User adds game manually via `AddGame.vue`
2. Frontend calls `lookupApi.combined(title)` → POST `/api/lookup/combined`
3. `backend/api/routes/lookup.py` delegates to `lookup_service.py`
4. Service queries multiple providers in parallel (IGDB, Comic Vine, HobbyDB, MFC)
5. Results merged and returned to frontend
6. User selects best match or confirms manual entry
7. Game created via `gamesApi.create()`

**Price Tracking Flow:**

1. User clicks "Check Price" on game detail → `priceApi.check(id)`
2. POST `/api/games/{id}/fetch-market-price` routes to `price_tracker.py`
3. Handler checks local catalog first via `_lookup_local_catalog_price()`
4. Falls back to live scrapers (PriceCharting, eBay) if not cached
5. Price history inserted into database
6. Returns pricing breakdown (loose/complete/new conditions)

**Scheduled Catalog Update:**

1. Scheduler triggers `scheduled_price_update()` on configured interval
2. Queries all owned platforms from database
3. For each platform: calls `scrape_platform_catalog()` from `price/catalog.py`
4. Catalog entries upserted to `price_catalog` table with change tracking
5. Game collection enriched with latest prices from catalog

**State Management Flow (Frontend):**

1. `useGameStore` is Pinia store providing centralized state
2. Actions (`load`, `refresh`, `updateGame`, `removeGame`, `addGame`) modify state
3. Computed getters filter state (collection vs wishlist)
4. Components subscribe to reactive state
5. Optimistic updates in `updateGame()` reduce latency

## Key Abstractions

**Game Entity:**
- Purpose: Represents collectible items (games, hardware, comics, figures, funkos)
- Examples: `backend/db/models.py::Game`, `frontend/src/types/index.ts::Game`
- Pattern: Flexible schema with `item_type` field supporting multiple collectible categories. Metadata fields (IGDB ID, Comic Vine ID, HobbyDB ID, MFC ID) enable cross-catalog lookups.

**Price Providers:**
- Purpose: Abstract different price data sources
- Examples: `backend/services/price/providers/pricecharting.py`, `ebay.py`, `rawg.py`
- Pattern: Each provider exports a `fetch_*` function with consistent signature. Registry pattern via imports in `price_tracker.py`.

**Lookup Service:**
- Purpose: Orchestrate metadata enrichment from multiple sources
- Examples: `backend/services/lookup_service.py`
- Pattern: Single entry point `lookup_game()` handles provider selection, parallel queries, result merging, and fallback logic.

**Database Wrapper (Legacy Compatibility):**
- Purpose: Make SQLAlchemy Session behave like sqlite3 connection for gradual migration
- Examples: `backend/database.py::LegacyDBWrapper`, `backend/database.py::RowProxy`
- Pattern: Adapter pattern to support existing code written against raw SQL without full ORM refactor.

**Job Tracker:**
- Purpose: Track long-running background operations in-memory
- Examples: `backend/jobs.py`
- Pattern: Simple dictionary-based state machine. Tracks progress, success/failure counts, and completion status.

## Entry Points

**Backend Entry Point:**
- Location: `backend/main.py`
- Triggers: `python -m uvicorn backend.main:app` or Docker CMD
- Responsibilities: FastAPI app initialization, router registration, database setup, scheduler startup, static file mounting

**Frontend Entry Point:**
- Location: `frontend/src/main.js`
- Triggers: Vite dev server or built `index.html`
- Responsibilities: Vue app creation, Pinia store initialization, router setup, service worker registration

**Route Handlers (API):**
- Games: `backend/api/routes/games.py` - Game CRUD, enrichment, cover upload
- Lookup: `backend/api/routes/lookup.py` - Metadata search across providers
- Import/Export: `backend/api/routes/import_export.py` - CSV/CLZ data import, CSV export
- Stats: `backend/api/routes/stats.py` - Collection statistics and value tracking
- Settings: `backend/api/routes/settings.py` - App configuration, credentials, database management
- Price Tracker: `backend/price_tracker.py` - Price fetching, history management

**Views (Frontend):**
- `GamesList.vue` - Display collection/wishlist with search/filter
- `GameDetail.vue` - Single item details, images, price history
- `AddGame.vue` - Create or edit game with lookup-based enrichment
- `Wishlist.vue` - Dedicated wishlist view with price alerts
- `PriceBrowser.vue` - Search and filter price catalog
- `Stats.vue` - Collection analytics and value charts
- `Import.vue` - CSV/CLZ import interface
- `Settings.vue` - Configuration, API keys, scheduler settings
- `MoreMenu.vue` - Additional navigation and options

## Error Handling

**Strategy:** HTTP exception codes with JSON error payloads; try-catch blocks at service boundaries; graceful degradation for external API failures.

**Patterns:**
- Custom error classes in `backend/api/errors.py` (e.g., `conflict()`, `not_found()`)
- Route handlers catch exceptions and return appropriate HTTP status codes
- Failed external lookups return partial results or empty arrays
- Price fetching falls back to local catalog if live scraping fails
- Frontend API client (`frontend/src/api/http.js`) wraps fetch with safe JSON parsing
- Notifications (`NotificationStack.vue`) display errors to users

## Cross-Cutting Concerns

**Logging:** Python `logging` module used in backend; console output in frontend for development.

**Validation:** Pydantic models for request validation in route handlers; basic field validation in frontend components.

**Authentication:** Optional admin API key stored in localStorage (`frontend/src/api/http.js::withAdminHeaders()`); checked via `X-Admin-Key` header; implemented in `backend/api/security.py`.

**Internationalization:** Not currently implemented; locale-aware formatting for currency (EUR/USD conversion via `backend/services/price/utils.py`).

---

*Architecture analysis: 2026-03-16*
