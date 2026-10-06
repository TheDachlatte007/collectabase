import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import closing
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestDeploymentConfig(unittest.TestCase):
    def test_compose_exposes_independent_persistent_host_paths(self):
        compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"
        compose = compose_path.read_text(encoding="utf-8")

        self.assertIn("COLLECTABASE_DATA_DIR", compose)
        self.assertIn("COLLECTABASE_UPLOADS_DIR", compose)
        self.assertIn("COLLECTABASE_BACKUP_DIR", compose)
        self.assertIn("target: /app/data", compose)
        self.assertIn("target: /app/uploads", compose)
        self.assertIn("target: /app/backups", compose)

    def test_runtime_uses_ci_node_version_and_lifespan(self):
        root = Path(__file__).resolve().parents[2]
        dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
        main = (root / "backend" / "main.py").read_text(encoding="utf-8")

        self.assertIn("FROM node:20-alpine", dockerfile)
        self.assertIn("RUN npm ci", dockerfile)
        self.assertIn("lifespan=lifespan", main)
        self.assertNotIn("@app.on_event", main)


class TestDatabaseConfiguration(unittest.TestCase):
    def test_database_url_environment_override_is_used_outside_docker(self):
        configured_url = "sqlite:////tmp/collectabase-configured.db"
        environment = os.environ | {"DATABASE_URL": configured_url}
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from backend.db.session import get_database_url; print(get_database_url())",
            ],
            capture_output=True,
            check=True,
            cwd=Path(__file__).resolve().parents[2],
            env=environment,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), configured_url)


