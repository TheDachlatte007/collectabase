# Architecture Research

**Domain:** Personal multi-type collectible tracker (games, figures, Funko Pops, vinyl, comics)
**Researched:** 2026-03-17
**Confidence:** HIGH — based on direct codebase inspection, not inference

---

## Current Architecture (as-built)

Understanding what exists is the prerequisite for knowing what to change.

```
┌──────────────────────────────────────────────────────────────────┐
│                        Vue 3 Frontend                             │
├────────────────┬───────────────────────────────────────────────  ┤
│  Views         │  AddGame.vue / GamesList.vue / GameDetail.vue    │
│  Store         │  useGameStore.ts  (Pinia, all items unified)     │
│  API Layer     │  api/index.js  (gamesApi, lookupApi, etc.)       │
└────────────────┴──────────────────────┬───────────────────────── ┘
                                        │ HTTP
┌──────────────────────────────────────┴───────────────────────── ┐
│                    FastAPI Backend                                │
├───────────────┬───────────────────────────────────────────────── ┤
│  Routes       │  api/routes/games.py  (CRUD, images)             │
│               │  api/routes/lookup.py  (search, enrich, barcode) │
│               │  api/routes/stats.py                             │
│  Service      │  services/lookup_service.py                      │
│               │    cache_remote_cover()  ← the reuse anchor      │
│               │    lookup_igdb/rawg/gametdb/hobbydb/mfc()        │
│  Schema/DB    │  db/models.py  (Game, Platform, ItemImage, ...)  │
│               │  api/schemas.py  (Pydantic: GameCreate/Update)   │
│               │  database.py / db/session.py                     │
│  Migrations   │  alembic/versions/  (incremental ADD COLUMN)     │
└───────────────┴──────────────────────┬───────────────────────── ┘
                                        │ SQL
                    ┌───────────────────┴──────────────────┐
                    │       SQLite (collectabase.db)        │
                    │  games table  — single table,         │
                    │  item_type discriminator column        │
                    └──────────────────────────────────────┘
```

### What the Current Schema Is

The `games` table is already a **single-table inheritance** design with an `item_type` discriminator. All collectible types (game, console, figure, funko, comic, manga, misc) live in the same table. The schema has:

- Universal fields: title, cover_url, condition, completeness, location, purchase_price, current_value, notes, is_wishlist
- Source ID columns per lookup service: igdb_id, comicvine_id, hobbydb_id, mfc_id
- Game-centric fields that overlap other types: publisher, developer, genre, release_date, region
- Image gallery: separate `item_images` table, FK to games.id

---

## Schema Design: The Right Approach for This App

### Three Canonical Patterns and Why Single-Table Is Already Correct Here

**Single-Table Inheritance (STI)** — one table, discriminator column
- All item types in `games`, `item_type` = 'game' | 'figure' | 'funko' | 'comic' | etc.
- Null columns for fields that don't apply to a given type
- Pros: simple queries, no joins, easy stats across the whole collection
- Cons: many nullable columns as types accumulate
- **This is what Collectabase already uses. It is the right choice.**

**Class Table Inheritance (CTI)** — base table + per-type extension tables
- `items` base table + `items_game`, `items_figure`, `items_vinyl` extension tables joined by FK
- Pros: type-specific columns are not-null enforced, no sparse rows
- Cons: every query requires a JOIN, migrations require two tables, cross-type stats get complex
- **Not worth the complexity for a personal tool with ~8 item types**

**Entity-Attribute-Value (EAV)** — metadata as key/value rows
- `item_attributes (item_id, key, value)` instead of typed columns
- Pros: infinitely extensible without schema changes
- Cons: terrible query performance for filtering/stats, no type safety, complex application logic
- **PROJECT.md explicitly calls this "out of scope — too complex." Confirmed correct call.**

### Recommendation: Extend STI Incrementally

The active milestone requires adding a handful of columns to support non-game collectible metadata that the save path actually uses. The pattern already established — `ADD COLUMN IF NOT EXISTS` via Alembic — is correct. Continue it.

**What columns to add per type:**

| Type | Missing fields that matter | Notes |
|------|---------------------------|-------|
| figure / funko | manufacturer, scale, character, series | "publisher" already maps to brand |
| vinyl | label, catalog_number, format (LP/7"/12") | genre already exists |
| comic | issue_number, volume, series | publisher already exists |
| game | already fully covered | — |

