from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import asyncio
from .database import get_db, dict_from_row

router = APIRouter()

# Map our platform names → PriceCharting slugs
PLATFORM_SLUGS = {
    'playstation 5': 'playstation-5',
    'playstation 4': 'playstation-4',
    'playstation 3': 'playstation-3',
    'playstation 2': 'playstation-2',
    'playstation': 'playstation',
    'psp': 'psp',
    'ps vita': 'ps-vita',
    'xbox series x/s': 'xbox-series-x',
    'xbox one': 'xbox-one',
    'xbox 360': 'xbox-360',
    'xbox': 'xbox',
    'nintendo switch': 'nintendo-switch',
    'nintendo switch 2': 'nintendo-switch-2',
    'wii u': 'wii-u',
    'wii': 'wii',
    'gamecube': 'gamecube',
    'nintendo 64': 'nintendo-64',
    'snes': 'super-nintendo',
    'nes': 'nes',
    'game boy advance': 'gameboy-advance',
    'game boy color': 'gameboy-color',
    'game boy': 'gameboy',
    'nintendo 3ds': '3ds',
    'nintendo ds': 'nintendo-ds',
    'sega dreamcast': 'sega-dreamcast',
    'sega saturn': 'sega-saturn',
    'sega genesis/mega drive': 'sega-genesis',
    'sega master system': 'sega-master-system',
    'sega game gear': 'game-gear',
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; Collectabase/1.0)'}


async def get_eur_rate() -> float:
    """Fetch live USD→EUR rate from frankfurter.app (no key required)."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get('https://api.frankfurter.app/latest?from=USD&to=EUR')
            return res.json()['rates']['EUR']
    except Exception:
        return 0.92  # reasonable fallback


async def fetch_pricecharting(title: str, platform_name: str):
    """Search PriceCharting for a game and return raw USD prices (or None)."""
    slug = PLATFORM_SLUGS.get(platform_name.lower())
    params = {'q': title}
    if slug:
        params['platform'] = slug

    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            # 1. Search for the product
            res = await client.get('https://www.pricecharting.com/api/products', params=params)
            products = res.json().get('products', [])
            if not products:
                return None

            product_id = products[0].get('id')

            # 2. Fetch detailed price data
            res2 = await client.get(f'https://www.pricecharting.com/api/product?id={product_id}')
            pd = res2.json()

            def cents(key):
                v = pd.get(key, 0)
                return v / 100 if v else None

            return {
                'pricecharting_id': str(product_id),
                'product_name': pd.get('product-name', ''),
                'loose_usd': cents('loose-price'),
                'cib_usd': cents('cib-price'),
                'new_usd': cents('new-price'),
            }
    except Exception as e:
        print(f"PriceCharting error for '{title}': {e}")
        return None


@router.post("/api/games/{game_id}/price-check")
async def check_price(game_id: int):
    """Fetch current market prices from PriceCharting and store a snapshot."""
    with get_db() as db:
        row = db.execute("""
            SELECT g.*, p.name as platform_name
            FROM games g LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.id = ?
        """, (game_id,)).fetchone()

    if not row:
        return {"error": "Game not found"}

    game = dict_from_row(row)
    eur_rate = await get_eur_rate()
    pc = await fetch_pricecharting(game['title'], game['platform_name'] or '')

    if not pc:
        return {"error": "No price data found on PriceCharting"}

    def to_eur(usd):
        return round(usd * eur_rate, 2) if usd else None

    loose_eur = to_eur(pc['loose_usd'])
    cib_eur = to_eur(pc['cib_usd'])
    new_eur = to_eur(pc['new_usd'])

    with get_db() as db:
        db.execute("""
            INSERT INTO price_history
                (game_id, source, loose_price, complete_price, new_price, eur_rate, pricecharting_id)
            VALUES (?, 'pricecharting', ?, ?, ?, ?, ?)
        """, (game_id, loose_eur, cib_eur, new_eur, eur_rate, pc['pricecharting_id']))
        db.commit()

    return {
        "loose_eur": loose_eur,
        "cib_eur": cib_eur,
        "new_eur": new_eur,
        "eur_rate": eur_rate,
        "source_name": pc['product_name'],
        "pricecharting_id": pc['pricecharting_id'],
    }


@router.get("/api/games/{game_id}/price-history")
async def get_price_history(game_id: int):
    """Return the last 20 price snapshots for a game."""
    with get_db() as db:
        rows = db.execute("""
            SELECT * FROM price_history
            WHERE game_id = ?
            ORDER BY fetched_at DESC
            LIMIT 20
        """, (game_id,)).fetchall()
        return [dict_from_row(r) for r in rows]


@router.post("/api/prices/update-all")
async def bulk_price_update(limit: int = 100):
    """Fetch prices for up to `limit` games (only non-wishlist games)."""
    with get_db() as db:
        rows = db.execute("""
            SELECT g.id, g.title, p.name as platform_name
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.is_wishlist = 0 AND g.item_type = 'game'
            ORDER BY g.id ASC
            LIMIT ?
        """, (limit,)).fetchall()
        games = [dict_from_row(r) for r in rows]

    eur_rate = await get_eur_rate()
    success = 0
    failed = 0

    for game in games:
        pc = await fetch_pricecharting(game['title'], game['platform_name'] or '')
        if pc:
            def to_eur(usd):
                return round(usd * eur_rate, 2) if usd else None

            with get_db() as db:
                db.execute("""
                    INSERT INTO price_history
                        (game_id, source, loose_price, complete_price, new_price, eur_rate, pricecharting_id)
                    VALUES (?, 'pricecharting', ?, ?, ?, ?, ?)
                """, (game['id'], to_eur(pc['loose_usd']), to_eur(pc['cib_usd']),
                      to_eur(pc['new_usd']), eur_rate, pc['pricecharting_id']))
                db.commit()
            success += 1
        else:
            failed += 1

        await asyncio.sleep(0.4)  # stay polite to PriceCharting

    return {"success": success, "failed": failed, "total": len(games)}


class ManualPriceEntry(BaseModel):
    loose_price: Optional[float] = None
    complete_price: Optional[float] = None
    new_price: Optional[float] = None


@router.post("/api/games/{game_id}/price-manual")
async def add_manual_price(game_id: int, entry: ManualPriceEntry):
    """Save a manually entered price snapshot (source='manual')."""
    with get_db() as db:
        row = db.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Game not found")

    with get_db() as db:
        db.execute("""
            INSERT INTO price_history
                (game_id, source, loose_price, complete_price, new_price)
            VALUES (?, 'manual', ?, ?, ?)
        """, (game_id, entry.loose_price, entry.complete_price, entry.new_price))
        db.commit()
    return {"ok": True}