class PlatformCatalogTests(unittest.TestCase):
    def test_known_aliases_and_unknown_platforms_have_stable_identities(self):
        from backend.services.price.platforms import canonicalize_platform, get_known_platforms

        self.assertEqual(canonicalize_platform("PlayStation").key, "playstation")
        self.assertEqual(canonicalize_platform("playstation").label, "PlayStation")
        self.assertEqual(canonicalize_platform("PS5").key, "playstation-5")
        self.assertEqual(canonicalize_platform("Nintendo Switch").label, "Nintendo Switch")
        self.assertEqual(canonicalize_platform("nintendo switch").key, "nintendo-switch")
        self.assertEqual(canonicalize_platform("Xbox One").key, "xbox-one")
        unknown = canonicalize_platform("Arcade Cabinet")
        self.assertEqual(unknown.key, "arcade-cabinet")
        self.assertEqual(unknown.label, "Arcade Cabinet")

        known = get_known_platforms()
        self.assertTrue(len(known) > 10)
        self.assertTrue(any(p.key == "playstation-5" for p in known))
        self.assertTrue(any(p.scraper_slug == "nintendo-switch" for p in known))


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
        with closing(sqlite3.connect(self._db_path())) as con:
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
            "location": "Archive Shelf A",
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

        filtered_location = self.client.get("/api/games?search=Archive Shelf A")
        self.assertEqual(filtered_location.status_code, 200)
        self.assertTrue(any(item["id"] == gid for item in filtered_location.json()))

        locations = self.client.get("/api/locations")
        self.assertEqual(locations.status_code, 200)
        self.assertTrue(any(item["name"] == "Archive Shelf A" for item in locations.json()))

        self.client.delete(f"/api/games/{gid}")
        self.client.delete(f"/api/games/{wid}")

    def test_price_catalog_platforms_endpoint(self):
        r = self.client.get("/api/price-catalog/platforms")
        self.assertEqual(r.status_code, 200)
        platforms = r.json()
        self.assertTrue(isinstance(platforms, list))
        self.assertTrue(len(platforms) > 0)
        first = platforms[0]
        self.assertIn("key", first)
        self.assertIn("label", first)
        self.assertIn("scraper_slug", first)
        self.assertIn("count", first)
        # Check that canonical keys exist
        keys = [p["key"] for p in platforms]
        self.assertIn("playstation-5", keys)
        self.assertIn("nintendo-switch", keys)

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

        listed = self.client.get("/api/games")
        self.assertEqual(listed.status_code, 200)
        matching_game = next(item for item in listed.json() if item["id"] == game_id)
        self.assertTrue(matching_game.get("last_price_at"))

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

    def test_full_backup_round_trip_with_uploads_and_credentials(self):
        platform = self._platform_by_name("xbox one")
        payload = {
            "title": "Backup Round Trip Item",
            "platform_id": platform["id"],
            "item_type": "accessory",
            "cover_url": "/uploads/backup-roundtrip.png",
            "is_wishlist": False,
        }
        created = self.client.post("/api/games", json=payload)
        self.assertEqual(created.status_code, 200)
        game_id = created.json()["id"]

        self._insert_price_catalog(
            title="Backup Catalog Entry",
            platform=platform["name"],
            loose_eur=42.50,
        )

        upload_path = Path(os.environ["UPLOADS_DIR"]) / "backup-roundtrip.png"
        upload_path.write_bytes(b"backup-image-content")
        with closing(sqlite3.connect(self._db_path())) as con:
            con.execute(
                "INSERT INTO app_meta (key, value) VALUES (?, ?)",
                ("cfg:rawg_api_key", "backup-secret-value"),
            )
            con.commit()

        lot = self.client.post(
            "/api/lots",
            json={"name": "Backup round trip lot", "purchase_price_gross": 50},
        )
        self.assertEqual(lot.status_code, 200)
        lot_id = lot.json()["id"]
        item = self.client.post(
            f"/api/lots/{lot_id}/items",
            json={"game_id": game_id, "quantity": 2, "estimated_value": 30},
        )
        self.assertEqual(item.status_code, 200)

        backup = self.client.post(
            "/api/backups/create",
            json={"include_provider_credentials": True, "backup_password": "correct horse battery staple"},
        )
        self.assertEqual(backup.status_code, 200)
        archive_bytes = backup.content
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = set(archive.namelist())
            self.assertIn("manifest.json", names)
            self.assertIn("collection.sqlite", names)
            self.assertIn("uploads/backup-roundtrip.png", names)
            self.assertIn("encrypted-secrets.json", names)
            manifest = __import__("json").loads(archive.read("manifest.json"))
            self.assertTrue(manifest["includes"]["price_catalog_cache"])
            self.assertGreaterEqual(manifest["counts"]["price_catalog"], 1)
            snapshot_dir = Path(tempfile.mkdtemp(prefix="collectabase_snapshot_"))
            snapshot_path = snapshot_dir / "collection.sqlite"
            snapshot_path.write_bytes(archive.read("collection.sqlite"))
        with closing(sqlite3.connect(snapshot_path)) as con:
            cleartext_secret = con.execute(
                "SELECT value FROM app_meta WHERE key = ?", ("cfg:rawg_api_key",)
            ).fetchone()
            catalog_entry = con.execute(
                "SELECT loose_eur FROM price_catalog WHERE title = ?", ("Backup Catalog Entry",)
            ).fetchone()
        self.assertIsNone(cleartext_secret)
        self.assertEqual(catalog_entry[0], 42.50)

        inspected = self.client.post(
            "/api/backups/inspect",
            files={"file": ("collectabase-backup.zip", archive_bytes, "application/zip")},
        )
        self.assertEqual(inspected.status_code, 200)
        preview = inspected.json()
        self.assertEqual(preview["counts"]["games"], 1)
        self.assertEqual(preview["counts"]["lots"], 1)
        self.assertTrue(preview["includes_provider_credentials"])

        self.client.delete(f"/api/games/{game_id}")
        upload_path.unlink()
        wrong_password = self.client.post(
            "/api/backups/restore",
            json={
                "restore_token": preview["token"],
                "confirmation": "RESTORE",
                "backup_password": "wrong password value",
            },
        )
        self.assertEqual(wrong_password.status_code, 400)
        self.assertEqual(self.client.get(f"/api/games/{game_id}").status_code, 404)
        restored = self.client.post(
            "/api/backups/restore",
            json={
                "restore_token": preview["token"],
                "confirmation": "RESTORE",
                "backup_password": "correct horse battery staple",
            },
        )
        self.assertEqual(restored.status_code, 200)
        self.assertTrue(restored.json()["safety_backup"])

        game = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(game.status_code, 200)
        self.assertEqual(game.json()["title"], payload["title"])
        self.assertEqual(upload_path.read_bytes(), b"backup-image-content")
        with closing(sqlite3.connect(self._db_path())) as con:
            restored_secret = con.execute(
                "SELECT value FROM app_meta WHERE key = ?", ("cfg:rawg_api_key",)
            ).fetchone()
        self.assertEqual(restored_secret[0], "backup-secret-value")

    def test_automatic_backup_keeps_only_configured_archives(self):
        from backend.services.backup_service import create_automatic_backup

        backup_dir = Path(self._db_path()).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        expired = backup_dir / "collectabase-auto-backup-20000101T000000Z.zip"
        expired.write_bytes(b"expired-test-backup")

        result = create_automatic_backup(retention=1)
        archive_path = Path(result["path"])
        self.assertTrue(archive_path.exists())
        self.assertEqual(result["retained"], 1)
        self.assertFalse(expired.exists())

        with zipfile.ZipFile(archive_path) as archive:
            self.assertIn("manifest.json", archive.namelist())
            self.assertIn("collection.sqlite", archive.namelist())
            self.assertNotIn("encrypted-secrets.json", archive.namelist())

    def test_automatic_backup_uses_configured_backup_directory(self):
        from backend.services.backup_service import create_automatic_backup

        configured_backup_dir = Path(tempfile.mkdtemp(prefix="collectabase_backup_destination_"))
        with patch.dict(os.environ, {"COLLECTABASE_BACKUP_DIR": str(configured_backup_dir)}):
            result = create_automatic_backup(retention=1)

        archive_path = Path(result["path"])
        self.assertEqual(archive_path.parent, configured_backup_dir)
        self.assertTrue(archive_path.exists())

    def test_settings_info_counts_backups_in_configured_directory(self):
        configured_backup_dir = Path(tempfile.mkdtemp(prefix="collectabase_settings_backups_"))
        (configured_backup_dir / "collectabase-auto-backup-20261005T000000Z.zip").write_bytes(b"backup")

        with patch.dict(os.environ, {"COLLECTABASE_BACKUP_DIR": str(configured_backup_dir)}):
            response = self.client.get("/api/settings/info")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["auto_backup_count"], 1)


if __name__ == "__main__":
    unittest.main()
