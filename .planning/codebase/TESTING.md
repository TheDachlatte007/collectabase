# Testing Patterns

**Analysis Date:** 2026-03-16

## Test Framework

### Backend

**Runner:**
- Python `unittest` (standard library)
- Config: No pytest.ini or setup.cfg (uses unittest discovery)
- TestClient from FastAPI for integration testing

**Test Location:**
- `backend/tests/test_api_smoke.py` - 317 lines of integration tests

**Run Commands:**
```bash
# Run all tests
python -m pytest backend/tests/
python -m unittest discover backend/tests/

# Coverage (if pytest-cov installed)
pytest --cov=backend backend/tests/
```

### Frontend

**Status:** No test framework detected
- No Jest config, Vitest config, or test files found
- No `*.test.js`, `*.spec.js`, or `*.test.ts` files in codebase
- Package.json has no test script or test dependencies

---

## Backend Test Structure

### Test File Organization

**Location:** `backend/tests/test_api_smoke.py`

**Class Structure:**
```python
class ApiSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One-time setup: temp DB, environment config, app initialization

    @classmethod
    def tearDownClass(cls):
        # One-time cleanup

    def test_core_routes(self):
        # Actual test method
```

### Setup & Teardown Patterns

**Class-level Setup (runs once per test class):**
- Creates temporary database: `tempfile.mkdtemp(prefix="collectabase_test_")`
- Sets environment variables:
  ```python
  os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
  os.environ["UPLOADS_DIR"] = uploads_dir.as_posix()
  ```
- Imports and initializes FastAPI app: `from backend.main import app`
- Creates test client: `cls.client = TestClient(app)`

**No Per-Test Teardown:**
- Tests are cumulative within same DB session
- Cleanup happens at `tearDownClass()`

### Test Suite Organization

**Smoke Test Coverage:**

The test suite validates core functionality across all major feature areas:

**1. Core Routes & CRUD:**
```python
def test_core_routes(self):
    # GET /
    r = self.client.get("/")
    self.assertEqual(r.status_code, 200)

    # POST /api/games (create)
    # GET /api/games/{id} (read)
    # PUT /api/games/{id} (update)
    # DELETE /api/games/{id} (delete)
    # GET /api/stats, /api/settings/info
```

**2. Error Cases:**
```python
def test_404_for_missing_game(self):
    r = self.client.get("/api/games/999999")
    self.assertEqual(r.status_code, 404)

def test_409_for_duplicate_game(self):
    # POST same game twice, expect conflict on second
```

**3. Query Filtering:**
```python
def test_games_filters(self):
    # Tests ?platform=X, ?wishlist=true, ?search=X
```

**4. Barcode Lookup:**
```python
def test_lookup_barcode_returns_existing_game(self):
    # Validates barcode normalization and existing game detection
```

**5. Price Fetching (with Mocking):**
```python
def test_fetch_market_price_uses_local_catalog_match(self):
    # Mocks external services, tests local price catalog fallback
```

---

## Assertion Patterns

### HTTP Status Assertions
```python
self.assertEqual(r.status_code, 200)
self.assertEqual(r.status_code, 404)
self.assertEqual(r.status_code, 409)
```

### Response Data Assertions
```python
self.assertEqual(r.json()["id"], game_id)
self.assertTrue(len(platforms) > 0)
self.assertIn("total_games", r.json())
```

### Conditional Assertions
```python
self.assertTrue(any(item["id"] == gid for item in response.json()))
self.assertFalse(any(item["id"] == gid for item in response.json()))
```

### Numeric Assertions
```python
self.assertAlmostEqual(float(data.get("market_price")), 24.49, places=2)
```

### Field Presence
```python
self.assertIn("error", data)
self.assertNotIn("market_price", data)
```

---

## Test Data & Fixtures

### Dynamic Test Data Creation

**Platform Selection:**
```python
def _platform_by_name(self, preferred: str):
    platforms = self.client.get("/api/platforms").json()
    wanted = preferred.strip().lower()
    for platform in platforms:
        if platform["name"].strip().lower() == wanted:
            return platform
    return platforms[0]
```

