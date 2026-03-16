# Codebase Structure

**Analysis Date:** 2026-03-16

## Directory Layout

```
collectabase/
├── backend/                    # Python FastAPI backend
│   ├── alembic/               # Database migrations
│   ├── api/                   # HTTP route handlers
│   │   ├── routes/            # Modular route implementations
│   │   └── security.py        # Authentication middleware
│   ├── db/                    # Database layer
│   │   ├── models.py          # SQLAlchemy models
│   │   └── session.py         # Session management
│   ├── services/              # Business logic layer
│   │   ├── lookup_service.py  # Multi-provider entity lookup
│   │   └── price/             # Price provider integrations
│   ├── static/                # Console fallback images
│   ├── main.py                # FastAPI app entry point
│   ├── database.py            # DB wrapper and utilities
│   ├── scheduler.py           # Background job scheduler
│   ├── jobs.py                # Job tracking system
│   └── price_tracker.py       # Price fetching router
│
├── frontend/                  # Vue 3 + TypeScript frontend
│   ├── public/                # Static assets
│   ├── src/
│   │   ├── api/               # HTTP client abstractions
│   │   ├── components/        # Reusable Vue components
│   │   ├── composables/       # Vue composition utilities
│   │   ├── router/            # Vue Router configuration
│   │   ├── stores/            # Pinia state management
│   │   ├── types/             # TypeScript interfaces
│   │   ├── utils/             # Helper functions
│   │   ├── views/             # Page-level components
│   │   ├── App.vue            # Root component
│   │   ├── main.js            # Entry point
│   │   └── style.css          # Global styles
│   ├── vite.config.js         # Vite build config
│   ├── tsconfig.json          # TypeScript config
│   └── package.json           # NPM dependencies
│
├── .planning/                 # GSD planning documents
├── data/                      # User data and exports
├── uploads/                   # Uploaded images and files
├── Dockerfile                 # Container image
├── docker-compose.yml         # Local dev environment
├── cli.py                     # CLI utilities
└── TODO.md                    # Development roadmap
```

## Directory Purposes

**Backend Structure:**

**`backend/`**
- Purpose: All server-side code, API handlers, database logic
- Contains: Python modules, SQLAlchemy models, route handlers, services
- Key files: `main.py`, `database.py`

**`backend/api/`**
- Purpose: HTTP API layer
- Contains: Route handlers organized by resource
- Key files: `routes/games.py`, `routes/lookup.py`, `routes/stats.py`

**`backend/api/routes/`**
- Purpose: Modular REST endpoint implementations
- Files: `games.py` (game CRUD), `lookup.py` (metadata), `import_export.py` (import/export), `stats.py` (analytics), `settings.py` (config), `clz_import.py` (CLZ import), `price.py` (if exists)

**`backend/db/`**
- Purpose: Data access layer and ORM models
- Contains: SQLAlchemy declarative models, session factory, connection management
- Key files: `models.py` (ORM definitions), `session.py` (engine/session setup)

**`backend/services/`**
- Purpose: Business logic and external integrations
- Contains: Lookup service, price provider implementations, utility functions
- Key files: `lookup_service.py`, `price/catalog.py`, `price/providers/`

**`backend/services/price/`**
- Purpose: Price data aggregation and catalog management
- Contains: Platform-specific scrapers, provider clients, utility functions
- Key files: `catalog.py` (price catalog CRUD), `providers/pricecharting.py`, `providers/ebay.py`, `providers/rawg.py`, `utils.py` (platform mappings)

**`backend/services/price/providers/`**
- Purpose: External price source integrations
- Files: `pricecharting.py` (PriceCharting scraper), `ebay.py` (eBay Browse API), `rawg.py` (RAWG game metadata)

**`backend/alembic/`**
- Purpose: Database schema migrations
- Contains: Alembic configuration and versioned migration scripts
- Key files: `alembic.ini`, `versions/*.py`

**`backend/static/`**
- Purpose: Static fallback images for platforms
- Contains: Subdirectories organized by manufacturer (Nintendo, Sony, Microsoft)
- Key files: Console images for offline fallback when cover URLs fail

**Frontend Structure:**

**`frontend/src/`**
- Purpose: All frontend source code
- Contains: Components, stores, utilities, styles

**`frontend/src/api/`**
- Purpose: HTTP client abstractions
- Contains: Wrapped fetch calls, endpoint definitions, auth header injection
- Key files: `http.js` (fetch wrapper), `index.js` (API client definitions)

**`frontend/src/components/`**
- Purpose: Reusable Vue components
- Contains: UI building blocks, form inputs, notifications
- Key files: `NotificationStack.vue` (toast notifications)

**`frontend/src/composables/`**
- Purpose: Vue composition utilities (logic to share across components)
- Contains: Custom hooks for common patterns
- Key files: `useNotifications.js` (notification composable)

**`frontend/src/router/`**
- Purpose: Vue Router configuration (if separate from main.js)
- Contains: Route definitions and navigation setup

**`frontend/src/stores/`**
- Purpose: Pinia state management
- Contains: Store definitions using Pinia's composition API
- Key files: `useGameStore.ts` (centralized collection state)

**`frontend/src/types/`**
- Purpose: TypeScript interfaces and type definitions
- Contains: Game, Platform, Price, Settings interfaces
- Key files: `index.ts` (main type exports)

**`frontend/src/utils/`**
- Purpose: Utility functions and helpers
- Contains: Formatting, calculations, localStorage helpers
- Key files: `uiPreferences.ts` (theme/sidebar state persistence)

**`frontend/src/views/`**
- Purpose: Page-level components (one per route)
- Contains: Full-page views for each application feature
- Key files: `GamesList.vue`, `GameDetail.vue`, `AddGame.vue`, `Stats.vue`, `PriceBrowser.vue`, `Settings.vue`, `Import.vue`, `Wishlist.vue`, `MoreMenu.vue`

