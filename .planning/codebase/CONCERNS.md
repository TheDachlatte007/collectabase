# Codebase Concerns

**Analysis Date:** 2026-03-16

## Tech Debt

**Dead Code in price_tracker.py:**
- Issue: Lines 407-420 contain orphaned code with incomplete function definition and unreachable return statement. Code block marked with comment separator but contains no function body—appears to be a stub or merge artifact.
- Files: `backend/price_tracker.py` (lines 407-420)
- Impact: Maintainability issue; confusing for future developers. No runtime impact as code is unreachable.
- Fix approach: Remove the orphaned block (lines 407-420) entirely or complete the intended function implementation.

**Duplicate Import Statements in scheduler.py:**
- Issue: Lines 1-11 contain exact duplicate import statements (asyncio, logging, os, datetime, AsyncIOScheduler) appearing twice in sequence.
- Files: `backend/scheduler.py` (lines 1-11)
- Impact: Code smell; suggests merge conflict or accidental copy-paste. May confuse IDE analysis and imports.
- Fix approach: Remove duplicate lines 7-11, keeping only the first import block.

**Bare Exception Catch in price_tracker.py:**
- Issue: `except Exception:` without logging or handling in bulk price update fallback query (lines 224-234). Silently continues on database errors.
- Files: `backend/price_tracker.py` (lines 224-234)
- Impact: Silent failures; operators won't know if price updates failed due to schema changes. Missing is_wishlist column won't be caught.
- Fix approach: Add logging before fallback query; log actual exception details. Consider whether fallback behavior is intentional.

**Bare Exception Catch in catalog lookup:**
- Issue: `except Exception:` on line 53 in `_lookup_local_catalog_price()` returns None silently without logging.
- Files: `backend/services/price/catalog.py` (line 53)
- Impact: Silent failures in price matching. Errors are swallowed with no visibility into what went wrong.
- Fix approach: Log the exception at warning level before returning None. Include context (title, platform).

**Bare Exception Catch in CLZ Import:**
- Issue: `except Exception as e:` in platform creation (line 97) and game insert (line 129) only appends to error list. No broader error recovery.
- Files: `backend/clz_import.py` (lines 97, 129)
- Impact: Partial import failures may leave database in inconsistent state. Errors are collected but not analyzed systematically.
- Fix approach: Add transaction rollback on critical errors, or provide clearer error categorization (validation vs. database vs. integrity errors).

## Known Bugs

**Broken Return Statement in price_tracker:**
- Symptoms: Lines 407-420 contain unreachable code with `return response` statement, but `response` is never defined in the context. File would not pass linting.
- Files: `backend/price_tracker.py` (line 410)
- Trigger: Attempting to run or import this module may fail if Python actually tries to parse this orphaned code block.
- Workaround: Code is unreachable so runtime impact is minimal, but code should be removed.

**Missing is_wishlist Column Handling:**
- Symptoms: Bulk price update in `_run_bulk_price_update()` queries `is_wishlist` column and silently catches exceptions if column is missing (due to migration failure).
- Files: `backend/price_tracker.py` (lines 212-234)
- Trigger: If database schema migration fails or `is_wishlist` column is dropped, first query fails and fallback query runs without filtering wishlist items.
- Workaround: Ensure database migrations are applied before starting service.

## Security Considerations

**Proxy Header Trust Without Rate Limiting:**
- Risk: If `TRUST_PROXY_HEADERS` is enabled, admin access can be spoofed by setting `X-Forwarded-For` headers. No rate limiting on API key verification attempts.
- Files: `backend/api/security.py` (lines 27-40, 75-109)
- Current mitigation: Code uses `hmac.compare_digest()` for constant-time comparison; validates IP addresses via ipaddress module.
- Recommendations: (1) Add rate limiting to admin authentication endpoint. (2) Document that `TRUST_PROXY_HEADERS` should only be enabled when running behind a trusted proxy (load balancer, reverse proxy). (3) Consider requiring both IP whitelist AND API key if remote access is needed.

**SQL Injection Risk in Catalog Search (LOW RISK):**
- Risk: Lines 654-677 in `backend/price_tracker.py` construct SQL with string interpolation for sort column and order direction.
- Files: `backend/price_tracker.py` (lines 646-677)
- Current mitigation: Sort column is validated against allowlist (`allowed_sorts = {"title", "platform", "loose_eur", "cib_eur", "new_eur"}`). Order is validated to "ASC" or "DESC".
- Recommendations: Pattern is safe. No changes required, but document the validation pattern for future similar code.