Rather than a separate table per type, add these as nullable columns to `games` with a migration that uses `_column_exists()` guard (established pattern in `b7c8d9e0f1a2`).

---

## Image Caching Pipeline

### Current State

`cache_remote_cover(url)` in `lookup_service.py` is a fully working async function that:
1. Fetches the remote URL with httpx
2. Derives a filename from `sha1(url)` + content-type extension
3. Writes to `UPLOADS_DIR` (idempotent — skips if file exists)
4. Returns `/uploads/{filename}`

It is called today at:
- `POST /api/games/{id}/enrich` — on demand per item
- `POST /api/enrich/all` — background bulk job
- `POST /api/games/{id}/cover-placeholder` — console images

### The Gap: HobbyDB and MFC Search Results

The lookup endpoints (`/api/lookup/hobbydb`, `/api/lookup/mfc`) return raw external image URLs in their results. These external URLs are displayed in the search result thumbnails in `AddGame.vue` before an item is saved. They frequently break due to hotlink protection on eBay CDN.

The fix is to cache the image at the point the search result is returned, before the URL reaches the frontend, OR to cache it at the point the item is saved. Caching at save time is simpler and matches how game covers are handled.

### Recommended Pipeline for Non-Game Types

```
User selects search result (hobbydb/mfc)
    ↓
fillFromIgdb() sets game.value.cover_url = external_url
    ↓
saveGame() POSTs to /api/games (create) or /api/games/{id} (update)
    ↓
Backend route receives cover_url
    ↓
call cache_remote_cover(cover_url)  ← REUSE EXISTING HELPER
    ↓
Store /uploads/{sha1_hash}.jpg
    ↓
Persist /uploads/... to games.cover_url
```

This means `cache_remote_cover()` must be called inside the create/update route handlers for any item that arrives with an http(s) cover URL. The game routes currently do NOT do this inline — they rely on the separate `/enrich` endpoint. For non-game types there is no enrich endpoint today, so inline caching at save time is the correct addition.

### Component Boundary: Image Pipeline

```
lookup_service.cache_remote_cover()
    └── called by:
        ├── lookup.py  (enrich endpoints — existing)
        └── games.py   (create/update — TO ADD for non-game items)
```

No new module required. No new pipeline. One call site added.

---

## Metadata Normalization Layer

### Current State

All lookup sources return results in a normalized shape defined in `lookup_service.py`:

```python
{
  "source": "igdb" | "rawg" | "hobbydb" | "mfc" | "comicvine" | ...,
  "title": str,
  "cover_url": str | None,
  "release_date": str | None,
  "publisher": str | None,
  "description": str | None,
  # source-specific IDs: igdb_id, hobbydb_id, mfc_id, comicvine_id
}
```

The `_merge_lookup_results()` function deduplicates across sources by (title, source, platform) key.

### The Gap: Source-Specific Fields Are Normalized Away

MFC returns figure scale, manufacturer, character name — but those fields are stripped during normalization to fit the common shape. HobbyDB (currently eBay-backed) returns brand as `publisher` which is a reasonable mapping but loses category/series data.

### Recommended Normalization Approach: Pass-Through Extra Fields

Rather than inventing a new normalization layer, extend the result dicts to carry type-specific extras as an optional `meta` dict:

```python
# In lookup_mfc_title():
results.append({
    "source": "mfc",
    "title": ...,
    "cover_url": ...,
    "publisher": brand,            # normalized common field
    "meta": {                      # type-specific passthrough
        "scale": item.get("scale"),
        "character": item.get("character"),
        "series": item.get("series"),
    }
})
```

The frontend `fillFromIgdb()` already has per-source branching (`if result.source === 'mfc'`). It can read `result.meta` fields and populate type-specific form inputs when those columns exist in the schema.

This is additive and does not break the existing normalization contract for common fields.

---

## Frontend: Handling Type-Specific Fields

### Current State

`AddGame.vue` is a single large form with:
- A provider selector (`combined` / `comicvine` / `hobbydb` / `mfc`) that changes which lookup API is called
- `item_type` dropdown that changes whether platform is required
- All fields rendered regardless of item type
- Per-source branching in `fillFromIgdb()` to apply different fields depending on `result.source`

The form is already multi-type aware. The `item_type` value drives behavior in exactly one place today: `platform` required-ness.

### Recommended Pattern: Conditional Section Rendering

