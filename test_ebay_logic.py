import asyncio
from unittest.mock import AsyncMock, patch
from backend.price_tracker import fetch_market_price
from backend.database import get_db

async def test_ebay_fallback():
    # Insert a dummy game using the backend context manager
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO games (id, title, platform_id, is_wishlist) VALUES (9999, 'Test Game', NULL, 0)")
        db.commit()
    
    # Mock everything to force fallback to eBay
    with patch("backend.price_tracker._lookup_local_catalog_price", return_value=None):
        with patch("backend.price_tracker._fetch_pricecharting_scrape", new=AsyncMock(return_value=None)):
            with patch("backend.price_tracker._ebay_credentials", return_value=("dummy", "dummy")):
                with patch("backend.price_tracker.fetch_ebay_market_price", new=AsyncMock(return_value={"market_price": 50.0, "sample_size": 10, "price_min": 40.0, "price_max": 60.0})):
                    res = await fetch_market_price(9999)
                    print("API Result:", res)

    with get_db() as db:
        history = db.execute("SELECT source, loose_price FROM price_history WHERE game_id = 9999").fetchall()
        print("DB History:", [dict(r) for r in history])
        db.execute("DELETE FROM games WHERE id = 9999")
        db.execute("DELETE FROM price_history where game_id = 9999")
        db.commit()

if __name__ == "__main__":
    asyncio.run(test_ebay_fallback())
