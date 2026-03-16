# Collectabase

## What This Is

A personal collection tracker that started with physical games and consoles, now expanding to support anime figures, Funko Pops, vinyl, and other collectible types. It pulls metadata from external sources (HobbyDB, MFC, IGDB) and lets you manage your collection with cover images, pricing info, and stats.

## Core Value

Reliably save and browse any collectible with accurate metadata and working images — regardless of the item type or data source.

## Requirements

### Validated

- ✓ Add and manage physical games and consoles — existing
- ✓ IGDB metadata lookup for games — existing
- ✓ Manual image upload for cover art — existing
- ✓ HobbyDB metadata lookup for collectibles — existing (images broken)
- ✓ MFC metadata lookup for anime figures — existing (images broken)
- ✓ Stats page with collection overview — existing (needs visual polish)
- ✓ Price catalog integration — existing

### Active

- [ ] Fix broken HobbyDB/MFC search result images by caching them locally
- [ ] Harden collectible schema — ensure all metadata fields are backed by migrations
- [ ] Stable local cover URLs in metadata search results instead of raw external URLs

### Out of Scope

- Universal collectible type system with dynamic tags — too complex for now, revisit later
- Stats page visual redesign — separate milestone
- Platform selection rework for non-game collectibles — future milestone
- Multi-user support — personal tool only

## Context

- Backend: Python (Flask/FastAPI), Alembic for migrations, SQLite/PostgreSQL
- Frontend: Vue.js (Vue 3)
- A recent migration fix resolved missing columns that broke saving collectibles
- `cache_remote_cover()` helper already exists and works for game covers
- HobbyDB and MFC return external image URLs that frequently break (hotlink protection, expiry)
- The codebase has been mapped via GSD (`/gsd:map-codebase`)

## Constraints

- **Scope**: Do not change core game-saving behavior that already works
- **Approach**: Reuse `cache_remote_cover()` — no new image pipeline
- **Migrations**: Only add migrations for fields actually used by the live save path
- **Personal tool**: No auth complexity, no multi-tenant concerns

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Cache external images locally via existing helper | External URLs break due to hotlink protection/expiry | — Pending |
| Expand schema incrementally per collectible type | Avoids big-bang migration, keeps things working | — Pending |
| Stats page polish deferred to separate milestone | Focus on data reliability first | — Pending |

---
*Last updated: 2026-03-16 after initialization*