The cleanest extension for type-specific fields is conditional sections based on `game.item_type`, not separate views:

```vue
<!-- Shown for all types -->
<div class="form-group">Title, Cover, Condition, etc.</div>

<!-- Shown only for game / console / accessory -->
<div v-if="isGameType" class="form-group">
  <label>Platform</label>
  <label>Region</label>
  <label>Developer</label>
</div>

<!-- Shown only for figure / funko -->
<div v-if="isFigureType" class="form-group">
  <label>Manufacturer</label>
  <label>Scale</label>
  <label>Character</label>
  <label>Series</label>
</div>

<!-- Shown only for vinyl -->
<div v-if="isVinylType" class="form-group">
  <label>Label</label>
  <label>Format</label>
  <label>Catalog Number</label>
</div>
```

This avoids separate Add/Edit views per type while keeping the form navigable. Computed helpers group item types:

```js
const isGameType = computed(() =>
  ['game', 'console', 'controller', 'accessory'].includes(game.value.item_type)
)
const isFigureType = computed(() =>
  ['figure', 'funko'].includes(game.value.item_type)
)
const isVinylType = computed(() => game.value.item_type === 'vinyl')
```

### Provider-to-Type Auto-Suggestion

When a user selects a search provider, suggest the matching `item_type` pre-selection:

| Provider selected | Suggest item_type |
|-------------------|-------------------|
| hobbydb | funko |
| mfc | figure |
| comicvine | comic |
| combined | game (keep current) |

This is a UX affordance, not a hard lock. The user can still override.

---

## Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `AddGame.vue` | Item creation and editing form, metadata search UI, barcode scan | `gamesApi`, `lookupApi`, `platformsApi`, `useGameStore` |
| `GamesList.vue` | Collection list, filtering by type/platform/wishlist | `useGameStore` (cached) |
| `GameDetail.vue` | Item detail view, image gallery, price history | `gamesApi`, `priceApi` |
| `useGameStore.ts` | Pinia cache for all items + platforms, cross-view state | `gamesApi`, `platformsApi` |
| `api/index.js` | HTTP client wrappers, API contract boundary | FastAPI backend |
| `games.py` route | CRUD for items + images, inline cover caching (to add) | `lookup_service`, `database` |
| `lookup.py` route | Metadata search dispatch, enrich-on-demand | `lookup_service` |
| `lookup_service.py` | All external API calls + `cache_remote_cover()` | IGDB, RAWG, GameTDB, HobbyDB/eBay, MFC/eBay, ComicVine, UPCItemDB |
| `db/models.py` | SQLAlchemy ORM models | Alembic, all routes |
| `alembic/` | Schema migrations | SQLite/PostgreSQL |

---

## Data Flow

### Adding a Non-Game Collectible (Happy Path)

```
User types figure name in AddGame search
    ↓
Select provider: "Anime Figures (MFC)"
    ↓
lookupApi.mfc(title)  →  POST /api/lookup/mfc
    ↓
lookup_mfc_title()  →  _lookup_ebay_search_title()  →  eBay API
    ↓
Results returned with external image URLs (may be hotlink-protected)
    ↓
User clicks result  →  fillFromIgdb(result)
    ↓
game.value populated: title, cover_url (external), item_type='figure', mfc_id
    ↓
User submits  →  saveGame()  →  POST /api/games
    ↓
create_game() route receives cover_url = "https://i.ebayimg.com/..."
    ↓
[TO ADD] cover_url = await cache_remote_cover(cover_url)
    ↓
INSERT INTO games (..., cover_url='/uploads/abc123.jpg', item_type='figure', ...)
    ↓
useGameStore.refresh()  →  GamesList shows new item with cached cover
```

### Image Cache Hit Flow

```
Second item with same external cover URL is added
    ↓
cache_remote_cover(url) called
    ↓
sha1(url) → filename → path.exists() → True
    ↓
Return /uploads/{filename} immediately (no HTTP fetch)
```

### Lookup Search Flow (Metadata Normalization)

```
SearchProvider selected + title entered
    ↓
lookupApi[provider](title)  →  POST /api/lookup/{provider}
    ↓
lookup_service dispatches to external API
    ↓
Response normalized to common shape + optional meta dict
    ↓
Results returned to frontend with cover_url (external)
    ↓
AddGame.vue renders thumbnails (external URLs, may break in search UI)
    ↓
User selects result  →  fillFromIgdb() applies fields per source
    ↓
Save triggers cover caching
```