**Direct Database Insertion (for price catalog):**
```python
def _insert_price_catalog(self, *, title: str, platform: str, loose_eur: float):
    with sqlite3.connect(self._db_path()) as con:
        con.execute("""
            INSERT INTO price_catalog
                (pricecharting_id, title, platform, loose_eur, ...)
            VALUES (?, ?, ?, ?, ...)
        """)
        con.commit()
```

**Game Payloads:**
```python
payload = {
    "title": "Smoke Test Game",
    "platform_id": platforms[0]["id"],
    "item_type": "game",
    "is_wishlist": False,
}
game_id = self.client.post("/api/games", json=payload).json()["id"]
```

### Cleanup Pattern

Tests manually clean up created resources:
```python
# After test assertions
self.client.delete(f"/api/games/{game_id}")
self.client.delete(f"/api/games/{wid}")
```

---

## Mocking Patterns

### Unittest Mock Usage

**Imports:**
```python
from unittest.mock import AsyncMock, patch
```

**Example: Mock External Service**
```python
with patch(
    "backend.api.routes.lookup.lookup_upcitemdb_barcode",
    new=AsyncMock(return_value={"results": [], "error": None}),
):
    r = self.client.post("/api/lookup/barcode", json={"barcode": "4005209025098"})
```

**Example: Mock Multiple Async Functions**
```python
with (
    patch("backend.price_tracker._fetch_pricecharting_scrape", new=AsyncMock(return_value=None)),
    patch("backend.price_tracker.fetch_ebay_market_price", new=AsyncMock(return_value=None)),
    patch("backend.price_tracker.fetch_rawg_reference", new=AsyncMock(return_value=None)),
):
    r = self.client.post(f"/api/games/{game_id}/fetch-market-price")
```

### What to Mock

- External API calls (eBay, RAWG, UpcItemDb, PriceCharting scrapers)
- Third-party services that require credentials
- Async functions that would block tests

### What NOT to Mock

- Database operations (use real in-memory SQLite)
- FastAPI app and routing
- Internal business logic functions
- API client helper functions

---

## Test Types Detected

### Integration Tests (Primary)

**Scope:** Full request → response cycle
- Real database (temporary SQLite)
- Real FastAPI app and routing
- Real business logic
- Mocked external services only

**Example:**
```python
def test_core_routes(self):
    r = self.client.post("/api/games", json=payload)
    self.assertEqual(r.status_code, 200)
    game_id = r.json()["id"]

    r = self.client.get(f"/api/games/{game_id}")
    self.assertEqual(r.json()["id"], game_id)
```

### Unit Tests (None Detected)

- No isolated function/method tests found
- No tests for utilities or helper functions
- Price matching logic (`_lookup_local_catalog_price`) not directly tested

### E2E Tests (None Detected)

- No end-to-end test framework configured
- Only API-level testing, no UI automation

---

## Frontend Testing

### Current State: No Tests

**Missing:**
- No Jest, Vitest, or other test runner configured
- No test files (no `*.spec.js`, `*.test.ts`)
- No test dependencies in package.json
- No coverage reports

**Areas Not Tested:**
- Vue component rendering logic
- Pinia store actions and state mutations
- API client functions
- Composable hooks (useNotifications, useGameStore)
- Vue Router integration
- User interactions

### Recommended Testing Areas (if implemented)

**Components to Test:**
- `GamesList.vue` - Filter, search, sorting logic
- `GameDetail.vue` - Display and edit flows
- `AddGame.vue` - Form validation
- `Stats.vue` - Data aggregation and display
- `PriceBrowser.vue` - Price lookup and UI

**Stores to Test:**
- `useGameStore.ts` - Load, refresh, update, remove actions

**API Functions to Test:**
- All facade methods in `api/index.js`

**Composables to Test:**
- `useNotifications.js` - Notification lifecycle

---

## Coverage

### Backend

**Coverage Status:** Smoke tests only (no coverage metrics configured)

**Covered Routes:**
- `GET /` → SPA entry
- `GET /api/games` → list with filters
- `POST /api/games` → create
- `GET /api/games/{id}` → detail
- `PUT /api/games/{id}` → update
- `DELETE /api/games/{id}` → delete
- `GET /api/platforms` → list
- `POST /api/platforms` → create
- `POST /api/upload/cover` → file upload
- `POST /api/lookup/barcode` → barcode lookup
- `POST /api/games/{id}/fetch-market-price` → price fetch
- `GET /api/games/{id}/price-history` → history

