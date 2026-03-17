# Feature Research

**Domain:** Multi-type personal collectibles tracker (games, anime figures, Funko Pops, vinyl, accessories)
**Researched:** 2026-03-17
**Confidence:** HIGH (codebase is fully mapped; competitor analysis from Discogs, MFC, HobbyDB, iCollect Everything, Pop Price Guide)

---

## Context: What Already Exists

The app already has a working foundation. This research focuses on **what's needed for the multi-type expansion milestone**, not rebuilding what works.

**Already working:**
- Game CRUD with IGDB metadata, cover caching, price tracking
- `item_type` field on the `games` table (`game`, `console`, `accessory`, `figure`, `funko`, `vinyl`, etc.)
- `hobbydb_id`, `mfc_id`, `comicvine_id` columns (added in latest migration)
- `cache_remote_cover()` helper — fetches remote URL, saves to `/uploads/`, returns stable local path
- `lookup_hobbydb_title()` and `lookup_mfc_title()` — both currently proxy via eBay search
- `ItemImage` table — multiple images per item with `is_primary` and `sort_order`
- Wishlist with `wishlist_max_price` per item

**Currently broken for non-game types:**
- HobbyDB and MFC search result images are raw external URLs — never run through `cache_remote_cover()`
- Schema has no type-specific fields (scale, character, series, manufacturer, funko_number, format, label)
- Search/filter in frontend is game-centric (platform-as-filter doesn't map to figures or vinyl)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete for the new item types.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Cached cover images for all item types | External URLs from MFC/HobbyDB break due to hotlink protection and expiry — the existing problem being solved | LOW | `cache_remote_cover()` already works; missing is calling it in the search-result/save path for non-game types |
| Stable local image URL returned from search results | Users see broken images immediately when adding a figure — kills trust in the lookup flow | LOW | Route handlers for IGDB already do this; the figure/funko/vinyl lookup paths skip this step |
| Display item type visually in the list | Without a type badge or icon, a mixed collection looks like one undifferentiated blob | LOW | `item_type` field exists; frontend needs to render it |
| Filter collection by item type | Users with 200+ items need to see "just my figures" or "just vinyl" — universally expected | MEDIUM | Requires frontend filter addition; backend `item_type` field is already queryable |
| Type-specific metadata fields persisted to DB | Anime figures need scale, manufacturer, character, series — these don't exist in schema yet | MEDIUM | Add nullable columns; only populate per type; existing fields (publisher = manufacturer, genre = series) are semantic mismatches that confuse the UI |
| Title search across all types | Core discovery flow — user types "Rem" and expects to find the Re:Zero figure | LOW | Already works; search is title-based today |
| Add item manually without external lookup | Lookup fails frequently for figures; user needs a fallback | LOW | Manual add already works for games; same form reused |
| Cover image upload for any item type | Lookup images are often wrong for figures (color variants, exclusive editions) | LOW | Already exists for games; just needs to work for figures/funko/vinyl |
| Wishlist for all item types | Users track wanted figures and vinyls, not just games | LOW | `is_wishlist` and `wishlist_max_price` already exist per item; frontend may assume "games only" |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable for this personal tool.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Type-aware search result display | Show scale + manufacturer for figures, pop number + series for Funko — not just a title list | MEDIUM | Requires frontend result card to conditionally render type-specific fields from lookup payload |
| Funko Pop number field | "Pop number" (#6, #449, etc.) is the primary identifier for Funko collectors — PPG and HobbyDB both surface this as a top-level field | LOW | Add `funko_number` column; parse from title during lookup (e.g., "Pop! Animation #449" → 449) |
| Figure scale field | Collectors always filter by scale (1/6, 1/7, 1/8, 1/4) — MFC treats it as a primary filter | LOW | Add `scale` column; populate from MFC API or user input |
| Character + series fields for figures | MFC's main organizational structure: character → series → figure. Separating "character" from "title" allows grouping | LOW | Add `character_name` and `series_name` columns; source from MFC or user input |
| Vinyl-specific format field | LP, 7", 12", EP, single — Discogs treats format as the top organizing axis for vinyl | LOW | Add `vinyl_format` or use existing `genre` field with a dedicated label; `format` column better |
| Value history tracks by item type | Stats page currently splits "games" vs "hardware" — extending to figure/funko/vinyl lets user see which category appreciates | MEDIUM | `value_history` table structure needs breakdown columns; or denormalize by type at snapshot time |
| Bulk image re-cache for existing items | Users may have saved items with broken external URLs before this fix — one-click "fix all images" is high-value recovery | LOW | The `enrich_all_covers` job pattern already exists; needs a variant that targets non-game types |
| Search results showing cached (not raw) images | Users pick metadata from a search results list — if thumbnails are broken, they can't identify the right figure | MEDIUM | Requires calling `cache_remote_cover()` at search result time, not just at save time; adds latency to lookup |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems in this context.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Dynamic/custom item types with user-defined fields | Collectors have endless edge cases — trading cards, LEGO, plushies | Full EAV schema or JSON blob field turns filtering, stats, and display into an unsolvable abstraction problem; PROJECT.md explicitly rules this out | Add hardcoded columns for the 3-4 known types now; revisit with strong use case later |
| Direct MFC/HobbyDB API integration | Better data fidelity than eBay fallback | MFC has no public API; HobbyDB requires registration and is inconsistently documented; eBay fallback is pragmatically correct for now | Document the eBay-as-fallback approach; improve field extraction from eBay response (aspects → scale, character, etc.) |
| Automatic image refresh on a schedule | Looks useful to keep covers current | Breaks user-applied manual overrides; wastes bandwidth; `cache_remote_cover()` is a write-once approach by design (only caches if file doesn't exist) | Only re-fetch images on explicit user action ("fix image") |
| Per-item condition grading rubric (Discogs-style) | Vinyl collectors want VG+/NM/M grades with separate media/sleeve grading | Requires a structured grading UI component that doesn't exist; existing `condition` field as free text already satisfies this need for a personal tool | Keep `condition` as free text; document the convention in UI placeholder text |
| Real MFC barcode lookup | Faster add flow for figures | MFC JAN codes require MFC API access which doesn't exist; UPCItemDB already handles barcodes generically and would find figures if in the DB | Use existing `lookup_upcitemdb_barcode()` path; no new integration needed |
| Social/community features (trade lists, showcase) | PPG and iCollect Everything offer this | This is explicitly a personal tool; multi-user scope is out | Stick to export (CSV already exists) as the sharing mechanism |

---

## Feature Dependencies

```
[Stable local cover URLs in search results]
    └──requires──> [cache_remote_cover() called at lookup time, not just save time]
                       └──requires──> [lookup routes for hobbydb/mfc pass through cache_remote_cover()]

[Type-specific metadata display]
    └──requires──> [Type-specific DB columns exist (scale, funko_number, character_name, series_name, vinyl_format)]
                       └──requires──> [Alembic migration adds columns]
                       └──requires──> [Lookup service extracts and returns these fields]
                       └──requires──> [Save route persists these fields]

[Filter by item type]
    └──requires──> [item_type field reliably set on all items]
    └──enhances──> [Type-specific metadata display]

[Value history by item type]
    └──requires──> [item_type reliably populated for all items]
    └──requires──> [value_history table extended with per-type breakdown columns]

[Bulk image re-cache]
    └──requires──> [Stable local cover URL mechanism works]
    └──enhances──> [items with existing broken external URLs get fixed]
```

### Dependency Notes

- **Stable local cover URLs requires lookup route changes:** The `lookup_hobbydb_title()` and `lookup_mfc_title()` routes return results immediately; calling `cache_remote_cover()` at that stage adds HTTP round-trip latency. Accept this tradeoff — broken images at add-time are worse than slow lookup.
- **Type-specific fields require migration before save route:** The save route (`POST /api/games`) will silently discard type-specific fields if columns don't exist in the schema. Migration must run first.
- **Filter by type is independent of metadata fields:** Can be shipped before type-specific fields exist; just filters on existing `item_type` values.

---

## MVP Definition

This is a subsequent milestone, not a greenfield app. MVP = "figures, Funko Pops, and vinyl are reliably addable with working images and correct metadata."

### Launch With (current milestone)

- [x] Fix broken HobbyDB/MFC search result images — call `cache_remote_cover()` in the lookup route handlers for these types (the core broken thing)
- [x] Harden collectible schema — add `scale`, `character_name`, `series_name`, `funko_number`, `vinyl_format` columns via migration
- [x] Stable local cover URLs in metadata search results — search result thumbnails must be served from `/uploads/` not raw external URLs
- [x] `item_type` reliably set on save — ensure the save path passes `item_type` correctly for figure/funko/vinyl adds
- [x] Display item type visually in collection list — badge or icon per item type

### Add After Validation (v1.x)

- [ ] Filter collection by item type — once the type field is reliably set on all items, add frontend filter
- [ ] Funko Pop number parsed from title — parse "Pop! #449" → `funko_number = 449` in lookup response
- [ ] Scale extracted from eBay aspects for figures — `localizedAspects` in eBay response often contains scale; extract it
- [ ] Type-aware search result display — figure cards show scale + manufacturer; Funko cards show number + series

### Future Consideration (v2+)

- [ ] Value history by item type — needs value_history schema change; defer until stats milestone
- [ ] Vinyl format field + vinyl-specific display — low user priority vs. figures and Funko for this owner
- [ ] Bulk image re-cache for all existing items — useful but not blocking; can be a settings-page button

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Cache images at lookup time (HobbyDB/MFC) | HIGH | LOW | P1 |
| Stable local cover URLs in search results | HIGH | LOW | P1 |
| `item_type` set correctly on save | HIGH | LOW | P1 |
| Type-specific DB columns (scale, funko_number, etc.) | HIGH | LOW | P1 |
| Item type badge/icon in list | MEDIUM | LOW | P1 |
| Filter by item type | HIGH | MEDIUM | P2 |
| Funko Pop number parsed from title | MEDIUM | LOW | P2 |
| Scale extracted from eBay aspects | MEDIUM | LOW | P2 |
| Type-aware search result cards | MEDIUM | MEDIUM | P2 |
| Bulk image re-cache job | MEDIUM | LOW | P2 |
| Value history by item type | MEDIUM | MEDIUM | P3 |
| Vinyl format field | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for this milestone
- P2: Should have, add when P1 is stable
- P3: Future milestone

---

## Competitor Feature Analysis

| Feature | MFC | HobbyDB/PPG | iCollect Everything | Discogs | Our Approach |
|---------|-----|-------------|---------------------|---------|--------------|
| Image source | Community uploads, CDN-hosted | Volunteer-maintained, CDN-hosted | Local device + iCloud | Community uploads, CDN-hosted | Cache external URLs locally on first fetch; reuse `cache_remote_cover()` |
| Type-specific fields | Scale, material, dimensions, JAN code, character, series, manufacturer | Variants/subvariants hierarchy, item type, UPC | Custom fields per collection type | Artist, label, catalog number, matrix, format, pressing plant | Hardcoded nullable columns per known type (scale, character_name, series_name, funko_number, vinyl_format) |
| Shared fields | Title, release date, publisher/brand, condition, purchase price, notes | Title, condition, purchase price, wishlist | Title, barcode, condition, location, price, notes | Title, year, condition, notes | Existing `games` table already has title, barcode, condition, purchase_price, notes — shared for all types |
| Cross-type search | Single-type site (figures only) | Multi-type but separate catalogs | Yes, unified search across all collection types | Single-type site (music only) | Title search already works across types; add `item_type` filter |
| Wishlist/wantlist | Wished / Ordered / Owned status | Want list | Wishlist tab per collection | Wantlist | `is_wishlist` field already exists per item |
| Value tracking | Manual + community prices | HobbyDB marketplace prices | Manual entry | Marketplace median prices | PriceCharting for games; eBay for others (already exists) |
| Barcode lookup | JAN codes | UPC/EAN | ISBN, barcode, OCR | Barcode via Discogs API | `lookup_upcitemdb_barcode()` exists; works generically |

---

## Type-Specific Metadata Reference

What each item type needs beyond the shared fields already in the `games` table.

### Anime Figures (item_type = "figure")
**Fields needed:** `character_name`, `series_name`, `scale`, `manufacturer`
- `character_name`: "Rem", "Miku Hatsune" — MFC's primary organizational axis
- `series_name`: "Re:Zero", "Vocaloid" — source property
- `scale`: "1/7", "1/8", "1/6", "Nendoroid", "figma" — primary filter for figure collectors
- `manufacturer`: "Good Smile Company", "Alter", "Kotobukiya" — stored as `publisher` today but semantically wrong
- Notes: `condition` field reused as-is (Mint in Box, Out of Box, etc.)

### Funko Pops (item_type = "funko")
**Fields needed:** `funko_number`, `series_name`
- `funko_number`: 449, 6, etc. — the Pop number printed on the box; primary identifier
- `series_name`: "Pop! Animation", "Pop! Movies", "Pop! Television" — line grouping
- `publisher` = "Funko" (hardcoded or from lookup)
- Notes: HobbyDB/PPG both treat exclusivity (Chase, Exclusive, Glow) as critical metadata; store in `condition` or `notes` for now

### Vinyl Records (item_type = "vinyl")
**Fields needed:** `vinyl_format`, `series_name` (as label/pressing info)
- `vinyl_format`: "LP", "7\"", "12\"", "EP", "Single" — format is how collectors organize
- `publisher` = record label (already fits)
- `developer` = repurposed as "artist" (already storing this way for existing items)
- Notes: Discogs-level granularity (matrix numbers, pressing plant) is anti-feature for a personal tool

### Games / Consoles / Accessories (item_type = "game"/"console"/"accessory")
**Already complete** — no new fields needed; existing schema is purpose-built for these.

---

## Image Handling Specifics

The current broken state and the fix approach:

**Problem:** `lookup_hobbydb_title()` and `lookup_mfc_title()` return eBay image URLs. These are served by eBay CDN with `imback.itm.ebayimg.com` or similar — no hotlink protection but URLs expire or rotate. Users see broken images in search results and in saved items.

**Fix (already in scope per PROJECT.md):**
1. Call `cache_remote_cover(image_url)` inside the lookup route handlers when building search results for hobbydb/mfc/vinyl
2. The helper downloads the image, saves to `/uploads/<sha1_hash>.<ext>`, and returns `/uploads/<filename>`
3. This stable local path is what gets returned to the frontend and stored in `cover_url`

**Tradeoff to accept:** Lookup response is slower (one extra HTTP request per result image). For a personal tool with 10-20 search results, this is acceptable (roughly 0.5-2s of added latency).

**What NOT to do:** Proxy images on-the-fly at display time (introduces dependency, adds complexity). Store image URLs directly from external sources and hope they stay valid (already proven not to work).

---

## Sources

- MFC FAQ and collection features: https://myfigurecollection.net/about/faq/
- iCollect Everything 2025 update: https://www.icollecteverything.com/2026/03/04/icollect-everything-mac-2025-update-ai-swiftui-trading-cards/
- Pop Price Guide / hobbyDB integration: https://blog.hobbydb.com/2025/03/24/pop-price-guide-now-fully-integrated/
- Discogs collection feature documentation: https://support.discogs.com/hc/en-us/articles/360007331534-How-Does-The-Collection-Feature-Work
- Discogs database guidelines (vinyl metadata fields): https://support.discogs.com/hc/en-us/articles/360005006614-Database-Guidelines-4-Label-Catalog-Number
- Funko Pop data schema reference: https://github.com/kennymkchan/funko-pop-data
- Codebase analysis: `B:/Code/collectabase/.planning/codebase/` (ARCHITECTURE.md, INTEGRATIONS.md, CONCERNS.md)

---

*Feature research for: multi-type collectible tracker expansion (games, anime figures, Funko Pops, vinyl)*
*Researched: 2026-03-17*