**File Upload MIME Type Validation:**
- Risk: Upload endpoint validates MIME type but relies on client-provided `content_type`. An attacker could upload a malicious file with spoofed MIME type.
- Files: `backend/api/routes/import_export.py` (lines 18-46)
- Current mitigation: File size limit (5 MB) is enforced. Content-Type whitelist exists.
- Recommendations: (1) Add file magic number (file signature) validation using `magic` or `imghdr` library to verify actual file type, not just MIME header. (2) Consider running uploaded images through image sanitization library.

**Default Admin Mode (Local Only):**
- Risk: If `ADMIN_API_KEY` is not set, admin endpoints are accessible from any client on private/loopback IPs. In containerized environments, this may be overly permissive.
- Files: `backend/api/security.py` (lines 67-109)
- Current mitigation: Private/loopback IP check via ipaddress module. Proxy header trust is opt-in.
- Recommendations: In production, require explicit `ADMIN_API_KEY` configuration. Consider warning log when admin_key_configured is False.

## Performance Bottlenecks

**N+1 Query Pattern in Scheduled Price Update:**
- Problem: `scheduled_price_update()` in `backend/scheduler.py` (lines 51-79) loops through all non-wishlist games and calls `_lookup_local_catalog_price()` for each, which queries the catalog table up to 5 times per game.
- Files: `backend/scheduler.py` (lines 51-79), `backend/services/price/catalog.py` (lines 21-94)
- Cause: Sequential catalog lookups with broad search queries (up to 5000 rows per lookup) without indexing or batch queries.
- Improvement path: (1) Build in-memory index of catalog on startup. (2) Batch catalog lookups using UNION queries. (3) Add database indexes on `price_catalog(platform, title)` and `price_catalog(title)`. (4) Consider reducing limit from 5000 rows to more targeted range.

**Catalog Scrape Recursion Without Pagination Index:**
- Problem: `scrape_platform_catalog()` loops up to 400 pages (line 129) and fetches full page each time without caching or resuming from last position.
- Files: `backend/services/price/catalog.py` (lines 118-200)
- Cause: No pagination state tracking; if scrape is interrupted, restart fetches same data.
- Improvement path: (1) Store last scraped cursor/page in database. (2) Resume from checkpoint on restart. (3) Cache PriceCharting responses with ETags.

**Missing Database Indexes:**
- Problem: Queries in `price_tracker.py` and `catalog.py` search `price_catalog` table without indexes on frequently-queried columns.
- Files: Database schema not shown, but queries reference `platform`, `title`, `loose_eur`, `cib_eur`.
- Cause: No CREATE INDEX statements in migration files for catalog search queries.
- Improvement path: Add indexes: `CREATE INDEX idx_price_catalog_platform ON price_catalog(platform)`, `CREATE INDEX idx_price_catalog_title ON price_catalog(title)`, `CREATE INDEX idx_price_catalog_platform_title ON price_catalog(platform, title)`.

**Bulk Price Update Serialization:**
- Problem: `_run_bulk_price_update()` processes games sequentially (line 247-307) with 0.4s sleeps between PriceCharting requests.
- Files: `backend/price_tracker.py` (lines 242-314)
- Cause: Sequential processing with intentional delays to avoid hitting rate limits.
- Improvement path: (1) Batch requests to PriceCharting using async/await instead of sequential sleep. (2) Implement exponential backoff for 429 responses. (3) Parallelize catalog lookups with asyncio.gather(). (4) Consider queue-based approach with worker pools.

## Fragile Areas

**Price Lookup Matching Logic:**
- Files: `backend/services/price/catalog.py` (lines 21-94)
- Why fragile: Matching uses fuzzy string comparison with hardcoded score thresholds (0.55, 0.90, 0.92). Platform matching applies +0.10 bonus. Small changes to scoring rules break existing matches.
- Safe modification: (1) Add unit tests for each scoring case (exact match, partial match, no match, platform-aware). (2) Create matching strategy class with pluggable score calculators. (3) Add test fixtures with known good matches.
- Test coverage: Gaps in: platform mismatch handling, titles with special characters (é, ñ), platform abbreviations vs. full names.

