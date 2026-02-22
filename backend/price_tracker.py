import asyncio
import base64
import os
import re
import statistics
import time
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import dict_from_row, get_db

router = APIRouter()

# Map our platform names -> PriceCharting slugs.
PLATFORM_SLUGS = {
    "playstation 5": "playstation-5",
    "playstation 4": "playstation-4",
    "playstation 3": "playstation-3",
    "playstation 2": "playstation-2",
    "playstation": "playstation",
    "psp": "psp",
    "ps vita": "ps-vita",
    "xbox series x/s": "xbox-series-x",
    "xbox one": "xbox-one",
    "xbox 360": "xbox-360",
    "xbox": "xbox",
    "nintendo switch": "nintendo-switch",
    "nintendo switch 2": "nintendo-switch-2",
    "wii u": "wii-u",
    "wii": "wii",
    "gamecube": "gamecube",
    "nintendo 64": "nintendo-64",
    "snes": "super-nintendo",
    "nes": "nes",
    "game boy advance": "gameboy-advance",
    "game boy color": "gameboy-color",
    "game boy": "gameboy",
    "nintendo 3ds": "3ds",
    "nintendo ds": "nintendo-ds",
    "sega dreamcast": "sega-dreamcast",
    "sega saturn": "sega-saturn",
    "sega genesis/mega drive": "sega-genesis",
    "sega master system": "sega-master-system",
    "sega game gear": "game-gear",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Collectabase/1.0)"}
NOT_CONFIGURED_ERROR = "Configure PRICECHARTING_TOKEN or EBAY_CLIENT_ID to enable market prices"
_EBAY_TOKEN_CACHE = {"token": None, "expires_at": 0.0}


async def get_eur_rate() -> float:
    """Fetch live USD->EUR rate from frankfurter.app (no key required)."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get("https://api.frankfurter.app/latest?from=USD&to=EUR")
            return res.json()["rates"]["EUR"]
    except Exception:
        return 0.92  # reasonable fallback.


def _pricecharting_token() -> Optional[str]:
    token = os.getenv("PRICECHARTING_TOKEN", "").strip()
    return token or None


def _ebay_credentials():
    client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None, None
    return client_id, client_secret


def _rawg_key() -> Optional[str]:
    key = os.getenv("RAWG_API_KEY", "").strip()
    return key or None


def _to_eur(usd_price: Optional[float], eur_rate: float):
    return round(usd_price * eur_rate, 2) if usd_price is not None else None


def _trim_outliers_and_median(prices):
    if not prices:
        return None, [], None, None

    ordered = sorted(prices)
    trim_each_side = int(len(ordered) * 0.1)
    if trim_each_side > 0 and len(ordered) > trim_each_side * 2:
        trimmed = ordered[trim_each_side:-trim_each_side]
    else:
        trimmed = ordered

    if not trimmed:
        return None, [], None, None

    median_price = float(statistics.median(trimmed))
    return median_price, trimmed, float(min(trimmed)), float(max(trimmed))


def _parse_usd_price(text: Optional[str]) -> Optional[float]:
    """Parse a price string like '$33.31' or '33.31' into a float."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text.strip())
    try:
        value = float(cleaned)
        return value if value > 0 else None
    except (ValueError, TypeError):
        return None


def _prices_differ(old_value: Optional[float], new_value: Optional[float]) -> bool:
    if old_value is None and new_value is None:
        return False
    if old_value is None or new_value is None:
        return True
    return abs(float(old_value) - float(new_value)) >= 0.005


