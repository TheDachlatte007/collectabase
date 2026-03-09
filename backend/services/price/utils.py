import os
import re
import statistics
from difflib import SequenceMatcher
from typing import Optional

import httpx

from ...database import get_app_meta_many, get_db, dict_from_row

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

def _env_any(*names: str) -> Optional[str]:
    env = os.environ
    for name in names:
        for candidate in (name, name.lower(), name.upper()):
            value = env.get(candidate, "").strip()
            if value:
                return value
    lowered = {k.lower(): v for k, v in env.items()}
    for name in names:
        value = str(lowered.get(name.lower(), "")).strip()
        if value:
            return value
    meta_keys = [f"cfg:{name.lower()}" for name in names]
    meta = get_app_meta_many(meta_keys)
    for key in meta_keys:
        value = str(meta.get(key, {}).get("value", "")).strip()
        if value:
            return value
    return None

async def get_eur_rate() -> float:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get("https://api.frankfurter.app/latest?from=USD&to=EUR")
            return res.json()["rates"]["EUR"]
    except Exception:
        return 0.92

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

def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

_TITLE_NOISE_TOKENS = {
    "console", "bundle", "edition", "model", "system", "with", "and", "the", "for", "new", "used",
}

def _clean_catalog_title(value: Optional[str], platform_name: Optional[str] = None) -> str:
    tokens = _normalize_text(value).split()
    platform_tokens = set(_normalize_text(platform_name).split())
    cleaned = []
    for token in tokens:
        if token in platform_tokens:
            continue
        if token in _TITLE_NOISE_TOKENS:
            continue
        if re.fullmatch(r"\d{2,4}(gb|tb)", token):
            continue
        if token in {"gb", "tb"}:
            continue
        cleaned.append(token)
    return " ".join(cleaned).strip()

def _catalog_match_score(query_title: str, row_title: str) -> float:
    if not query_title or not row_title:
        return 0.0
    if query_title == row_title:
        return 1.0
    q_tokens = set(query_title.split())
    r_tokens = set(row_title.split())
    overlap = len(q_tokens & r_tokens) / max(len(q_tokens), 1)
    seq = SequenceMatcher(None, query_title, row_title).ratio()
    contains_bonus = 0.85 if (query_title in row_title or row_title in query_title) else 0.0
    return max(seq, overlap * 0.9, contains_bonus)
