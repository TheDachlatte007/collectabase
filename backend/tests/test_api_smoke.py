import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class ApiSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = Path(tempfile.mkdtemp(prefix="collectabase_test_"))
        db_path = tmp / "games.db"
        uploads_dir = tmp / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
        os.environ["UPLOADS_DIR"] = uploads_dir.as_posix()

        from backend.main import app

        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def _db_path(self) -> str:
        url = os.environ["DATABASE_URL"]
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "", 1)
        return url

    def _insert_price_catalog(self, *, title: str, platform: str, loose_eur: float):
        with sqlite3.connect(self._db_path()) as con:
            con.execute(
                """
                INSERT INTO price_catalog
                    (pricecharting_id, title, platform, loose_usd, cib_usd, new_usd,
                     loose_eur, cib_eur, new_eur, page_url, scraped_at, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    "",
                    title,
                    platform,
                    None,
                    None,
                    None,
                    float(loose_eur),
                    None,
                    None,
                    None,
                ),
            )
            con.commit()

    def _platform_by_name(self, preferred: str):
        platforms = self.client.get("/api/platforms").json()
        wanted = preferred.strip().lower()
        for platform in platforms:
            if platform["name"].strip().lower() == wanted:
                return platform
        return platforms[0]

    def test_core_routes(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/spa/route/test")
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/api/platforms")
        self.assertEqual(r.status_code, 200)
        platforms = r.json()
        self.assertTrue(len(platforms) > 0)

        payload = {
            "title": "Smoke Test Game",
            "platform_id": platforms[0]["id"],
            "item_type": "game",
            "is_wishlist": False,
        }
        r = self.client.post("/api/games", json=payload)
        self.assertEqual(r.status_code, 200)
        game_id = r.json()["id"]

        r = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], game_id)

        updated = payload | {"title": "Smoke Test Updated"}
        r = self.client.put(f"/api/games/{game_id}", json=updated)
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/api/stats")
        self.assertEqual(r.status_code, 200)
        self.assertIn("total_games", r.json())

        r = self.client.get("/api/settings/info")
        self.assertEqual(r.status_code, 200)
        self.assertIn("version", r.json())

        r = self.client.delete(f"/api/games/{game_id}")
        self.assertEqual(r.status_code, 200)

    def test_404_for_missing_game(self):
        r = self.client.get("/api/games/999999")
        self.assertEqual(r.status_code, 404)

    def test_409_for_duplicate_game(self):
        platforms = self.client.get("/api/platforms").json()
        payload = {
            "title": "Duplicate Test",
            "platform_id": platforms[0]["id"],
            "item_type": "game",
            "is_wishlist": False,
        }

        first = self.client.post("/api/games", json=payload)
        self.assertEqual(first.status_code, 200)
        game_id = first.json()["id"]

        second = self.client.post("/api/games", json=payload)
        self.assertEqual(second.status_code, 409)

        cleanup = self.client.delete(f"/api/games/{game_id}")
        self.assertEqual(cleanup.status_code, 200)

    def test_400_for_invalid_cover_upload(self):
        files = {"file": ("bad.txt", b"not-an-image", "text/plain")}
        r = self.client.post("/api/upload/cover", files=files)
        self.assertEqual(r.status_code, 400)

    def test_games_filters(self):
        platforms = self.client.get("/api/platforms").json()
        platform_id = platforms[0]["id"]

        game_payload = {
            "title": "Filter Test Game",
            "platform_id": platform_id,
            "item_type": "game",
            "is_wishlist": False,
        }
        wish_payload = {
            "title": "Filter Test Wishlist",
            "platform_id": platform_id,
            "item_type": "game",
            "is_wishlist": True,
        }

        g = self.client.post("/api/games", json=game_payload)
        w = self.client.post("/api/games", json=wish_payload)
        self.assertEqual(g.status_code, 200)
        self.assertEqual(w.status_code, 200)
        gid = g.json()["id"]
        wid = w.json()["id"]

        filtered_platform = self.client.get(f"/api/games?platform={platform_id}")
        self.assertEqual(filtered_platform.status_code, 200)
        self.assertTrue(any(item["id"] == gid for item in filtered_platform.json()))

        filtered_wishlist = self.client.get("/api/games?wishlist=true")
        self.assertEqual(filtered_wishlist.status_code, 200)
        self.assertTrue(any(item["id"] == wid for item in filtered_wishlist.json()))
        self.assertFalse(any(item["id"] == gid for item in filtered_wishlist.json()))

        filtered_search = self.client.get("/api/games?search=Filter Test Game")
        self.assertEqual(filtered_search.status_code, 200)
        self.assertTrue(any(item["id"] == gid for item in filtered_search.json()))

        self.client.delete(f"/api/games/{gid}")
        self.client.delete(f"/api/games/{wid}")

    def test_lookup_barcode_rejects_invalid_code(self):
        r = self.client.post("/api/lookup/barcode", json={"barcode": "123"})
        self.assertEqual(r.status_code, 400)

    def test_lookup_barcode_returns_existing_game(self):
        platform = self._platform_by_name("xbox one")
        payload = {
            "title": "Barcode Existing Test",
            "platform_id": platform["id"],
            "item_type": "game",
            "barcode": "4005209025098",
            "is_wishlist": False,
        }
        created = self.client.post("/api/games", json=payload)
        self.assertEqual(created.status_code, 200)
        game_id = created.json()["id"]

        with patch(
            "backend.api.routes.lookup.lookup_upcitemdb_barcode",
            new=AsyncMock(return_value={"results": [], "error": None}),
        ):
            r = self.client.post("/api/lookup/barcode", json={"barcode": "4005209025098"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("normalized_barcode"), "4005209025098")
        self.assertEqual(data.get("existing", {}).get("id"), game_id)

        self.client.delete(f"/api/games/{game_id}")

    def test_fetch_market_price_uses_local_catalog_match(self):
        xbox = self._platform_by_name("xbox one")
        title = "UT Local Match Xbox One White Wireless Controller"
        payload = {
            "title": title,
            "platform_id": xbox["id"],
            "item_type": "console",
            "is_wishlist": False,
        }
        created = self.client.post("/api/games", json=payload)
        self.assertEqual(created.status_code, 200)
        game_id = created.json()["id"]

        self._insert_price_catalog(
            title=title,
            platform=xbox["name"].lower(),
            loose_eur=24.49,
        )

        with (
            patch("backend.price_tracker._fetch_pricecharting_scrape", new=AsyncMock(return_value=None)),
            patch("backend.price_tracker.fetch_ebay_market_price", new=AsyncMock(return_value=None)),
            patch("backend.price_tracker.fetch_rawg_reference", new=AsyncMock(return_value=None)),
        ):
            r = self.client.post(f"/api/games/{game_id}/fetch-market-price")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("source"), "pricecharting")
        self.assertAlmostEqual(float(data.get("market_price")), 24.49, places=2)
        self.assertEqual(data.get("matched_title"), title)

        history = self.client.get(f"/api/games/{game_id}/price-history")
        self.assertEqual(history.status_code, 200)
        entries = history.json()
        self.assertTrue(any(e.get("source") == "pricecharting" for e in entries))

        self.client.delete(f"/api/games/{game_id}")

    def test_fetch_market_price_rejects_weak_local_match(self):
        xbox = self._platform_by_name("xbox one")
        payload = {
            "title": "UT Non Matching Device ZXQ-771",
            "platform_id": xbox["id"],
            "item_type": "console",
            "is_wishlist": False,
        }
        created = self.client.post("/api/games", json=payload)
        self.assertEqual(created.status_code, 200)
        game_id = created.json()["id"]

        self._insert_price_catalog(
            title="UT Totally Different Sports 2019",
            platform=xbox["name"].lower(),
            loose_eur=199.00,
        )

        with (
            patch("backend.price_tracker._fetch_pricecharting_scrape", new=AsyncMock(return_value=None)),
            patch("backend.price_tracker.fetch_ebay_market_price", new=AsyncMock(return_value=None)),
            patch("backend.price_tracker.fetch_rawg_reference", new=AsyncMock(return_value=None)),
        ):
            r = self.client.post(f"/api/games/{game_id}/fetch-market-price")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("error", data)
        self.assertNotIn("market_price", data)

        self.client.delete(f"/api/games/{game_id}")

    def test_fetch_market_price_prefers_same_platform_match(self):
        xbox = self._platform_by_name("xbox one")
        ps5 = self._platform_by_name("playstation 5")
        shared_title = "UT Multi Platform Shared Title"

        payload = {
            "title": shared_title,
            "platform_id": xbox["id"],
            "item_type": "console",
            "is_wishlist": False,
        }
        created = self.client.post("/api/games", json=payload)
        self.assertEqual(created.status_code, 200)
        game_id = created.json()["id"]

        self._insert_price_catalog(
            title=shared_title,
            platform=ps5["name"].lower(),
            loose_eur=77.00,
        )
        self._insert_price_catalog(
            title=shared_title,
            platform=xbox["name"].lower(),
            loose_eur=33.00,
        )

        with (
            patch("backend.price_tracker._fetch_pricecharting_scrape", new=AsyncMock(return_value=None)),
            patch("backend.price_tracker.fetch_ebay_market_price", new=AsyncMock(return_value=None)),
            patch("backend.price_tracker.fetch_rawg_reference", new=AsyncMock(return_value=None)),
        ):
            r = self.client.post(f"/api/games/{game_id}/fetch-market-price")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertAlmostEqual(float(data.get("market_price")), 33.00, places=2)
        self.assertEqual(data.get("matched_platform"), xbox["name"].lower())

        self.client.delete(f"/api/games/{game_id}")


if __name__ == "__main__":
    unittest.main()
