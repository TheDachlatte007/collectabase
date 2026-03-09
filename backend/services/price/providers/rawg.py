from typing import Optional

import httpx

from ..utils import _env_any

def _rawg_key() -> Optional[str]:
    return _env_any("RAWG_API_KEY", "RAWG_KEY")

async def fetch_rawg_reference(title: str, platform_name: str):
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
                    stores_res = await client.get(f"https://api.rawg.io/api/games/{rawg_id}/stores", params={"key": key})
                if stores_res.status_code < 400:
                    for row in (stores_res.json().get("results") or []):
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
            if not url or url in seen: continue
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
