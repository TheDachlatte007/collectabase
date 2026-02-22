import os
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