**Barcode Lookup and Normalization:**
- Files: `backend/api/routes/lookup.py` (implicit barcode handling), `backend/services/lookup_service.py` (barcode validation)
- Why fragile: Barcode format validation is strict but database queries are lenient. A slight format change breaks lookups.
- Safe modification: (1) Add comprehensive test cases for barcode formats (EAN-13, UPC-A, ISBN-10, ISBN-13). (2) Normalize barcodes to canonical form on insert. (3) Create separate validation and normalization functions.
- Test coverage: Tests exist in `test_api_smoke.py` but only for basic format rejection. Missing: international barcode formats, leading zeros, checksum validation.

**Import Data Format Assumptions:**
- Files: `backend/clz_import.py` (lines 38-139), `backend/api/routes/import_export.py` (lines 49-224)
- Why fragile: CSV import relies on column name matching (e.g., "Title" vs "title" vs "item_type"). Date formats are guessed from multiple formats. Price parsing handles € and , but not other currency symbols.
- Safe modification: (1) Add strict validation of required columns before processing. (2) Define explicit column mapping schema. (3) Add pre-import validation report showing what will be imported.
- Test coverage: Gaps in: Unicode characters in titles, mixed-case column names, non-standard date formats.

**PriceCharting Scraper HTML Parsing:**
- Files: `backend/services/price/catalog.py` (lines 118-200)
- Why fragile: BeautifulSoup CSS selector `table#games_table` relies on PriceCharting DOM structure. If site redesigns, scraper breaks silently.
- Safe modification: (1) Add timeout and retry logic with exponential backoff. (2) Log HTML diff when parsing fails to help diagnose site changes. (3) Add optional override config with custom CSS selectors.
- Test coverage: No tests for scraper; relies on live PriceCharting data. Need: mocked HTML fixtures, parser error scenarios, edge cases (empty tables, missing columns).

## Scaling Limits

**SQLite Database:**
- Current capacity: SQLite is single-writer, suitable for single-user deployments with < 1M games.
- Limit: When collection exceeds 10k items or multiple concurrent users need admin access, SQLite will become bottleneck. Write contention under concurrent imports/price updates.
- Scaling path: (1) Migrate to PostgreSQL for multi-user support. (2) Use connection pooling (PgBouncer). (3) Add read replicas for stats queries.

**In-Memory Token Cache:**
- Current capacity: Single eBay token cached in memory (`_EBAY_TOKEN_CACHE`). If multiple FastAPI worker processes run, each has separate cache.
- Limit: Token expiry logic assumes single process; multiple workers won't share token, causing redundant eBay API calls.
- Scaling path: (1) Move token cache to Redis/Memcached. (2) Use APScheduler's persistent job store for distributed scheduling. (3) Implement token refresh endpoint that all workers check before making eBay calls.

**Scheduler Single Instance:**
- Current capacity: APScheduler runs in a single FastAPI worker process. If app scales to multiple workers, scheduled tasks run multiple times.
- Limit: Concurrent scheduled_price_update() jobs from different workers will duplicate work and cause database contention.
- Scaling path: (1) Move scheduler to dedicated service (separate Docker container/pod). (2) Use distributed lock (Redis/database) to ensure only one worker runs each job. (3) Use APScheduler with persistent job store and distributed locking.

**Asset Upload Directory:**
- Current capacity: File uploads stored in local `/uploads` directory. Suitable for < 100k images.
- Limit: In containerized/Kubernetes deployments, uploaded files are lost on pod restart. No cloud storage integration.
- Scaling path: (1) Move uploads to S3/Azure Blob Storage. (2) Use CloudFront/CDN for image caching. (3) Generate thumbnails asynchronously.

## Dependencies at Risk

**SQLAlchemy Version Mismatch:**
- Risk: `error.log` shows SQLAlchemy compatibility error: "Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly but has additional attributes". This indicates incompatibility between SQLAlchemy and Python 3.13.
- Impact: Application fails to import on some Python versions. Backend cannot start.
- Migration plan: (1) Upgrade SQLAlchemy to latest version (2.0+) if not already done. (2) Pin Python version to 3.11 or 3.12 in Dockerfile. (3) Run integration tests with multiple Python versions.

**httpx AsyncClient Connection Management:**
- Risk: Multiple AsyncClient instances created without cleanup in catalog scraping (`backend/services/price/catalog.py` line 128) and eBay lookup (`backend/services/price/providers/ebay.py` line 114). No connection pooling.
- Impact: Resource leaks under high concurrent load; socket exhaustion.
- Migration plan: (1) Use single shared AsyncClient instance with connection pool. (2) Implement proper context manager cleanup. (3) Add connection pool limits in httpx config.

