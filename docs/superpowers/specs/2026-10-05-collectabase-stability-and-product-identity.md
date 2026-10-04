# Collectabase Stability and Product Identity Specification

## Purpose

Make Collectabase dependable as a self-hosted personal collection archive while retaining every working collection, pricing, enrichment, Lots, and manual-entry workflow. The work must make a future TrueNAS/Portainer rebuild recoverable, preserve the local Price Browser data that took time to collect, and replace visually inconsistent PWA behavior with a dark, technical, precise product identity.

## Non-Negotiable Constraints

- Do not change existing API paths or remove existing user workflows.
- Do not delete collection records, price history, uploaded images, Lots, sales, or provider configuration during migrations or restore.
- SQLite must remain on a local Docker/TrueNAS filesystem, never on an SMB-mounted Windows drive.
- Existing `games.db` and legacy `data/backups/` archives must remain usable.
- Provider credentials remain opt-in, encrypted in manual backups only; `ADMIN_API_KEY` is never exported.
- The frontend remains a Vue PWA and must build with Node 20.
- Keep all interface text practical and avoid promises about third-party price or metadata quality.

## 1. Persistent Storage and Backup Resilience

### Explicit mount configuration

Compose must expose three configurable host paths:

- `COLLECTABASE_DATA_DIR` -> `/app/data`
- `COLLECTABASE_UPLOADS_DIR` -> `/app/uploads`
- `COLLECTABASE_BACKUP_DIR` -> `/app/backups`

The checked-in Compose file defaults to `./data`, `./uploads`, and `./backups` for local development. A tracked `stack.env.example` explains that TrueNAS/Portainer installations should use absolute local ZFS paths, not SMB shares and not Portainer's compose-directory default. This separates automated backups from the active database directory.

### Backup behavior

Manual and automatic portable ZIP backups contain `collection.sqlite`, all local uploads, all collection tables including `price_catalog`, and a manifest with table counts, upload totals, catalog presence, version, timestamp, and database checksum.

Automatic archives use the dedicated `COLLECTABASE_BACKUP_DIR` when set, falling back to the existing database-parent `backups/` directory for backward compatibility. Existing restore validation, staged confirmation, pre-restore archive, ZIP safety limits, and credential encryption remain unchanged. Settings and README state catalog inclusion and explain the configured backup destination without exposing server filesystem paths to untrusted callers.

## 2. Price Catalog Canonicalization

### Data contract

Price catalog records gain `platform_key`: a stable internal identifier such as `ps5`, `nintendo-switch`, or `xbox-one`. `platform` remains the user-facing canonical display label such as `PlayStation 5`, `Nintendo Switch`, or `Xbox One`.

A single backend platform catalog owns values, display labels, scraper slugs, aliases, and lookup normalization. Scraper results, targeted scraping, filters, catalog-to-game linking, and library enrichment use it. The frontend consumes API labels and keys instead of maintaining a second incompatible platform-slug map.

### Migration rules

The Alembic migration adds and indexes `price_catalog.platform_key`; derives keys and display labels case-insensitively; preserves unknown labels with deterministic fallback keys; merges only true duplicates sharing canonical key plus non-empty PriceCharting ID; and retains URLs, history links, and catalog IDs whenever a merge is unsafe.

Responses keep `platform` for backwards compatibility. New clients can pass `platform_key`; old display-label filters remain accepted.

## 3. Runtime and Static Asset Efficiency

Docker's frontend builder uses Node 20 and `npm ci`, matching CI. FastAPI uses a lifespan handler instead of deprecated events while retaining migration-before-server startup and health behavior.

Console fallback images remain local and offline-capable. A reproducible maintenance script creates appropriately sized WebP derivatives without cropping or overwriting originals. Legacy PNG/JPEG fallbacks keep working until references migrate. The runtime asset path should not retain unnecessarily large source images.

## 4. Collector Workshop Product Identity and Responsive UX

### Identity

The default interface remains dark, technical, and precise:

- deep navy/graphite base surfaces, not flat black;
- blue for navigation and information, limited semantic success/warning/error colors;
- restrained display type for headings and readable body type;
- monospace only for values, identifiers, dates, and dense data;
- solid layered surfaces and fine borders instead of generic glass on every element;
- existing optional palettes and density preference remain supported.

### Interaction rules

- Desktop prioritizes scanability and dense data.
- Mobile prioritizes reachable controls, one-column forms, safe-area spacing, and no clipped elements.
- Wide price tables may scroll horizontally; their search and filters remain independently usable.
- Lots use compact expandable item cards on mobile rather than wide tables.
- Game detail has one visible primary action plus a compact overflow menu for secondary actions.
- Empty, loading, error, and paused-scanner states use a consistent calm component language.

Apply the system first to the app shell, Collection list, Game Detail, Price Browser, Lots, Settings, More menu, and Collection Care. Preserve routes and actions. No showcase/social mode is part of this milestone.

## Acceptance Criteria

- Fresh Docker/Compose deployments can place data, uploads, and backups on explicit host paths.
- Manual and automatic backups restore a representative `price_catalog` entry and an uploaded cover.
- Historic raw catalog platform casing resolves to one display label and one key; filters and catalog-to-game linking work.
- Docker build, backend smoke/migration tests, frontend type check, and production build pass.
- The PWA is consistent at 360px, 768px, and desktop widths with no unintentional horizontal clipping.
- Existing settings/theme/density choices and core collection workflows continue to work.
