# Storage and Backup Resilience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make persistent data, uploads, and portable backups explicit and independently located without breaking existing restores.

**Architecture:** Compose provides configurable bind-source variables while application code only sees stable container paths. Backup service keeps its SQLite snapshot and restore protections, expands the archive contract to include price catalog rows, and resolves a dedicated backup directory with a backward-compatible fallback.

**Tech Stack:** Docker Compose, FastAPI, SQLite, Python `zipfile`, Vue 3.

**Spec:** `docs/superpowers/specs/2026-10-05-collectabase-stability-and-product-identity.md`

## Global Constraints

- SQLite must remain on local container-host storage; never document SMB as a database host path.
- Preserve existing `data/backups/` restore compatibility.
- Provider credentials remain encrypted and opt-in; never export `ADMIN_API_KEY`.
- Backups now include `price_catalog` in manual and automatic archives.

## Review Focus

- An older archive whose manifest has `price_catalog_cache: false` still stages and restores.
- A backup with a catalog table but zero rows reports catalog inclusion accurately.
- An unset backup-directory variable retains the current `data/backups/` behavior.
- A configured backup directory is created before the first scheduled backup.
- Compose interpolation with a TrueNAS host path containing spaces is documented as one value.

---

### Task 1: Configurable persistent bind mounts

**Files:**
- Modify: `docker-compose.yml`
- Create: `stack.env.example`
- Modify: `README.md`
- Test: `backend/tests/test_api_smoke.py`

**Interfaces:** Produces `COLLECTABASE_DATA_DIR`, `COLLECTABASE_UPLOADS_DIR`, and `COLLECTABASE_BACKUP_DIR`; container paths remain `/app/data`, `/app/uploads`, and `/app/backups`.

- [x] **Step 1: Write a failing Compose configuration regression check**

Add a test that loads `docker-compose.yml` and verifies each source variable and container target appears exactly once.

- [x] **Step 2: Run the focused check**

Run: `python -m unittest backend.tests.test_api_smoke.TestDeploymentConfig`

Expected: FAIL because configurable source variables do not exist.

- [x] **Step 3: Implement explicit Compose mounts and example values**

Use long-syntax bind mounts or quoted interpolation so paths containing spaces are one source value. Add local defaults and `COLLECTABASE_BACKUP_DIR=/app/backups`. Add `stack.env.example` with local defaults plus a commented TrueNAS local-ZFS example. Update README and warn against SMB-backed SQLite.

- [x] **Step 4: Run the focused check**

Run: `python -m unittest backend.tests.test_api_smoke.TestDeploymentConfig`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add docker-compose.yml stack.env.example README.md backend/tests/test_api_smoke.py
git commit -m "feat: configure persistent storage paths"
```

### Task 2: Catalog-complete backup archives

**Files:**
- Modify: `backend/services/backup_service.py`
- Modify: `backend/api/routes/backups.py`
- Modify: `backend/tests/test_api_smoke.py`
- Modify: `frontend/src/views/Settings.vue`
- Modify: `README.md`

**Interfaces:** `create_backup()` manifests report `includes.price_catalog_cache: true`. `_backup_destination_dir() -> Path` resolves `COLLECTABASE_BACKUP_DIR` before legacy fallback.

- [x] **Step 1: Write failing catalog and destination tests**

Seed a catalog row and upload in the backup fixture. Assert archive and manifest retain the row, automatic backup writes under a patched `COLLECTABASE_BACKUP_DIR`, and a legacy `price_catalog_cache: false` manifest remains accepted.

- [x] **Step 2: Run focused tests**

Run: `python -m unittest backend.tests.test_api_smoke.Backup* -v`

Expected: FAIL because sanitization deletes `price_catalog` and automatic backups use only the database parent.

- [x] **Step 3: Preserve catalog data and resolve independent destination**

Remove catalog deletion from snapshot sanitization, add catalog count, report catalog inclusion in staged restore, and resolve `COLLECTABASE_BACKUP_DIR` when set. Keep encryption, ZIP limits, staged confirmation, and legacy parsing unchanged.

- [x] **Step 4: Update backup UI and documentation**

Replace statements that catalog data is excluded. Keep precise wording on encrypted provider credentials and never exporting `ADMIN_API_KEY`.

- [x] **Step 5: Verify and commit**

Run: `python -m unittest backend.tests.test_api_smoke -v`

Expected: PASS.

```bash
git add backend/services/backup_service.py backend/api/routes/backups.py backend/tests/test_api_smoke.py frontend/src/views/Settings.vue README.md
git commit -m "feat: include price catalog in portable backups"
```