**BeautifulSoup HTML Parser:**
- Risk: Uses default parser (may fall back to html.parser). No specified parser, behavior varies across environments.
- Impact: Scraper may fail silently on some systems if lxml is not installed.
- Migration plan: (1) Specify parser explicitly: `BeautifulSoup(html, "html.parser")` or `"lxml"` with it as a required dependency. (2) Add error handling for parser failures.

## Missing Critical Features

**No Monitoring/Observability:**
- Problem: No logging of price lookups, scraper health, or job execution except basic `print()` and logger calls. No metrics/tracing.
- Blocks: Cannot diagnose why price updates fail for specific items. Cannot track scraper success rates over time.
- Suggested approach: (1) Add structured logging (JSON) with context fields (game_id, title, source). (2) Export metrics to Prometheus (requests, successes, failures, latency). (3) Add distributed tracing with OpenTelemetry.

**No Data Validation Schema:**
- Problem: Game creation accepts data without consistent schema validation. Schemas exist (`GameCreate`, `GameUpdate`) but are not comprehensive.
- Blocks: Garbage data can be inserted. Edge cases (negative prices, future dates, invalid item types) pass through.
- Suggested approach: (1) Extend Pydantic schemas to validate ranges (0 <= price <= 100000). (2) Add custom validators for dates (not in future), item types (enum). (3) Document valid ranges in schema docstrings.

**No Soft Delete / Audit Trail:**
- Problem: Deleting games or price history entries removes data permanently. No audit log.
- Blocks: Cannot recover accidentally deleted items. Cannot track who changed what.
- Suggested approach: (1) Add `deleted_at` timestamp instead of hard delete. (2) Create audit_log table with (user, action, table, row_id, old_values, new_values, timestamp). (3) Add soft-delete flag to queries.

**No Bulk Error Recovery:**
- Problem: Bulk price update (`_run_bulk_price_update()`) silently skips items that fail to match or scrape. No report of which items were missed.
- Blocks: User doesn't know which items need manual price entry. Cannot retry failed items.
- Suggested approach: (1) Collect failed items in list. (2) Return detailed report with failed item IDs and reasons. (3) Implement job retry queue for failed items.

## Test Coverage Gaps

**Price Matching Logic:**
- What's not tested: Edge cases in `_catalog_match_score()` and matching thresholds. No tests for: special characters in titles, platform abbreviations, very short titles, very long titles.
- Files: `backend/services/price/catalog.py` (lines 21-94)
- Risk: Matching algorithm changes break silently. Regression in fuzzy matching not caught.
- Priority: **High** - affects core pricing feature.

**PriceCharting Scraper:**
- What's not tested: HTML parsing with various page layouts. No mocked fixtures; tests would require live scraping.
- Files: `backend/services/price/catalog.py` (lines 118-200)
- Risk: Site redesign breaks scraper; error is discovered in production, not in CI.
- Priority: **High** - scraper is critical external dependency.

**Scheduler Job Execution:**
- What's not tested: Concurrent job execution, job failure scenarios, scheduler state on app restart.
- Files: `backend/scheduler.py` (lines 22-84, 86-104)
- Risk: Scheduled jobs may run multiple times, skip runs, or fail silently.
- Priority: **Medium** - affects data freshness but not critical path.

**CSV/CLZ Import Validation:**
- What's not tested: Invalid date formats, non-numeric prices, missing required columns, encoding edge cases (BOM, latin-1).
- Files: `backend/clz_import.py`, `backend/api/routes/import_export.py`
- Risk: Import silently skips malformed rows without clear feedback to user.
- Priority: **Medium** - user-facing feature but rare error scenario.

**Frontend Component Error Boundaries:**
- What's not tested: Error states in large components (GameDetail, AddGame are 2000+ lines). No error boundary tests for missing API responses, network errors.
- Files: `frontend/src/views/GameDetail.vue` (2059 lines), `frontend/src/views/AddGame.vue` (1302 lines)
- Risk: UI crashes on API errors or slow network without graceful degradation.
- Priority: **Medium** - user experience issue but not data loss.

**Admin Authentication:**
- What's not tested: Proxy header spoofing, concurrent authentication attempts, token expiry edge cases.
- Files: `backend/api/security.py`
- Risk: Admin endpoint security not validated; could be bypassed in production.
- Priority: **High** - security feature must be tested.

---

*Concerns audit: 2026-03-16*
