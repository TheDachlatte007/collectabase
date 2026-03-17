# Project Research Summary

**Project:** Collectabase — Multi-Type Collectible Tracker
**Domain:** Personal collectibles management app (games, anime figures, Funko Pops, vinyl, comics)
**Researched:** 2026-03-17
**Confidence:** HIGH

## Executive Summary

Collectabase is an existing single-user personal collection tracker that works well for games but is partially broken for the non-game collectible types it was recently expanded to support. The core product design — a single `games` table with an `item_type` discriminator column, a Flask/Vue 3 stack, and a `cache_remote_cover()` image helper — is architecturally sound and does not need redesign. The milestone at hand is closing the gap between what the schema promises and what actually works: images break for figures and Funko Pops because the save path doesn't call `cache_remote_cover()`, and type-specific metadata fields (scale, funko_number, character_name, series_name) don't exist in the schema yet.

The recommended approach is strictly additive: wire `cache_remote_cover()` into the `create_game()` and `update_game()` route handlers, add a handful of nullable columns via an idempotent Alembic migration, extend the lookup service to pass type-specific fields through a `meta` dict, and conditionally render type-specific form sections in `AddGame.vue`. This sequence respects the established dependency chain: schema first, then backend image caching, then lookup service enrichment, then frontend form sections, then stats display. No new tables, no new modules, no renames.

The dominant risk is the one already biting the live app: external image URLs persisted to `cover_url` that expire or block hotlinking. The fix is a one-line guard in the save path. The secondary risk is Alembic migration crashes from duplicate column additions — the `_column_exists()` pattern from migration `b7c8d9e0f1a2` already solves this and must be followed for every future column addition. Both risks are low-cost to address and well-understood.

---

## Key Findings

### Recommended Stack

The stack is already decided and in production: Flask backend (described as FastAPI in architecture research — confirm actual framework in codebase), Vue 3 frontend with Pinia state management, SQLAlchemy models for Alembic migrations with raw `sqlite3` connections for query execution, and SQLite as the database. All external lookup sources (IGDB, eBay Browse API, ComicVine, UPCItemDB) are integrated and working. No new dependencies are required for this milestone.

**Core technologies:**
- Flask/backend: REST API, image upload handling, async route handlers for cover caching
- Vue 3 + Pinia: Single-page app, `useGameStore` manages all item state, `AddGame.vue` is the multi-type entry point
- SQLite via raw `sqlite3`: All route queries use raw SQL; SQLAlchemy ORM used only for migration introspection
- Alembic: Incremental `ADD COLUMN IF NOT EXISTS` migrations; `_column_exists()` guard is mandatory pattern
- eBay Browse API: Proxied as "HobbyDB" and "MFC" sources; eBay credentials required for non-game lookups

### Expected Features

**Must have (table stakes — current milestone):**
- Cache HobbyDB/MFC search result images at save time — `cache_remote_cover()` in `create_game()` and `update_game()`
- Type-specific DB columns — `scale`, `character_name`, `series_name`, `funko_number`, `vinyl_format` via migration
- `item_type` correctly set on save for figure/funko/vinyl items
- Stable local cover URL (`/uploads/...`) for every saved item regardless of source
- Item type badge/icon visible in collection list

**Should have (v1.x, after P1 is stable):**
- Filter collection by item type (frontend filter using existing `item_type` field)
- Funko Pop number parsed from eBay title string ("Pop! #449" → `funko_number = 449`)
- Scale extracted from eBay `localizedAspects` response for figure lookups
- Type-aware search result cards (figure cards show scale + manufacturer)
- Provider-to-item_type auto-suggestion (selecting MFC provider defaults item_type to "figure")

**Defer (v2+):**
- Value history breakdown by item type (requires `value_history` schema extension)
- Vinyl format field and vinyl-specific display (low priority vs. figures/Funko)
- Bulk image re-cache button in settings (useful repair tool, not blocking)
- Stats "by platform" query cleanup for non-game types

**Anti-features to avoid:**
- Dynamic/custom item types with user-defined fields (EAV trap — explicitly out of scope)
- Direct MFC or HobbyDB API integration (no public MFC API; HobbyDB inconsistently documented; eBay fallback is correct for now)
- Automatic image refresh on a schedule (breaks manual overrides; the write-once cache is correct by design)
- Per-item Discogs-style condition grading rubric (free-text `condition` field is sufficient for a personal tool)

### Architecture Approach

The existing architecture is a straightforward layered design: Vue 3 frontend talks to a REST backend, which dispatches to `lookup_service.py` for external API calls and writes to SQLite via raw SQL. All collectible types share the `games` table with an `item_type` discriminator — this Single-Table Inheritance design is correct and should not be changed. The only significant architectural gap is that `cache_remote_cover()` is wired to the enrich pipeline but not to the primary save path. The metadata normalization layer strips type-specific fields from lookup results; this should be extended with an optional `meta` dict pass-through rather than replaced.