Note: cover URLs in the search result list (before save) still point to external URLs. That is acceptable — the breakage only matters for saved items.

---

## Suggested Build Order

Based on dependency analysis of the above:

### Step 1: Schema — Add Type-Specific Columns

**Prerequisite for everything else.** Without the columns, save paths have nowhere to store type-specific metadata.

- Add Alembic migration: `manufacturer`, `scale`, `character_name`, `series_name` (figures/funko), `vinyl_label`, `vinyl_format`, `catalog_number` (vinyl)
- Follow established `_column_exists()` guard pattern from `b7c8d9e0f1a2`
- Update `db/models.py` columns
- Update `api/schemas.py` Pydantic models (GameCreate/GameUpdate)
- Update `api/routes/games.py` INSERT and UPDATE statements

### Step 2: Backend — Inline Cover Caching at Save Time

**Prerequisite for reliable images.** Must happen before frontend changes, otherwise images break on save.

- In `create_game()`: call `cache_remote_cover(game.cover_url)` before INSERT if URL is external
- In `update_game()`: same, if cover_url changed and is external
- These are the only two code paths where a cover URL gets persisted
- No new modules. No new routes.

### Step 3: Lookup Service — Pass-Through Meta Fields

**Prerequisite for rich field population in the form.**

- Extend `lookup_mfc_title()` and `lookup_hobbydb_title()` to include a `meta` dict with type-specific fields recovered from eBay response (brand, category, etc.)
- No changes to the normalization contract for common fields

### Step 4: Frontend — Type-Specific Form Sections

**Depends on Steps 1 and 3.**

- Add `isGameType`, `isFigureType`, `isVinylType` computed helpers to `AddGame.vue`
- Conditionally render type-specific field groups
- Extend `fillFromIgdb()` per-source branching to populate `meta` fields into type-specific form inputs
- Add provider-to-item_type suggestion when provider selector changes
- Update `src/types/index.ts` `Game` interface with new columns

### Step 5: Stats — Type-Aware Grouping

**Depends on Step 1 (item_type data being accurate).**

- Stats already has `by_type` query in `stats.py` — this works today
- With more distinct item types, the `by_type` breakdown becomes more useful
- No schema changes needed; this is display logic in `Stats.vue`

---

## Architectural Patterns

### Pattern 1: Single-Table Type Discrimination

**What:** One `games` table with `item_type` column. All types coexist. Nullable columns for type-specific fields.
**When to use:** Personal tools, fewer than ~15 types, queries span all types (stats, search, list).
**Trade-offs:** Simple queries, easy stats, some nullable column sprawl. For this app, the sprawl will be ~8-10 new columns — entirely manageable.

### Pattern 2: Inline Cover Caching at Persistence Layer

**What:** `cache_remote_cover()` called inside the route handler that persists the item, not in a separate background job.
**When to use:** When you want guaranteed local URLs for every saved item without a second step.
**Trade-offs:** Adds ~100-500ms to each save request (network fetch). For a personal tool with one user this is fine. The function already handles failures gracefully by returning the original URL.

**Example (Python):**
```python
# In create_game():
if game.cover_url and str(game.cover_url).startswith(("http://", "https://")):
    game.cover_url = await cache_remote_cover(game.cover_url)
```

### Pattern 3: Per-Source Branching in Frontend Fill

**What:** `fillFromIgdb(result)` already branches on `result.source` to apply source-specific fields. New types extend this with additional `else if` blocks.
**When to use:** When each source has a distinct field mapping.
**Trade-offs:** Linear growth in `fillFromIgdb()` as sources are added. Acceptable — the function is already ~60 lines of branching and it's straightforward. A source registry (map of source → field mappings) could replace it if sources grow beyond ~8, but that is premature for now.

---

## Anti-Patterns

### Anti-Pattern 1: Separate Views Per Item Type

**What people do:** Create `AddFigure.vue`, `AddVinyl.vue`, `AddComic.vue` each duplicating the save/upload/barcode logic.
**Why it's wrong:** The save path, barcode scanner, cover upload, and metadata search are identical across all types. Duplicating them creates 4x the bugs to fix.
**Do this instead:** Conditional sections within `AddGame.vue` controlled by `item_type`. The form is already doing this for `platform` required-ness.

### Anti-Pattern 2: Background-Only Cover Caching

