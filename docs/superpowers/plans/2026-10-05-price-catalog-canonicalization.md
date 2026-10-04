# Price Catalog Canonicalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every catalog platform one stable key and one consistent user-facing label so catalog scraping, filtering, and price linking work regardless of historic casing or aliases.

**Architecture:** A backend platform catalog becomes the only source of scraper slugs, canonical labels, aliases, and normalizers. A reversible Alembic migration backfills a `platform_key` column; APIs accept keys or old display-label filters while the Vue client stops maintaining separate slug knowledge.

**Tech Stack:** Python, SQLite/Alembic, FastAPI, Vue 3.

**Spec:** `docs/superpowers/specs/2026-10-05-collectabase-stability-and-product-identity.md`

## Global Constraints

- Keep `price_catalog.platform` in responses for backwards compatibility.
- Preserve catalog rows unless identity is conclusively the same canonical platform plus non-empty PriceCharting ID.
- Unknown historic platform values remain searchable.
- Keep existing PriceCharting target and library-enrichment endpoints.

## Review Focus

- `PlayStation`, `playstation`, and `PS5` aliases resolve deterministically without changing unrelated records.
- Unknown source values such as `Arcade Cabinet` get a stable fallback key and readable label.
- A blank PriceCharting ID is never merged solely on title.
- Existing callers filtering with `platform=PlayStation 5` still receive results.
- Applying a normalized catalog row keeps current-value and price-history behavior unchanged.

---

### Task 1: Single platform catalog module

**Files:**
- Create: `backend/services/price/platforms.py`
- Modify: `backend/services/price/catalog.py`
- Modify: `backend/price_tracker.py`
- Test: `backend/tests/test_api_smoke.py`

**Interfaces:** `canonicalize_platform(value: str | None) -> PlatformIdentity` returns `key`, `label`, and `scraper_slug`. `platform_filter_values(value: str) -> tuple[str, str]` accepts a display label or key.

- [ ] **Step 1: Write normalization tests**

Add tests for `PlayStation`, `playstation`, `PS5`, `Nintendo Switch`, `nintendo switch`, `Xbox One`, and an unknown input. Assert stable key, expected label, and no empty key.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest backend.tests.test_api_smoke.PlatformCatalogTests -v`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement `PlatformIdentity` and alias table**

Move current `PLATFORM_SLUGS` ownership into the module. Include every existing scrape label and a deterministic slugified fallback. Update price tracker and scraper entry creation to use the module rather than local maps.

- [ ] **Step 4: Verify and commit**

Run: `python -m unittest backend.tests.test_api_smoke.PlatformCatalogTests -v`

Expected: PASS.

```bash
git add backend/services/price/platforms.py backend/services/price/catalog.py backend/price_tracker.py backend/tests/test_api_smoke.py
git commit -m "feat: centralize catalog platform identities"
```

### Task 2: Canonical migration and API filters

**Files:**
- Create: `backend/alembic/versions/f7a8b9c0d1e2_normalize_price_catalog_platforms.py`
- Modify: `backend/price_tracker.py`
- Modify: `backend/tests/test_api_smoke.py`

**Interfaces:** `price_catalog.platform_key` is indexed. `GET /api/price-catalog` accepts canonical `platform_key` and legacy `platform`. `GET /api/price-catalog/platforms` returns display labels and keys.

- [ ] **Step 1: Write migration fixture tests**

Seed `PlayStation`, `playstation`, and an unknown label. Run Alembic to head and assert canonical labels/keys, no unsafe blank-ID merge, and an index on `platform_key`. Exercise searches with label and key.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest backend.tests.test_api_smoke.PriceCatalogMigrationTests -v`

Expected: FAIL because `platform_key` and canonical filtering do not exist.

- [ ] **Step 3: Implement migration and query behavior**

Add nullable column, backfill through `canonicalize_platform`, canonicalize labels, safely merge matching non-empty PriceCharting IDs, then index the key. Make upsert, search, platform listing, deletion, targeted scrape, library enrichment, and catalog-to-game apply key-aware.

- [ ] **Step 4: Verify and commit**

Run: `python -m unittest backend.tests.test_api_smoke.PriceCatalogMigrationTests backend.tests.test_api_smoke.PriceCatalogApiTests -v`

Expected: PASS.

```bash
git add backend/alembic/versions/f7a8b9c0d1e2_normalize_price_catalog_platforms.py backend/price_tracker.py backend/tests/test_api_smoke.py
git commit -m "feat: normalize price catalog platforms"
```

### Task 3: Frontend catalog contract

**Files:**
- Modify: `frontend/src/api/index.js`
- Modify: `frontend/src/views/PriceBrowser.vue`
- Modify: `frontend/src/views/GameDetail.vue`

**Interfaces:** Catalog entries have `platform`, `platform_key`, and canonical filter options. Price-link requests retain the existing `catalog_id` payload.

- [ ] **Step 1: Locate duplicate platform knowledge**

Run: `rg "platformSlugs|PlayStation 5" frontend/src/views/PriceBrowser.vue`

Expected: existing local mapping is found.

- [ ] **Step 2: Render API-provided labels and keys**

Replace the local platform-slug map with catalog API options. Keep current search, scrape, link, and display flows, but send/compare canonical keys where present. Unknown labels remain visible.

- [ ] **Step 3: Verify and commit**

Run: `npm run build && npx vue-tsc --noEmit`

Expected: PASS.

```bash
git add frontend/src/api/index.js frontend/src/views/PriceBrowser.vue frontend/src/views/GameDetail.vue
git commit -m "feat: use canonical platforms in price browser"
```