**Major components:**
1. `lookup_service.py` — all external API calls + `cache_remote_cover()`; the reuse anchor for image caching
2. `games.py` route — CRUD handlers; must be extended to call `cache_remote_cover()` inline at save time
3. `AddGame.vue` — single form for all item types; extend with conditional type-specific sections controlled by `isGameType`/`isFigureType`/`isVinylType` computed helpers
4. `db/models.py` + `alembic/` — SQLAlchemy models for schema declaration; Alembic for incremental migrations with `_column_exists()` guards
5. `useGameStore.ts` — Pinia cache; invalidates on save; no optimistic updates

**Critical architectural constraint:** SQLAlchemy ORM and raw `sqlite3` connections coexist. Models in `models.py` are used only by Alembic — all route queries use raw SQL. New code must follow the raw SQL pattern; do not introduce ORM queries.

### Critical Pitfalls

1. **External image URLs saved without caching** — The live app already has this bug. Fix: call `cache_remote_cover(cover_url)` inside `create_game()` and `update_game()` gated on `cover_url.startswith(("http://", "https://"))`. Verify: `SELECT COUNT(*) FROM games WHERE cover_url LIKE 'http%'` returns 0 after adding any new item.

2. **Alembic migration crashes on duplicate columns** — Any `op.add_column()` without `_column_exists()` guard crashes on databases where the column already exists. Fix: copy the guard pattern from `b7c8d9e0f1a2`. Verify: run `alembic upgrade head` twice in a row with no error.

3. **SQLAlchemy model / Alembic migration drift** — Column added to `models.py` without a matching migration works on fresh DBs (where `create_all` ran) but fails on the production DB. Fix: write and test the migration immediately after every model change. Verify: `alembic current` reports `head`; manually confirm each new column exists in a migrated DB copy.

4. **"HobbyDB" and "MFC" sources are eBay in disguise** — Both lookup functions proxy to eBay Browse API. eBay image URLs are listing-specific and expire. The masking (`r["source"] = "hobbydb"`) hides this from the frontend. This makes image caching at save time mandatory, not optional.

5. **`platform_id` stats noise for non-game types** — The stats `by_platform` breakdown aggregates all platform-less items into a "No Platform" bucket, mixing figures, Funko Pops, and vinyl together. Do not tighten `platform_id` nullable constraint; address the stats display in a later polish phase.

---

## Implications for Roadmap

Based on research, the dependency chain is deterministic: schema must precede backend image caching, which must precede lookup service enrichment, which must precede frontend form changes. There is no phase reordering ambiguity.

### Phase 1: Schema Hardening
**Rationale:** Everything else depends on the columns existing. The save path silently discards type-specific fields if the DB columns aren't there. This is a non-negotiable prerequisite.
**Delivers:** `scale`, `character_name`, `series_name`, `manufacturer`, `funko_number`, `vinyl_format` columns in the `games` table; updated `models.py`, `schemas.py` (Pydantic), and `games.py` INSERT/UPDATE statements.
**Addresses:** Type-specific metadata fields (P1 feature); blocks type-aware form and lookup enrichment.
**Avoids:** Schema drift pitfall (migration written alongside model changes); duplicate column crash pitfall (`_column_exists()` guards required).
**Research flag:** Standard pattern — established migration guard pattern from `b7c8d9e0f1a2` is the template. No additional research needed.

### Phase 2: Inline Image Caching at Save Time
**Rationale:** This is the primary broken thing in the live app. Once the schema is correct, the image fix is a small change to two route handlers — but it must be done before frontend work so saved items always have stable local URLs.
**Delivers:** `create_game()` and `update_game()` in `games.py` call `cache_remote_cover()` for any incoming `cover_url` that starts with `http://` or `https://`. All newly saved items have `/uploads/...` URLs.
**Addresses:** Image caching (P1 feature); stable local cover URL (P1 feature).
**Avoids:** External URL expiry pitfall; eBay CDN URL TTL pitfall.
**Research flag:** No research needed — `cache_remote_cover()` exists and works; one call site to add.

### Phase 3: Lookup Service Enrichment (Meta Fields Pass-Through)
**Rationale:** Enables the frontend to populate type-specific form fields from search results. Requires Phase 1 schema columns to exist so the frontend knows where to put the data.
**Delivers:** `lookup_mfc_title()` and `lookup_hobbydb_title()` extended with a `meta` dict carrying `scale`, `character`, `series` (MFC) and `funko_number`, `series` (HobbyDB/eBay). Frontend `fillFromIgdb()` reads `result.meta` to populate type-specific inputs.
**Addresses:** Type-aware search result display (P2); scale extracted from eBay aspects (P2); Funko number parsed from title (P2).
**Avoids:** Normalization layer stripping type-specific fields.
**Research flag:** Low complexity — eBay response shape is already known from existing code. `localizedAspects` extraction for scale is a parsing exercise, not an API integration.

