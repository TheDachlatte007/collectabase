# Coding Conventions

**Analysis Date:** 2026-03-16

## Language & Runtime Split

**Backend:** Python 3 with FastAPI
**Frontend:** JavaScript/TypeScript with Vue 3

---

## Naming Patterns

### Python (Backend)

**Files:**
- Snake case: `price_tracker.py`, `lookup_service.py`, `import_export.py`
- Modules grouped by feature: `backend/api/routes/*.py`, `backend/services/price/*.py`

**Functions/Methods:**
- Snake case: `fetch_market_price()`, `lookup_igdb_title()`, `_normalize_text()`
- Private helpers prefixed with underscore: `_get_game_for_price_lookup()`, `_should_use_console_placeholder()`

**Classes:**
- PascalCase: `GameCreate`, `GameUpdate`, `PlatformCreate`, `RowProxy`, `LegacyDBWrapper`
- Pydantic models inherit from `BaseModel`
- SQLAlchemy models inherit from `Base`

**Variables:**
- Snake case: `game_id`, `platform_name`, `existing_data`, `selected_platform`
- Constants in UPPER_CASE: `UPLOADS_DIR`, `CONSOLE_FALLBACKS_DIR`, `FALLBACKS_DIR`

### TypeScript/JavaScript (Frontend)

**Files:**
- PascalCase for Vue components: `GamesList.vue`, `GameDetail.vue`, `AddGame.vue`, `NotificationStack.vue`
- Camel case for utilities and composables: `useGameStore.ts`, `useNotifications.js`, `coverFallback.js`, `uiPreferences.js`
- Index files as barrel exports: `api/index.js`, `types/index.ts`

**Functions/Methods:**
- Camel case: `listGames()`, `createGame()`, `fetchMarketPrice()`, `parseJsonSafe()`, `withAdminHeaders()`
- Composable functions prefixed with `use`: `useGameStore()`, `useNotifications()` (Pinia + Vue 3 pattern)
- API facade methods: `gamesApi.list()`, `platformsApi.list()`, `lookupApi.combined()`

**Variables:**
- Camel case: `games`, `platforms`, `loading`, `selectedPlatform`, `filteredGames`, `brokenCoverIds`
- Refs with semantic names: `ref(false)` → `loading`, `ref({})` → `brokenCoverIds`

**Type Definitions:**
- PascalCase for interfaces: `Game`, `Platform`, `PriceEntry`, `Stats`, `ApiResponse<T>`

---

## Code Style

### Formatting

**Backend:**
- No explicit formatter configured (no `.prettierrc` or ESLint found)
- Import organization: stdlib → third-party → local modules
- Type hints used extensively: `def fetch_market_price(game_id: int) -> dict`
- Optional types: `Optional[int]`, `Optional[str]` or modern `int | None`
- Context managers for database access: `with get_db() as db:`

**Frontend:**
- No explicit linter/formatter configured
- Vue 3 Composition API with TypeScript support
- Vite build config in `vite.config.js` (no formatter rules)
- Import order: Vue/external → local components/stores → utils
- Template uses kebab-case for custom elements and directives

### Import Organization

**Backend (Python):**
```python
import os
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..errors import not_found
from ..database import get_db
from ...services.price.utils import normalize_text
```

Pattern: stdlib → third-party → relative imports (by depth)

**Frontend (JavaScript/TypeScript):**
```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gamesApi } from '../api'
import type { Game } from '../types'
```

Pattern: External packages → local imports → type imports

---

## Error Handling

### Backend Patterns

**Custom Exception Factory:**
- `api_error(status_code, message, code)` in `backend/api/errors.py`
- Helpers: `not_found()`, `bad_request()`, `conflict(extra=None)`
- Returns `HTTPException` with structured detail dict:
  ```python
  def not_found(message="Resource not found"):
      return api_error(404, message, "not_found")
  ```
- Used in route handlers: `raise not_found("Game not found")`

**Database Error Handling:**
- Catches `sqlite3.IntegrityError` for duplicate constraints
- Example: `except sqlite3.IntegrityError: raise conflict("Platform already exists")`

**Try/Finally for Resources:**
- Context managers for database cleanup: `with get_db() as db:`
- Explicit commit/rollback in transaction blocks

### Frontend Patterns

**Composable-based Error Handling:**
- Try/catch in async actions with error assignment: `catch (e: unknown) { error.value = e }`
- Notification system for user feedback: `notifyError()`, `notifySuccess()`
- Store-level error tracking: `error: ref<unknown>(null)` in `useGameStore`

**Response Validation:**
- Safe JSON parsing: `parseJsonSafe(res)` catches parse errors
- Status code checks before processing data: `if (!res.ok) return { ok: false, ... }`
- Type guards with `Array.isArray()` before assignment