async def _fetch_pricecharting_api(title: str, platform_name: str, token: str):
    """PriceCharting API: /api/product?t=TOKEN&q=QUERY."""
    query = " ".join(part for part in [title, platform_name] if part).strip()
    params = {"t": token, "q": query}

    try:
        async with httpx.AsyncClient(timeout=12, headers=HEADERS) as client:
            res = await client.get("https://www.pricecharting.com/api/product", params=params)

        print(f"PriceCharting API ({res.status_code}) for '{query}': {res.text[:500]}")

        if res.status_code >= 400:
            return None

        payload = res.json()
        if not isinstance(payload, dict):
            return None

        def cents(key):
            value = payload.get(key, 0)
            return value / 100 if value else None

        loose_usd = cents("loose-price")
        if loose_usd is None:
            return None

        return {
            "pricecharting_id": str(payload.get("id") or payload.get("product-id") or ""),
            "product_name": payload.get("product-name", query),
            "loose_usd": loose_usd,
            "cib_usd": cents("cib-price"),
            "new_usd": cents("new-price"),
        }
    except Exception as e:
        print(f"PriceCharting API error for '{query}': {e}")
        return None


async def _fetch_pricecharting_scrape(title: str, platform_name: str):
    """Scrape PriceCharting without an API token by parsing HTML pages."""
    query = " ".join(part for part in [title, platform_name] if part).strip()
    search_url = "https://www.pricecharting.com/search-products"
    search_params = {"q": query, "type": "videogames"}

    try:
        async with httpx.AsyncClient(timeout=15, headers=HEADERS, follow_redirects=True) as client:
            # Step 1: Search for the game
            search_res = await client.get(search_url, params=search_params)
            print(f"PriceCharting scrape search ({search_res.status_code}) for '{query}'")
            if search_res.status_code >= 400:
                return None

            soup = BeautifulSoup(search_res.text, "html.parser")

            # Find the first result link matching /game/...
            product_link = None
            for a in soup.select("a[href^='/game/']"):
                href = a.get("href", "")
                # Skip non-game links (e.g. /game-type)
                parts = href.strip("/").split("/")
                if len(parts) >= 3 and parts[0] == "game":
                    product_link = href
                    break

            if not product_link:
                print(f"PriceCharting scrape: no result found for '{query}'")
                return None

            product_url = f"https://www.pricecharting.com{product_link}"
            print(f"PriceCharting scrape: fetching {product_url}")

            # Step 2: Fetch the product page
            product_res = await client.get(product_url)
            if product_res.status_code >= 400:
                return None

        # Extract pricecharting_id from URL (last numeric segment or query param)
        pc_id_match = re.search(r"/(\d+)(?:\?|$)", product_link)
        pc_id = pc_id_match.group(1) if pc_id_match else ""

        product_soup = BeautifulSoup(product_res.text, "html.parser")

        # Extract product name from page title or h1
        product_name = query
        h1 = product_soup.select_one("h1#product_name, h1.chart_title")
        if h1:
            product_name = h1.get_text(strip=True)

        # Extract prices by element ID
        def get_price(element_id: str) -> Optional[float]:
            el = product_soup.select_one(f"#{element_id} .price, #{element_id}")
            if el:
                # Try span.price first, then the element itself
                span = el.select_one("span.price") or el.select_one(".price")
                text = (span or el).get_text(strip=True)
                return _parse_usd_price(text)
            return None

        loose_usd = get_price("used_price")
        cib_usd = get_price("complete_price")
        new_usd = get_price("new_price")

        if loose_usd is None:
            print(f"PriceCharting scrape: could not parse loose price for '{query}'")
            return None

        return {
            "pricecharting_id": pc_id,
            "product_name": product_name,
            "loose_usd": loose_usd,
            "cib_usd": cib_usd,
            "new_usd": new_usd,
        }
    except Exception as e:
        print(f"PriceCharting scrape error for '{query}': {e}")
        return None


async def fetch_pricecharting(title: str, platform_name: str):
    """Fetch prices from PriceCharting. Uses API token if available, scraping as fallback."""
    token = _pricecharting_token()
    if token:
        return await _fetch_pricecharting_api(title, platform_name, token)
    return await _fetch_pricecharting_scrape(title, platform_name)