**Project Root:**

**`data/`**
- Purpose: User-generated data directory
- Generated: Yes (created at runtime)
- Committed: No

**`uploads/`**
- Purpose: User-uploaded images and files
- Generated: Yes (images uploaded via UI)
- Committed: No

**`alembic/`** (root level if present)
- Purpose: Database migrations tracked at project root
- Generated: No (created by developer)
- Committed: Yes

## Key File Locations

**Entry Points:**

- `backend/main.py`: FastAPI application initialization and router setup
- `frontend/src/main.js`: Vue app creation, Pinia/Router setup, service worker registration
- `frontend/index.html`: HTML entry point, serves bundled Vue app

**Configuration:**

- `backend/.env`: Backend environment variables (secrets, API keys)
- `backend/.env` (root): Shared environment variables
- `frontend/vite.config.js`: Vite build configuration
- `frontend/tsconfig.json`: TypeScript compiler settings
- `docker-compose.yml`: Docker Compose for local development
- `Dockerfile`: Production container image definition

**Core Logic:**

- `backend/database.py`: Database connection, wrapper utilities, app metadata functions
- `backend/db/models.py`: All SQLAlchemy ORM models (Game, Platform, PriceHistory, etc.)
- `backend/db/session.py`: SQLAlchemy engine and SessionLocal factory
- `backend/services/lookup_service.py`: Multi-provider entity lookup and enrichment
- `backend/services/price/catalog.py`: Price catalog CRUD and platform scraping
- `frontend/src/stores/useGameStore.ts`: Pinia store with games/platforms state

**Testing:**

- `backend/tests/`: Test modules (layout mirrors backend/ structure)

## Naming Conventions

**Files:**

- Python: `snake_case.py` (e.g., `lookup_service.py`, `price_tracker.py`)
- Vue components: `PascalCase.vue` (e.g., `GamesList.vue`, `NotificationStack.vue`)
- TypeScript: `camelCase.ts` or `PascalCase.ts` depending on export type
- CSS files: `style.css` or component-scoped styles in `<style scoped>`

**Directories:**

- Python packages: `lowercase_with_underscores` (e.g., `price_providers`, `backend`)
- Vue directories: lowercase (e.g., `components`, `views`, `stores`)
- Logical groupings: feature-based (e.g., `api/routes/`, `services/price/`)

**Classes/Types:**

- Python: `PascalCase` (e.g., `Game`, `PriceHistory`, `LegacyDBWrapper`)
- TypeScript: `PascalCase` (e.g., `Game`, `Platform`)

**Functions/Variables:**

- Python: `snake_case` (e.g., `list_games()`, `get_db()`, `scheduled_price_update()`)
- JavaScript/TypeScript: `camelCase` (e.g., `gamesApi.list()`, `useGameStore()`)

**Constants:**

- Python: `UPPER_SNAKE_CASE` (e.g., `PLATFORM_SLUGS`, `CONSOLE_IMAGE_MAP`)
- JavaScript: `UPPER_SNAKE_CASE` or `camelCase` depending on scope

## Where to Add New Code

**New Feature (e.g., wishlist price alerts):**
- API endpoint: `backend/api/routes/settings.py` or new file `backend/api/routes/wishlist.py`
- Business logic: `backend/services/wishlist_service.py`
- Database: Add model to `backend/db/models.py`, create Alembic migration
- Frontend view: `frontend/src/views/WishlistAlerts.vue`
- Frontend store: Add action to `frontend/src/stores/useGameStore.ts`
- API client: Add endpoints to `frontend/src/api/index.js`

**New Component/Module:**
- Reusable component: `frontend/src/components/MyComponent.vue`
- Page component: `frontend/src/views/MyPage.vue`
- Route: Add to routes array in `frontend/src/main.js`
- Composition utility: `frontend/src/composables/useMyComposable.js`

**New External API Integration (e.g., new price provider):**
- Provider implementation: `backend/services/price/providers/newprovider.py`
- Export provider function in `backend/services/price/providers/__init__.py`
- Add route handler or integrate into `backend/price_tracker.py`
- Update settings to accept new API credentials via `backend/api/routes/settings.py`

**Utilities:**
- Shared frontend helpers: `frontend/src/utils/myutil.ts`
- Shared backend helpers: `backend/services/utils.py` or `backend/utils.py`
- Data transformation: `frontend/src/api/` for API-specific, `frontend/src/utils/` for general

## Special Directories

**`.planning/`**
- Purpose: GSD orchestrator documents and phase plans
- Generated: Managed by GSD system
- Committed: Yes

**`.claude/`**
- Purpose: Local Claude configuration and command definitions
- Generated: Created by user
- Committed: Yes (shared with team)

**`.github/workflows/`**
- Purpose: GitHub Actions CI/CD workflows
- Generated: No (created by developer)
- Committed: Yes

**`node_modules/`** (frontend/)
- Purpose: NPM dependencies
- Generated: Yes (`npm install`)
- Committed: No

**`.pytest_cache/`** (backend/)
- Purpose: Pytest cache directory
- Generated: Yes (created by test runner)
- Committed: No

**`dist/`** (frontend/)
- Purpose: Built/compiled frontend assets
- Generated: Yes (`npm run build`)
- Committed: No

**`__pycache__/`** (backend/)
- Purpose: Python bytecode cache
- Generated: Yes (created by Python runtime)
- Committed: No

**`.venv/`** (root)
- Purpose: Python virtual environment
- Generated: Yes (`python -m venv .venv`)
- Committed: No

---

*Structure analysis: 2026-03-16*
