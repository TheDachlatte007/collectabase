# Runtime and Asset Efficiency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove avoidable runtime drift and make local console imagery efficient without losing offline fallback coverage.

**Architecture:** Docker matches CI's Node version and lockfile installation. FastAPI lifecycle is expressed through lifespan. A maintenance script generates WebP runtime derivatives safely and verifies no oversized raster remains in the served fallback directory.

**Tech Stack:** Docker, Node 20, FastAPI, Python, Pillow (maintenance-only).

**Spec:** `docs/superpowers/specs/2026-10-05-collectabase-stability-and-product-identity.md`

## Global Constraints

- Do not change static URLs consumed by existing covers until compatible derivative references exist.
- Do not add image processing dependency to the runtime image.
- Preserve startup migrations, scheduler initialization/shutdown, and `/api/health` behavior.

## Review Focus

- Missing frontend lockfile fails the container build rather than resolving different dependencies.
- Scheduler shutdown runs when FastAPI exits.
- A malformed image is reported and skipped without deleting source.
- Portrait artwork preserves aspect ratio and avoids crop.
- A legacy PNG/JPEG fallback URL remains served during transition.

---

### Task 1: Reproducible runtime build and lifespan

**Files:**
- Modify: `Dockerfile`
- Modify: `backend/main.py`
- Modify: `backend/tests/test_api_smoke.py`

**Interfaces:** Docker builder uses `node:20-alpine` and `npm ci`. FastAPI has an `@asynccontextmanager` lifespan that calls `init_db`, `init_scheduler`, and `shutdown_scheduler`.

- [x] **Step 1: Write lifecycle and Dockerfile checks**

Assert startup initializes database/scheduler once, shutdown delegates to scheduler shutdown, and Dockerfile specifies Node 20 plus `npm ci`.

- [x] **Step 2: Run focused checks to verify failure**

Run: `python -m unittest backend.tests.test_api_smoke.RuntimeConfigTests -v`

Expected: FAIL because deprecated event decorators and Node 18/npm install remain.

- [x] **Step 3: Implement lifespan and aligned build**

Use lifespan without changing router/static/SPA order. Change only frontend Docker stage to Node 20 and `npm ci`.

- [x] **Step 4: Verify and commit**

Run: `python -m unittest backend.tests.test_api_smoke.RuntimeConfigTests -v && docker build -t collectabase:runtime-check .`

Expected: PASS.

```bash
git add Dockerfile backend/main.py backend/tests/test_api_smoke.py
git commit -m "chore: align runtime build and application lifecycle"
```

### Task 2: Reproducible console fallback optimization

**Files:**
- Create: `scripts/optimize_console_fallbacks.py`
- Create: `scripts/requirements.txt`
- Modify: `README.md`
- Modify: `.gitignore`

**Interfaces:** `python scripts/optimize_console_fallbacks.py --source <dir> --output <dir> --check` outputs WebP with max long edge 1200px, preserves aspect ratio, and leaves sources untouched.

- [x] **Step 1: Write temporary-image optimizer tests**

Generate a portrait image, run script, assert WebP output, longest edge <=1200, and unchanged source checksum. Add invalid-file case that exits nonzero without deletion.

- [x] **Step 2: Run tests to verify failure**

Run: `python -m unittest backend.tests.test_api_smoke.ConsoleAssetOptimizerTests -v`

Expected: FAIL because script does not exist.

- [x] **Step 3: Implement non-destructive optimizer**

Use Pillow from `scripts/requirements.txt` only. Write explicit output directory via temporary output and atomic rename. Print per-file and total reduction. Ignore raw staging and generated temporary directories, not final served assets.

- [x] **Step 4: Process reviewed batch and verify**

Run against a copied source set, inspect portrait/landscape samples, then migrate only verified runtime assets/references. Do not delete source assets before visual verification.

Run: `npm run build && python -m unittest backend.tests.test_api_smoke.ConsoleAssetOptimizerTests -v`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add scripts/optimize_console_fallbacks.py scripts/requirements.txt README.md .gitignore backend/static/console-fallbacks
git commit -m "perf: optimize console fallback assets"
```