**Not Covered:**
- Games image endpoints (add, delete, set primary)
- Import/export routes
- Settings/scheduler endpoints
- Stats aggregation endpoints
- Console fallback endpoints
- Most error paths and edge cases

### Frontend

**Coverage Status:** 0% (no tests)

---

## Running Tests

### Backend Only

```bash
# From project root
cd backend
python -m unittest discover tests/

# Or using pytest if installed
pytest tests/

# Run specific test
python -m unittest tests.test_api_smoke.ApiSmokeTest.test_core_routes
```

### Expected Output

```
test_core_routes (__main__.ApiSmokeTest) ... ok
test_404_for_missing_game (__main__.ApiSmokeTest) ... ok
test_409_for_duplicate_game (__main__.ApiSmokeTest) ... ok
...
----------------------------------------------------------------------
Ran 13 tests in 2.543s

OK
```

---

## Test Environment

### Database Setup

**Temporary Database:**
- Created per test class in system temp directory
- Path: `/tmp/collectabase_test_XXXXXX/games.db`
- Automatically deleted after tests complete

**Schema Initialization:**
- Alembic migrations run during app startup
- `init_db()` in `backend/main.py` triggers schema setup

### Environment Configuration

**Test-specific Variables:**
```python
os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
os.environ["UPLOADS_DIR"] = uploads_dir.as_posix()
```

**Inherited from `.env` files:**
- Any API keys needed (mocked in tests)

---

## Test Isolation

### Isolation Strategy

**Database Level:**
- Each test class gets fresh temp DB
- Tests within class share same DB (cumulative state)
- No per-test rollback/isolation

**Concerns:**
- Tests must clean up created resources manually
- Test execution order matters if tests are interdependent
- Side effects from one test can affect others

**Example:**
```python
# Test 1 creates game
r = self.client.post("/api/games", json=payload)
game_id = r.json()["id"]

# Test 2 (if run) would see game created in Test 1
# Unless explicitly cleaned up:
self.client.delete(f"/api/games/{game_id}")
```

---

## Common Test Patterns

### Testing Happy Path (Success Case)

```python
def test_core_routes(self):
    # 1. Get initial data
    r = self.client.get("/api/platforms")
    platforms = r.json()

    # 2. Create resource
    payload = {"title": "Test", "platform_id": platforms[0]["id"], ...}
    r = self.client.post("/api/games", json=payload)
    game_id = r.json()["id"]

    # 3. Verify created
    r = self.client.get(f"/api/games/{game_id}")
    self.assertEqual(r.json()["title"], "Test")

    # 4. Update
    updated = payload | {"title": "Updated"}
    r = self.client.put(f"/api/games/{game_id}", json=updated)
    self.assertEqual(r.status_code, 200)

    # 5. Delete & cleanup
    r = self.client.delete(f"/api/games/{game_id}")
    self.assertEqual(r.status_code, 200)
```

### Testing Error Cases

```python
def test_404_for_missing_game(self):
    r = self.client.get("/api/games/999999")
    self.assertEqual(r.status_code, 404)

def test_409_for_duplicate_game(self):
    # Create first
    first = self.client.post("/api/games", json=payload)
    self.assertEqual(first.status_code, 200)

    # Duplicate attempt fails
    second = self.client.post("/api/games", json=payload)
    self.assertEqual(second.status_code, 409)

    # Cleanup
    self.client.delete(f"/api/games/{first.json()['id']}")
```

### Testing with Mocks

```python
def test_fetch_market_price_uses_local_catalog_match(self):
    # 1. Insert test data
    self._insert_price_catalog(title="Test Game", platform="xbox one", loose_eur=24.49)

    # 2. Create game
    created = self.client.post("/api/games", json=payload)
    game_id = created.json()["id"]

    # 3. Mock external services
    with patch("backend.price_tracker._fetch_pricecharting_scrape", new=AsyncMock(return_value=None)):
        r = self.client.post(f"/api/games/{game_id}/fetch-market-price")

    # 4. Assert used local catalog
    data = r.json()
    self.assertEqual(data.get("source"), "pricecharting")
    self.assertAlmostEqual(float(data.get("market_price")), 24.49, places=2)

    # 5. Cleanup
    self.client.delete(f"/api/games/{game_id}")
```

---

*Testing analysis: 2026-03-16*
