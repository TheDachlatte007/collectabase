import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from ..utils import (
    HEADERS,
    _catalog_match_score,
    _env_any,
    _normalize_text,
    _parse_usd_price,
)

def _pricecharting_token() -> Optional[str]:
    return _env_any("PRICECHARTING_TOKEN", "PRICE_CHARTING_TOKEN")

async def _fetch_pricecharting_api(title: str, platform_name: str, token: str):
    query = " ".join(part for part in [title, platform_name] if part).strip()
    params = {"t": token, "q": query}

    try:
        async with httpx.AsyncClient(timeout=12, headers=HEADERS) as client:
            res = await client.get("https://www.pricecharting.com/api/product", params=params)

        print(f"PriceCharting API ({res.status_code}) for '{query}': {res.text[:500]}")
        if res.status_code >= 400: return None

        payload = res.json()
        if not isinstance(payload, dict): return None

        def cents(key):
            value = payload.get(key, 0)
            return value / 100 if value else None

        loose_usd = cents("loose-price")
        if loose_usd is None: return None

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
    title = (title or "").strip()
    platform_name = (platform_name or "").strip()
    query = " ".join(part for part in [title, platform_name] if part).strip()
    search_url = "https://www.pricecharting.com/search-products"
    normalized_platform = _normalize_text(platform_name)
    normalized_title = _normalize_text(title)
    normalized_query = _normalize_text(query)

    attempts = []
    seen_attempts = set()

    def add_attempt(q: str, search_type: Optional[str]):
        cleaned_q = (q or "").strip()
        if not cleaned_q: return
        key = (cleaned_q.lower(), (search_type or "").lower())
        if key in seen_attempts: return
        seen_attempts.add(key)
        attempts.append((cleaned_q, search_type))

    add_attempt(query, "prices")
    add_attempt(query, "videogames")
    add_attempt(title, "prices")
    add_attempt(title, "videogames")
    add_attempt(query, None)
    add_attempt(title, None)

    try:
        async with httpx.AsyncClient(timeout=15, headers=HEADERS, follow_redirects=True) as client:
            product_link = None
            selected_query = query

            for attempt_query, search_type in attempts:
                params = {"q": attempt_query}
                if search_type: params["type"] = search_type
                search_res = await client.get(search_url, params=params)
                print(f"PriceCharting scrape search ({search_res.status_code}) for '{attempt_query}' type='{search_type or 'default'}'")
                if search_res.status_code >= 400: continue

                soup = BeautifulSoup(search_res.text, "html.parser")
                best_link = None
                best_score = -1.0

                for a in soup.select("a[href^='/game/']"):
                    href = a.get("href", "")
                    parts = href.strip("/").split("/")
                    if len(parts) < 3 or parts[0] != "game": continue

                    text = _normalize_text(a.get_text(" ", strip=True))
                    score = 0.0
                    if normalized_query and text:
                        score = max(
                            score,
                            _catalog_match_score(normalized_query, text),
                            _catalog_match_score(normalized_title or normalized_query, text),
                        )
                    if normalized_platform and normalized_platform in _normalize_text(href):
                        score += 0.08
                    if text and normalized_title and normalized_title in text:
                        score = max(score, 0.9)
                    if score > best_score:
                        best_score = score
                        best_link = href

                if best_link:
                    product_link = best_link
                    selected_query = attempt_query
                    break

            if not product_link:
                print(f"PriceCharting scrape: no result found for '{query}'")
                return None

            product_url = f"https://www.pricecharting.com{product_link}"
            print(f"PriceCharting scrape: fetching {product_url}")
            product_res = await client.get(product_url)
            if product_res.status_code >= 400: return None

        pc_id_match = re.search(r"/(\d+)(?:\?|$)", product_link)
        pc_id = pc_id_match.group(1) if pc_id_match else ""

        product_soup = BeautifulSoup(product_res.text, "html.parser")
        product_name = selected_query or query
        h1 = product_soup.select_one("h1#product_name, h1.chart_title")
        if h1: product_name = h1.get_text(strip=True)

        def get_price(element_id: str) -> Optional[float]:
            el = product_soup.select_one(f"#{element_id} .price, #{element_id}, td.{element_id} .js-price, td.{element_id}")
            if el:
                span = el.select_one("span.price") or el.select_one(".price")
                text = (span or el).get_text(strip=True)
                return _parse_usd_price(text)
            return None

        loose_usd = get_price("used_price")
        if loose_usd is None: return None

        return {
            "pricecharting_id": pc_id,
            "product_name": product_name,
            "loose_usd": loose_usd,
            "cib_usd": get_price("complete_price"),
            "new_usd": get_price("new_price"),
            "page_url": product_url,
        }
    except Exception as e:
        print(f"PriceCharting scrape error for '{query}': {e}")
        return None

async def fetch_pricecharting(title: str, platform_name: str):
    scraped = await _fetch_pricecharting_scrape(title, platform_name)
    if scraped: return scraped
    token = _pricecharting_token()
    if token: return await _fetch_pricecharting_api(title, platform_name, token)
    return None