async def get_ebay_token() -> Optional[str]:
    client_id, client_secret = _ebay_credentials()
    if not client_id or not client_secret:
        return None

    now = time.time()
    cached = _EBAY_TOKEN_CACHE.get("token")
    if cached and _EBAY_TOKEN_CACHE.get("expires_at", 0) > now:
        return cached

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    body = "grant_type=client_credentials&scope=https://api.ebay.com/oauth/api_scope"

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            res = await client.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers=headers,
                content=body,
            )

        if res.status_code >= 400:
            print(f"eBay token error ({res.status_code}): {res.text[:500]}")
            return None

        data = res.json()
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 0))
        if not token:
            return None

        _EBAY_TOKEN_CACHE["token"] = token
        _EBAY_TOKEN_CACHE["expires_at"] = now + max(expires_in - 60, 60)
        return token
    except Exception as e:
        print(f"eBay token fetch error: {e}")
        return None


async def fetch_ebay_market_price(title: str, platform_name: str):
    token = await get_ebay_token()
    if not token:
        return None

    query = " ".join(part for part in [title, platform_name] if part).strip()
    params = {
        "q": query,
        "filter": "conditionIds:{2750|3000}",
        "limit": "10",
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE",
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            res = await client.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                params=params,
                headers=headers,
            )

        if res.status_code >= 400:
            print(f"eBay browse error ({res.status_code}): {res.text[:500]}")
            return None

        payload = res.json()
        items = payload.get("itemSummaries", []) or []
        prices = []
        for item in items:
            value = (item.get("price") or {}).get("value")
            if value is None:
                continue
            try:
                price = float(value)
            except (TypeError, ValueError):
                continue
            if price > 0:
                prices.append(price)

        median_price, trimmed, min_price, max_price = _trim_outliers_and_median(prices)
        if median_price is None:
            return None

        return {
            "market_price": round(median_price, 2),
            "sample_size": len(trimmed),
            "price_min": round(min_price, 2),
            "price_max": round(max_price, 2),
        }
    except Exception as e:
        print(f"eBay browse error for '{query}': {e}")
        return None


