import base64
import time
from typing import Optional

import httpx

from ..utils import _env_any, _trim_outliers_and_median

_EBAY_TOKEN_CACHE = {"token": None, "expires_at": 0.0}

def _ebay_credentials():
    client_id = _env_any("EBAY_CLIENT_ID", "EBAY_APP_ID", "EBAY_APPID", "EBAY_CLIENTID")
    client_secret = _env_any("EBAY_CLIENT_SECRET", "EBAY_SECRET", "EBAY_CLIENTSECRET", "EBAY_SECRET_KEY")
    if not client_id or not client_secret:
        return None, None
    return client_id, client_secret

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
            res = await client.post("https://api.ebay.com/identity/v1/oauth2/token", headers=headers, content=body)
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
    params = {"q": query, "filter": "conditionIds:{2750|3000}", "limit": "10"}
    headers = {"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE"}

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            res = await client.get("https://api.ebay.com/buy/browse/v1/item_summary/search", params=params, headers=headers)

        if res.status_code >= 400:
            print(f"eBay browse error ({res.status_code}): {res.text[:500]}")
            return None

        payload = res.json()
        items = payload.get("itemSummaries", []) or []
        prices = []
        for item in items:
            value = (item.get("price") or {}).get("value")
            if value is None: continue
            try: price = float(value)
            except (TypeError, ValueError): continue
            if price > 0: prices.append(price)

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