---

## Logging

### Backend

**Framework:** `console.log`-style (Python standard library, no dedicated logger configured)

**Patterns:**
- Console logging in Vue composables: `console.error('[GameStore] Failed to load data:', e)`
- Service Worker registration: `navigator.serviceWorker.register('/sw.js').then(() => console.log('SW registered'))`

### Frontend

**Pattern:**
- Minimal logging (mostly for debugging)
- Error-specific logging: `console.error()` for failures
- Info logging: `console.log()` for lifecycle events

---

## Comments

### When to Comment

**Backend:**
- Class/function docstrings for public APIs:
  ```python
  class RowProxy:
      """Mimics sqlite3.Row – supports both dict-style and integer-style access."""
  ```
- Inline comments for complex logic:
  ```python
  # If deleted primary, pick another one
  next_img = db.execute(...).fetchone()
  ```
- Why comments, not what: `# exec_driver_sql passes raw SQL containing "?" directly to sqlite3`

**Frontend:**
- Sparse comments (code is self-documenting via TypeScript)
- Section dividers in Pinia stores:
  ```javascript
  // ── State ──────────────────────────────────────────────
  // ── Getters ────────────────────────────────────────────
  // ── Actions ────────────────────────────────────────────
  ```

---

## Module Design

### Barrel Files (Facade Pattern)

**Frontend API Layer** (`frontend/src/api/index.js`):
- Exports organized groups of endpoint methods
- Each group is an object with method references
- Examples:
  ```javascript
  export const gamesApi = { list, get, create, update, remove, ... }
  export const platformsApi = { list }
  export const lookupApi = { combined, barcode, consoleFallbacks, ... }
  ```

### Layered Architecture

**Backend:**
- `main.py` - FastAPI app setup, route registration, static file mounting
- `api/routes/*.py` - Route handlers (get, post, put, delete)
- `api/schemas.py` - Pydantic models for validation
- `api/errors.py` - Error helpers
- `database.py` - SQLAlchemy session management, legacy wrapper
- `db/models.py` - SQLAlchemy ORM models
- `services/` - Business logic (price lookups, scraping, etc.)

**Frontend:**
- `main.js` - Vue app initialization, router setup, service worker registration
- `stores/*.ts` - Pinia stores (state management)
- `api/*.js` - HTTP client and API facade
- `types/index.ts` - TypeScript interfaces
- `views/*.vue` - Page-level components
- `components/*.vue` - Reusable UI components
- `composables/*.js` - Shared Vue 3 composables
- `utils/*.js` - Standalone utilities

---

## Function Design

### Size & Scope

**Backend:**
- Route handlers stay focused (40-50 lines typical)
- Database queries isolated in helper functions
- Extraction example: `_get_game_for_price_lookup()` extracts repeated fetch logic

**Frontend:**
- Composables handle state + actions (20-30 lines)
- Computed properties derive filtered/sorted data
- Setup functions in Vue components organize refs/computed/watchers

### Parameter Conventions

**Backend:**
- Path parameters as positional: `def update_game(game_id: int, ...)`
- Optional query parameters with defaults: `async def list_games(platform: Optional[int] = None, ...)`
- Pydantic schemas for request bodies: `async def create_game(game: GameCreate, force: bool = False)`

**Frontend:**
- API functions take URL path + optional body
- Composables return object with state/actions: `return { games, platforms, load, refresh, ... }`

### Return Values

**Backend:**
- JSON-serializable dicts from route handlers
- Success pattern: `{"id": cursor.lastrowid, "message": "Game created successfully"}`
- Error pattern: Raises `HTTPException` (not returned)

**Frontend:**
- API functions return `{ ok, status, data }` object
- Store actions return `Promise<void>`
- Computed properties return typed values (filters, maps, etc.)

---

## Type Annotations

### Python

- Pydantic models for input validation (no type checking on GET params beyond implicit FastAPI parsing)
- Type hints on function signatures: `def execute(self, statement: str, parameters=None)`
- Optional types for nullable fields: `Optional[int]`, `Optional[str]`

### TypeScript

- Interfaces for data structures: `export interface Game { id: number; title: string; ... }`
- Generic types for API responses: `ApiResponse<T>`
- Type guards in store actions: `Array.isArray(gRes.data) ? (gRes.data as Game[]) : []`
- Ref typing: `const games = ref<Game[]>([])`

---

## Path Aliases

### Frontend tsconfig

- No aliases configured (imports use relative paths)
- Relative paths: `../api`, `../stores`, `../types`

### Backend

- No aliases (uses Python relative imports)
- Imports from root: `from backend.main import app`

---

## Testing Conventions

See TESTING.md for comprehensive testing patterns.

---

*Convention analysis: 2026-03-16*