async def fetch_rawg_reference(title: str, platform_name: str):
    """Fetch RAWG metadata/store links as reference fallback (no sold-price estimation)."""
    key = _rawg_key()
    if not key:
        return None

    query = " ".join(part for part in [title, platform_name] if part).strip()
    params = {"key": key, "search": query, "search_precise": "true", "page_size": "1"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get("https://api.rawg.io/api/games", params=params)
        if res.status_code >= 400:
            print(f"RAWG search error ({res.status_code}): {res.text[:500]}")
            return None

        payload = res.json()
        results = payload.get("results", []) or []
        if not results:
            return None

        game = results[0]
        rawg_id = game.get("id")
        slug = game.get("slug")
        rawg_url = f"https://rawg.io/games/{slug}" if slug else None

        store_links = []
        for store_entry in (game.get("stores") or []):
            store = store_entry.get("store") or {}
            url = store_entry.get("url") or store_entry.get("url_en")
            name = store.get("name") or "Store"
            if url:
                store_links.append({"name": name, "url": url})

        if rawg_id and len(store_links) < 3:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    stores_res = await client.get(
                        f"https://api.rawg.io/api/games/{rawg_id}/stores",
                        params={"key": key},
                    )
                if stores_res.status_code < 400:
                    stores_payload = stores_res.json()
                    for row in (stores_payload.get("results") or []):
                        store = row.get("store") or {}
                        url = row.get("url") or row.get("url_en")
                        name = store.get("name") or "Store"
                        if url:
                            store_links.append({"name": name, "url": url})
            except Exception as nested:
                print(f"RAWG stores fallback error for '{query}': {nested}")

        unique = []
        seen = set()
        for row in store_links:
            url = row.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            unique.append(row)

        return {
            "source": "rawg",
            "rawg_game_id": rawg_id,
            "rawg_url": rawg_url,
            "store_links": unique[:6],
        }
    except Exception as e:
        print(f"RAWG reference error for '{query}': {e}")
        return None


def _get_game_for_price_lookup(game_id: int):
    with get_db() as db:
        row = db.execute(
            """
            SELECT g.*, p.name as platform_name
            FROM games g LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.id = ?
            """,
            (game_id,),
        ).fetchone()
    return dict_from_row(row) if row else None


@router.post("/api/games/{game_id}/fetch-market-price")
async def fetch_market_price(game_id: int):
    """Primary source: PriceCharting. Fallback: eBay Browse."""
    game = _get_game_for_price_lookup(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    pricecharting_enabled = _pricecharting_token() is not None
    ebay_enabled = all(_ebay_credentials())
    rawg_enabled = _rawg_key() is not None

    if not pricecharting_enabled and not ebay_enabled and not rawg_enabled:
        return {"error": NOT_CONFIGURED_ERROR}

    eur_rate = await get_eur_rate()

    if pricecharting_enabled:
        pc = await fetch_pricecharting(game["title"], game.get("platform_name") or "")
        if pc:
            loose_eur = _to_eur(pc["loose_usd"], eur_rate)
            cib_eur = _to_eur(pc["cib_usd"], eur_rate)
            new_eur = _to_eur(pc["new_usd"], eur_rate)
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO price_history
                        (game_id, source, loose_price, complete_price, new_price, eur_rate, pricecharting_id)
                    VALUES (?, 'pricecharting', ?, ?, ?, ?, ?)
                    """,
                    (game_id, loose_eur, cib_eur, new_eur, eur_rate, pc["pricecharting_id"]),
                )
                db.commit()
            return {"market_price": loose_eur, "source": "pricecharting", "condition": "loose"}

    if ebay_enabled:
        ebay = await fetch_ebay_market_price(game["title"], game.get("platform_name") or "")
        if ebay:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO price_history
                        (game_id, source, loose_price, complete_price, new_price, eur_rate)
                    VALUES (?, 'ebay', ?, NULL, NULL, 1.0)
                    """,
                    (game_id, ebay["market_price"]),
                )
                db.commit()
            return {
                "market_price": ebay["market_price"],
                "source": "ebay",
                "sample_size": ebay["sample_size"],
                "price_min": ebay["price_min"],
                "price_max": ebay["price_max"],
            }

    if rawg_enabled:
        rawg = await fetch_rawg_reference(game["title"], game.get("platform_name") or "")
        if rawg:
            return {
                "error": "No market price found. Set value manually.",
                "source": "rawg",
                "rawg_url": rawg.get("rawg_url"),
                "store_links": rawg.get("store_links", []),
            }

    return {"error": "No market price found. Set value manually."}


@router.post("/api/games/{game_id}/price-check")
async def check_price(game_id: int):
    """Backward-compatible alias."""
    return await fetch_market_price(game_id)


@router.get("/api/games/{game_id}/price-history")
async def get_price_history(game_id: int):
    """Return the last 20 price snapshots for a game."""
    with get_db() as db:
        rows = db.execute(
            """
            SELECT * FROM price_history
            WHERE game_id = ?
            ORDER BY fetched_at DESC
            LIMIT 20
            """,
            (game_id,),
        ).fetchall()
        return [dict_from_row(r) for r in rows]


@router.post("/api/prices/update-all")
async def bulk_price_update(limit: int = 100):
    """Fetch prices for up to `limit` games (only non-wishlist games)."""
    with get_db() as db:
        rows = db.execute(
            """
            SELECT g.id, g.title, p.name as platform_name
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.is_wishlist = 0 AND g.item_type = 'game'
            ORDER BY g.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        games = [dict_from_row(r) for r in rows]

    eur_rate = await get_eur_rate()
    token = _pricecharting_token()
    if not token:
        return {"success": 0, "failed": len(games), "total": len(games), "error": "PRICECHARTING_TOKEN not set"}

    success = 0
    failed = 0

    for game in games:
        pc = await fetch_pricecharting(game["title"], game["platform_name"] or "")
        if pc:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO price_history
                        (game_id, source, loose_price, complete_price, new_price, eur_rate, pricecharting_id)
                    VALUES (?, 'pricecharting', ?, ?, ?, ?, ?)
                    """,
                    (
                        game["id"],
                        _to_eur(pc["loose_usd"], eur_rate),
                        _to_eur(pc["cib_usd"], eur_rate),
                        _to_eur(pc["new_usd"], eur_rate),
                        eur_rate,
                        pc["pricecharting_id"],
                    ),
                )
                db.commit()
            success += 1
        else:
            failed += 1

        await asyncio.sleep(0.4)  # stay polite to PriceCharting.

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
        db.execute(
            """
            INSERT INTO price_history
                (game_id, source, loose_price, complete_price, new_price)
            VALUES (?, 'manual', ?, ?, ?)
            """,
            (game_id, entry.loose_price, entry.complete_price, entry.new_price),
        )
        db.commit()
    return {"ok": True}


# ── Price Catalog (scraped platform catalogs) ─────────────────────────────────


async def scrape_platform_catalog(platform_slug: str, platform_label: str) -> list:
    """Scrape all games from a PriceCharting console catalog page."""
    entries = []
    base_url = f"https://www.pricecharting.com/console/{platform_slug}"

    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        for page in range(1, 51):  # max 50 pages safety cap
            params = {"sort": "title", "order": "asc", "page": str(page)}
            try:
                res = await client.get(base_url, params=params)
                print(f"Catalog scrape {platform_slug} page {page}: HTTP {res.status_code}")
                if res.status_code >= 400:
                    break
            except Exception as e:
                print(f"Catalog scrape error {platform_slug} page {page}: {e}")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.select_one("table#games_table")
            if not table:
                break

            rows = table.select("tbody tr")
            if not rows:
                break

            page_entries = []
            for row in rows:
                # Title + link
                title_cell = row.select_one("td.title a")
                if not title_cell:
                    continue
                title = title_cell.get_text(strip=True)
                href = title_cell.get("href", "")

                # Extract pricecharting_id from href e.g. /game/nintendo-switch/mario-kart-8-deluxe
                pc_id_match = re.search(r"/game/[^/]+/(.+)$", href)
                pc_id = pc_id_match.group(1) if pc_id_match else ""
                page_url = f"https://www.pricecharting.com{href}" if href else ""

                # Prices – cells have class loose_price / cib_price / new_price
                def cell_price(cls):
                    td = row.select_one(f"td.{cls}")
                    if not td:
                        return None
                    span = td.select_one("span.price") or td
                    return _parse_usd_price(span.get_text(strip=True))

                loose_usd = cell_price("loose_price")
                cib_usd   = cell_price("cib_price")
                new_usd   = cell_price("new_price")

                if title and (loose_usd is not None or cib_usd is not None):
                    page_entries.append({
                        "pricecharting_id": pc_id,
                        "title": title,
                        "platform": platform_label,
                        "loose_usd": loose_usd,
                        "cib_usd": cib_usd,
                        "new_usd": new_usd,
                        "page_url": page_url,
                    })

            if not page_entries:
                break

            entries.extend(page_entries)
            print(f"  → {len(page_entries)} games collected (total so far: {len(entries)})")

            if len(page_entries) < 25:
                # Likely the last page
                break

            await asyncio.sleep(1.0)  # be polite between pages

    return entries


def _upsert_catalog_entries(entries: list, eur_rate: float):
    """Incrementally upsert catalog rows; update only when prices changed."""
    if not entries:
        return {
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "unchanged": 0,
            "deduped_in_batch": 0,
            "duplicates_removed": 0,
        }

    deduped_entries = []
    seen = set()
    deduped_in_batch = 0
    for e in entries:
        platform_key = (e.get("platform") or "").strip().lower()
        title_key = (e.get("title") or "").strip().lower()
        pc_id = (e.get("pricecharting_id") or "").strip().lower()
        key = (platform_key, pc_id if pc_id else title_key)
        if key in seen:
            deduped_in_batch += 1
            continue
        seen.add(key)
        deduped_entries.append(e)

    inserted = 0
    updated = 0
    unchanged = 0
    duplicates_removed = 0

    with get_db() as db:
        for e in deduped_entries:
            platform = e["platform"]
            title = e["title"]
            pc_id = (e.get("pricecharting_id") or "").strip()

            # Prefer matching by platform+pricecharting_id when available.
            existing_rows = []
            if pc_id:
                existing_rows = db.execute(
                    """
                    SELECT id, loose_usd, cib_usd, new_usd
                    FROM price_catalog
                    WHERE platform = ? AND pricecharting_id = ?
                    ORDER BY id DESC
                    """,
                    (platform, pc_id),
                ).fetchall()

            # Fallback for older rows without pricecharting_id.
            if not existing_rows:
                existing_rows = db.execute(
                    """
                    SELECT id, loose_usd, cib_usd, new_usd
                    FROM price_catalog
                    WHERE platform = ? AND LOWER(title) = LOWER(?)
                    ORDER BY id DESC
                    """,
                    (platform, title),
                ).fetchall()

            keep = existing_rows[0] if existing_rows else None
            if len(existing_rows) > 1:
                duplicate_ids = [row["id"] for row in existing_rows[1:]]
                db.executemany(
                    "DELETE FROM price_catalog WHERE id = ?",
                    [(dup_id,) for dup_id in duplicate_ids],
                )
                duplicates_removed += len(duplicate_ids)

            loose_usd = e["loose_usd"]
            cib_usd = e["cib_usd"]
            new_usd = e["new_usd"]
            loose_eur = _to_eur(loose_usd, eur_rate)
            cib_eur = _to_eur(cib_usd, eur_rate)
            new_eur = _to_eur(new_usd, eur_rate)

            if not keep:
                db.execute(
                    """
                    INSERT INTO price_catalog
                        (pricecharting_id, title, platform, loose_usd, cib_usd, new_usd,
                         loose_eur, cib_eur, new_eur, page_url, scraped_at, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (
                        pc_id,
                        title,
                        platform,
                        loose_usd,
                        cib_usd,
                        new_usd,
                        loose_eur,
                        cib_eur,
                        new_eur,
                        e["page_url"],
                    ),
                )
                inserted += 1
                continue

            prices_changed = (
                _prices_differ(keep["loose_usd"], loose_usd)
                or _prices_differ(keep["cib_usd"], cib_usd)
                or _prices_differ(keep["new_usd"], new_usd)
            )

            if prices_changed:
                db.execute(
                    """
                    UPDATE price_catalog
                    SET pricecharting_id = ?, title = ?, platform = ?,
                        loose_usd = ?, cib_usd = ?, new_usd = ?,
                        loose_eur = ?, cib_eur = ?, new_eur = ?,
                        page_url = ?, scraped_at = CURRENT_TIMESTAMP, changed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        pc_id,
                        title,
                        platform,
                        loose_usd,
                        cib_usd,
                        new_usd,
                        loose_eur,
                        cib_eur,
                        new_eur,
                        e["page_url"],
                        keep["id"],
                    ),
                )
                updated += 1
            else:
                # Keep "last seen" fresh even without a price movement.
                db.execute(
                    """
                    UPDATE price_catalog
                    SET pricecharting_id = ?, title = ?, platform = ?,
                        loose_eur = ?, cib_eur = ?, new_eur = ?,
                        page_url = ?, scraped_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        pc_id,
                        title,
                        platform,
                        loose_eur,
                        cib_eur,
                        new_eur,
                        e["page_url"],
                        keep["id"],
                    ),
                )
                unchanged += 1

        db.commit()

    return {
        "processed": len(deduped_entries),
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "deduped_in_batch": deduped_in_batch,
        "duplicates_removed": duplicates_removed,
    }


@router.post("/api/price-catalog/scrape")
async def scrape_catalog(platform: str = "all"):
    """Scrape PriceCharting catalog for one or all platforms into price_catalog table."""
    if platform == "all":
        targets = list(PLATFORM_SLUGS.items())
    else:
        # Accept either a slug (e.g. "nintendo-switch") or a label
        label = next(
            (lbl for lbl, slug in PLATFORM_SLUGS.items() if slug == platform or lbl == platform),
            None,
        )
        if not label:
            raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
        targets = [(label, PLATFORM_SLUGS[label])]

    eur_rate = await get_eur_rate()
    total_scraped = 0
    total_inserted = 0
    total_updated = 0
    total_unchanged = 0
    total_deduped_in_batch = 0
    total_duplicates_removed = 0

    for label, slug in targets:
        print(f"Starting catalog scrape for {label} ({slug})")
        entries = await scrape_platform_catalog(slug, label)
        stats = _upsert_catalog_entries(entries, eur_rate)
        total_scraped += stats["processed"]
        total_inserted += stats["inserted"]
        total_updated += stats["updated"]
        total_unchanged += stats["unchanged"]
        total_deduped_in_batch += stats["deduped_in_batch"]
        total_duplicates_removed += stats["duplicates_removed"]
        print(
            f"Finished {label}: processed={stats['processed']} inserted={stats['inserted']} "
            f"updated={stats['updated']} unchanged={stats['unchanged']}"
        )
        if len(targets) > 1:
            await asyncio.sleep(2.0)  # pause between platforms when scraping all

    return {
        "scraped": total_scraped,
        "inserted": total_inserted,
        "updated": total_updated,
        "unchanged": total_unchanged,
        "deduped_in_batch": total_deduped_in_batch,
        "duplicates_removed": total_duplicates_removed,
        "platforms": [lbl for lbl, _ in targets],
    }


@router.get("/api/price-catalog")
async def search_catalog(
    search: Optional[str] = None,
    platform: Optional[str] = None,
    sort: str = "title",
    order: str = "asc",
    page: int = 1,
    limit: int = 50,
):
    """Search and paginate the local price catalog."""
    allowed_sorts = {"title", "platform", "loose_eur", "cib_eur", "new_eur"}
    if sort not in allowed_sorts:
        sort = "title"
    order_dir = "DESC" if order.lower() == "desc" else "ASC"

    conditions = []
    params = []

    if search:
        conditions.append("title LIKE ?")
        params.append(f"%{search}%")
    if platform:
        conditions.append("platform = ?")
        params.append(platform)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * limit

    with get_db() as db:
        total = db.execute(
            f"SELECT COUNT(*) FROM price_catalog {where}", params
        ).fetchone()[0]

        rows = db.execute(
            f"""
            SELECT * FROM price_catalog
            {where}
            ORDER BY {sort} {order_dir}
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()

    return {
        "items": [dict_from_row(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/api/price-catalog/platforms")
async def catalog_platforms():
    """Return distinct platforms present in the price catalog."""
    with get_db() as db:
        rows = db.execute(
            "SELECT DISTINCT platform FROM price_catalog ORDER BY platform"
        ).fetchall()
    return [r["platform"] for r in rows]


@router.delete("/api/price-catalog")
async def clear_catalog(platform: Optional[str] = None):
    """Delete all (or one platform's) entries from the price catalog."""
    with get_db() as db:
        if platform:
            db.execute("DELETE FROM price_catalog WHERE platform = ?", (platform,))
        else:
            db.execute("DELETE FROM price_catalog")
        db.commit()
    return {"ok": True}
