# Collector Workshop UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply a dark, technical, precise visual system that improves mobile PWA ergonomics and desktop scanability without replacing working collection flows.

**Architecture:** Refine existing design tokens and theme/density preferences instead of adding a UI framework. The shell owns navigation and safe-area behavior; views use shared surface, toolbar, status, action, and data-display conventions while retaining routes and API calls.

**Tech Stack:** Vue 3 Composition API, Vue Router, CSS custom properties, Vite.

**Spec:** `docs/superpowers/specs/2026-10-05-collectabase-stability-and-product-identity.md`

## Global Constraints

- Preserve current routes, buttons, API calls, theme choices, and density preference.
- Default identity is dark, technical, and precise; do not add an image-heavy showcase mode.
- Mobile forms are one column with no clipped interactive control at 360px.
- Wide price data may scroll horizontally; Lots must not rely on horizontal scrolling on mobile.

## Review Focus

- At 360px, bottom navigation and primary action remain reachable above safe-area inset.
- Keyboard focus is visible for sidebar, bottom-nav, form, and overflow-menu controls.
- Long titles and unknown platform labels do not overflow cards or action rows.
- Compact density reduces spacing without controls falling below 36px.
- Existing alternative palettes retain readable text and semantic states.

---

### Task 1: Shared Collector Workshop foundations and navigation

**Files:**
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/utils/uiPreferences.js`
- Modify: `frontend/src/views/Settings.vue`

**Interfaces:** Semantic tokens cover canvas, surface, raised surface, border, focus, info, success, warning, danger, and data typography. `setUiPrefs(next)` and current local-storage preference key remain unchanged.

- [ ] **Step 1: Add preference regression assertions and visual checklist**

Add a small utility test/check for unknown stored preferences falling back to `indigo`/`comfortable`. Add a documented 360px, 768px, and 1440px UI acceptance checklist.

- [ ] **Step 2: Record baseline quality gates**

Run: `npm run build && npx vue-tsc --noEmit`

Expected: PASS before visual changes.

- [ ] **Step 3: Refine tokens and shell behavior**

Replace generic glass-heavy defaults with solid layered surfaces, fine borders, focus states, semantic color tokens, and controlled shadows. Replace emoji navigation with consistent inline SVG icons. Retain four mobile navigation items, clear active text/indicator, and safe-area padding.

- [ ] **Step 4: Verify and commit**

Run: `npm run build && npx vue-tsc --noEmit`

Expected: PASS. Inspect 360px, 768px, and 1440px and record any clipping.

```bash
git add frontend/src/style.css frontend/src/App.vue frontend/src/utils/uiPreferences.js frontend/src/views/Settings.vue README.md
git commit -m "style: establish collector workshop foundations"
```

### Task 2: Collection, detail, and care interaction polish

**Files:**
- Modify: `frontend/src/views/GamesList.vue`
- Modify: `frontend/src/views/GameDetail.vue`
- Modify: `frontend/src/views/CollectionCare.vue`
- Modify: `frontend/src/utils/coverFallback.js`

**Interfaces:** Collection cards show title only once in their information region. Game Detail provides one visible primary action plus a labelled overflow menu for secondary actions.

- [ ] **Step 1: Capture core-flow visual baselines**

Use a local seeded database to capture collection, detail, and Collection Care at desktop and 360px. List expected actions: search, open item, edit, fetch/apply price, manual price, and care resolution.

- [ ] **Step 2: Implement card and action hierarchy**

Remove duplicate/truncated placeholder title rendering while keeping accessible fallbacks. Use a compact action bar: visible edit/primary action and menu for enrichment, external lookups, cover actions, and destructive-action confirmation. Give Care states a consistent status layout.

- [ ] **Step 3: Verify and commit**

Run: `npm run build && npx vue-tsc --noEmit`

Expected: PASS. Manually verify baseline actions on desktop and mobile.

```bash
git add frontend/src/views/GamesList.vue frontend/src/views/GameDetail.vue frontend/src/views/CollectionCare.vue frontend/src/utils/coverFallback.js
git commit -m "style: clarify collection and detail actions"
```

### Task 3: Responsive data views and supporting pages

**Files:**
- Modify: `frontend/src/views/PriceBrowser.vue`
- Modify: `frontend/src/views/LotsView.vue`
- Modify: `frontend/src/views/MoreMenu.vue`
- Modify: `frontend/src/views/Settings.vue`
- Modify: `frontend/src/views/AddGame.vue`
- Modify: `frontend/src/views/Import.vue`
- Modify: `frontend/src/views/Wishlist.vue`
- Modify: `frontend/src/views/Stats.vue`

**Interfaces:** Price Browser owns an intentional scroll region for wide data. Lots switch to compact expandable records at mobile breakpoint. Forms share a one-column mobile rule.

- [ ] **Step 1: Add viewport acceptance scenarios**

Create a checklist for 360px and 1440px covering catalog filter/search/link, Lot edit/save/sale, settings backup/restore, add-game search, import, wishlist CTA, and stats cards.

- [ ] **Step 2: Implement responsive data patterns**

Keep wide catalog columns but make overflow deliberate, keep query/filter controls outside scroll region, and use muted `N/A` for missing prices. Rework Lot rows into compact expandable mobile cards. Apply common toolbars, empty/status panels, form sections, and touch-safe action grouping across support views. Do not alter API behavior.

- [ ] **Step 3: Verify and commit**

Run: `npm run build && npx vue-tsc --noEmit`

Expected: PASS. Verify every scenario at 360px and 1440px with no page-level horizontal overflow.

```bash
git add frontend/src/views/PriceBrowser.vue frontend/src/views/LotsView.vue frontend/src/views/MoreMenu.vue frontend/src/views/Settings.vue frontend/src/views/AddGame.vue frontend/src/views/Import.vue frontend/src/views/Wishlist.vue frontend/src/views/Stats.vue
git commit -m "style: refine responsive collection workflows"
```