**What people do:** Only cache covers via the `POST /api/enrich/all` background job, not at save time.
**Why it's wrong:** Items saved from HobbyDB/MFC searches get persisted with external URLs that expire within hours. Users see broken images until the next enrich run.
**Do this instead:** Cache inline at save time as the primary path. The bulk enrich job remains as a repair tool for existing items.

### Anti-Pattern 3: EAV for Type-Specific Fields

**What people do:** Add an `item_attributes (item_id, key, value)` table to avoid schema changes for new types.
**Why it's wrong:** Stats queries (`GROUP BY item_type`, `SUM(value)`) become joins against a key/value table. Filtering by `scale = '1/7'` requires a subquery. For a small number of well-known types, typed columns are strictly better.
**Do this instead:** `ADD COLUMN` via Alembic migration with `_column_exists()` guard.

### Anti-Pattern 4: Renaming the Table

**What people do:** Rename `games` to `items` or `collectibles` to make the schema "correct" for multi-type support.
**Why it's wrong:** Requires migration of every foreign key (`item_images.game_id`, `price_history.game_id`), every route, every schema, every query, and the frontend `gamesApi` — for zero functional benefit. The name is internal implementation detail.
**Do this instead:** Leave the table named `games`. The `item_type` column already makes all items equal. Rename only if the team changes and new people are confused.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| IGDB (Twitch) | OAuth2 client credentials, cached in-process | Token cached in `_igdb_token_cache` dict; refreshed on expiry |
| RAWG | API key, simple GET | Key from env via `_env_any()` |
| GameTDB | No auth, XML response | Parse with `xml.etree.ElementTree` |
| eBay Browse API | OAuth2 client credentials (via `get_ebay_token`) | Used as backend for both HobbyDB and MFC lookups |
| ComicVine | API key, JSON | Key from env |
| UPCItemDB | Optional API key (free tier without) | Barcode lookup |
| HobbyDB | Currently eBay-backed, results masked with `source='hobbydb'` | Real HobbyDB API not integrated |
| MFC | Currently eBay-backed, results masked with `source='mfc'` | Real MFC API not integrated |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `AddGame.vue` ↔ `useGameStore` | Direct Pinia store call — `useGameStore().refresh()` after save | Only invalidates, does not patch optimistically on create |
| `games.py` ↔ `lookup_service.py` | Direct async function call | `await cache_remote_cover(url)` — no queue, no worker |
| Routes ↔ Database | `get_db()` context manager returns raw `sqlite3.Connection` | Not SQLAlchemy ORM — SQLAlchemy models exist but routes use raw SQL |
| Frontend ↔ Backend | REST over HTTP, no WebSocket, no SSE | Background jobs polled via `GET /api/jobs/{job_id}` |

Note on the ORM vs raw SQL split: `db/models.py` defines SQLAlchemy ORM models used only by Alembic for migrations and inspection. All actual queries in routes use raw `sqlite3.Connection` from `database.py`. This is a known inconsistency — do not introduce ORM queries in new code without awareness of this split.

---

## Scalability Considerations

This is a personal tool. Scalability is not a concern. The relevant scale is: one user, hundreds to low thousands of items.

| Concern | At current scale | Notes |
|---------|-----------------|-------|
| Query performance | Indexed on platform_id, item_type already in GROUP BY | No optimization needed |
| Image storage | SHA1-named flat directory in uploads/ | Fine for thousands of images |
| External API rate limits | IGDB: 4 req/s, eBay: 5000/day | Acceptable for personal use |
| Background jobs | In-process dict (`jobs.py`), no persistence | Restarts lose job state; acceptable |

---

## Sources

- Direct inspection of `backend/db/models.py` (schema structure)
- Direct inspection of `backend/services/lookup_service.py` (image caching, normalization)
- Direct inspection of `backend/api/routes/games.py` (CRUD, image management)
- Direct inspection of `backend/api/routes/lookup.py` (enrich pipeline)
- Direct inspection of `frontend/src/views/AddGame.vue` (form structure, fillFromIgdb branching)
- Direct inspection of `frontend/src/stores/useGameStore.ts` (state management)
- Direct inspection of `frontend/src/api/index.js` (API boundaries)
- Direct inspection of `backend/alembic/versions/b7c8d9e0f1a2_*.py` (migration pattern)
- `.planning/PROJECT.md` (constraints, key decisions)

---
*Architecture research for: Collectabase multi-type collectible support*
*Researched: 2026-03-17*