### Phase 4: Frontend Type-Specific Form Sections
**Rationale:** Depends on schema (Phase 1) for knowing which fields exist and lookup enrichment (Phase 3) for auto-populating them. The form extension is a conditional rendering change, not a new component.
**Delivers:** `AddGame.vue` with `isGameType`/`isFigureType`/`isVinylType` computed helpers; conditional form sections per type; provider-to-item_type auto-suggestion; item type badge in `GamesList.vue`.
**Addresses:** Display item type visually (P1); type-specific form sections; provider auto-suggestion (UX pitfall fix).
**Avoids:** Separate `AddFigure.vue`/`AddVinyl.vue` per-type views (anti-pattern confirmed by architecture research); `window.confirm()` overwrite warning (acceptable tech debt for now).
**Research flag:** No research needed — conditional rendering pattern is standard Vue 3; `v-if` on computed helpers is established practice.

### Phase 5: Stats and Display Polish (Deferred)
**Rationale:** Non-blocking for the core milestone. The `by_type` breakdown in `stats.py` already works; the `by_platform` "No Platform" noise is cosmetic. Value history by item type requires schema changes to `value_history` table — defer.
**Delivers:** Stats `by_platform` query filters or labels non-game "No Platform" items; completeness options filtered by `item_type`; search result `onerror` fallback for broken external thumbnail images.
**Addresses:** UX pitfalls (completeness options, stats noise); `platform_id` stats pitfall resolution.
**Avoids:** `value_history` schema changes without validation (premature).
**Research flag:** Standard Vue 3 and SQL patterns. No external API research needed.

### Phase Ordering Rationale

- Schema first because the save path silently discards unknown columns — no amount of frontend or backend work produces correct results without the columns.
- Image caching second because it fixes the live breakage that harms trust, and because it must be in place before frontend work triggers more saves from non-game lookups.
- Lookup enrichment third because the frontend form can only display what the backend returns; empty `meta` fields make the form work but with no auto-population.
- Frontend fourth because it depends on both schema (column names to bind) and lookup enrichment (data to populate from).
- Stats last because it is display polish on already-correct data, not a prerequisite for anything.

### Research Flags

Phases needing deeper research during planning:
- None for this milestone. All 5 phases operate on known code paths with well-understood patterns.

Phases with standard patterns (skip research-phase):
- **All phases:** Direct codebase inspection provides complete implementation clarity. The `_column_exists()` pattern, `cache_remote_cover()` integration point, `fillFromIgdb()` branching structure, and Vue 3 `v-if` conditional rendering are all established in the existing codebase. No third-party API research needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Stack is already decided and in production; no research uncertainty |
| Features | HIGH | Direct codebase inspection + competitor analysis (MFC, HobbyDB, Discogs, PPG); feature scope is tightly bounded |
| Architecture | HIGH | Based on direct file inspection of every relevant module; no inference |
| Pitfalls | HIGH | Pitfalls 1-3 are already-encountered issues documented in PROJECT.md; Pitfalls 4-5 are direct consequences of observed code patterns |

**Overall confidence:** HIGH

### Gaps to Address

- **eBay `localizedAspects` shape for scale/character extraction:** The architecture research recommends extracting `scale` and `character` from the eBay Browse API response's `localizedAspects` field. The exact field names in the eBay response for figure categories should be confirmed when implementing Phase 3 (inspect live eBay API response for a figure search to validate field names before writing the extraction logic).
- **Funko number regex reliability:** Parsing "Pop! Animation #449" → `449` from eBay title strings is regex-based and may miss variant title formats. Validate against 10-15 real eBay Funko listing titles before shipping.
- **Backend framework confirmation:** Architecture research notes "FastAPI" but the task context specifies "Flask". Confirm actual framework before writing route handler code in Phase 2 — the `async`/`await` pattern for `cache_remote_cover()` depends on this.

---

## Sources

### Primary (HIGH confidence)
- Direct inspection of `backend/services/lookup_service.py` — `cache_remote_cover()`, all lookup providers, normalization shape
- Direct inspection of `backend/api/routes/games.py` — CRUD handlers, confirmed absence of `cache_remote_cover()` in save path
- Direct inspection of `backend/alembic/versions/b7c8d9e0f1a2_add_collectible_metadata_columns.py` — `_column_exists()` guard pattern
- Direct inspection of `frontend/src/views/AddGame.vue` — form structure, `fillFromIgdb()` branching, provider selector
- Direct inspection of `frontend/src/stores/useGameStore.ts` — state management, refresh pattern
- `.planning/PROJECT.md` — project constraints, already-encountered issues

### Secondary (MEDIUM confidence)
- MFC FAQ and collection features: https://myfigurecollection.net/about/faq/
- Pop Price Guide / hobbyDB integration: https://blog.hobbydb.com/2025/03/24/pop-price-guide-now-fully-integrated/
- Discogs collection documentation: https://support.discogs.com/hc/en-us/articles/360007331534-How-Does-The-Collection-Feature-Work
- Funko Pop data schema reference: https://github.com/kennymkchan/funko-pop-data
- iCollect Everything 2025 update: https://www.icollecteverything.com/2026/03/04/icollect-everything-mac-2025-update-ai-swiftui-trading-cards/

### Tertiary (LOW confidence)
- eBay CDN URL TTL behavior — based on common knowledge of eBay image hosting; actual TTL varies by listing and CDN region; treat all eBay URLs as ephemeral regardless of observed behavior

---
*Research completed: 2026-03-17*
*Ready for roadmap: yes*
