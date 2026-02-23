from typing import Optional
import hashlib
import mimetypes
import os
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import httpx


CONSOLE_IMAGE_MAP = {
    "nes": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/NES-Console-Set.jpg/320px-NES-Console-Set.jpg",
    "nintendo entertainment system": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/NES-Console-Set.jpg/320px-NES-Console-Set.jpg",
    "snes": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/SNES-Mod1-Console-Set.jpg/320px-SNES-Mod1-Console-Set.jpg",
    "super nintendo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/SNES-Mod1-Console-Set.jpg/320px-SNES-Mod1-Console-Set.jpg",
    "super nintendo entertainment system": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/SNES-Mod1-Console-Set.jpg/320px-SNES-Mod1-Console-Set.jpg",
    "nintendo 64": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Nintendo-64-wController-L.jpg/320px-Nintendo-64-wController-L.jpg",
    "n64": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Nintendo-64-wController-L.jpg/320px-Nintendo-64-wController-L.jpg",
    "gamecube": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/GameCube-Console-Set.jpg/320px-GameCube-Console-Set.jpg",
    "nintendo gamecube": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/GameCube-Console-Set.jpg/320px-GameCube-Console-Set.jpg",
    "wii": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Wii-Console.jpg/240px-Wii-Console.jpg",
    "wii u": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Wii_U_Console_and_Gamepad.png/320px-Wii_U_Console_and_Gamepad.png",
    "nintendo switch": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Nintendo-Switch-wJoyCons-L-R-LR.jpg/320px-Nintendo-Switch-wJoyCons-L-R-LR.jpg",
    "nintendo switch 2": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Nintendo-Switch-wJoyCons-L-R-LR.jpg/320px-Nintendo-Switch-wJoyCons-L-R-LR.jpg",
    "game boy": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Nintendo_Gameboy.jpg/200px-Nintendo_Gameboy.jpg",
    "game boy color": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Nintendo-Game-Boy-Color-FL.jpg/220px-Nintendo-Game-Boy-Color-FL.jpg",
    "game boy advance": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Nintendo-Game-Boy-Advance-FL.jpg/250px-Nintendo-Game-Boy-Advance-FL.jpg",
    "nintendo ds": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Nintendo-DS-Lite-Black-Open.jpg/250px-Nintendo-DS-Lite-Black-Open.jpg",
    "nintendo 3ds": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Nintendo-3DS-AquaOpen.jpg/250px-Nintendo-3DS-AquaOpen.jpg",
    "playstation": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/PlayStation-SCPH-1000-with-Controller.jpg/320px-PlayStation-SCPH-1000-with-Controller.jpg",
    "playstation 2": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/PlayStation_2-Set.jpg/320px-PlayStation_2-Set.jpg",
    "playstation 3": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/PlayStation_3.png/320px-PlayStation_3.png",
    "playstation 4": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/PlayStation_4_and_DualShock_4.jpg/320px-PlayStation_4_and_DualShock_4.jpg",
    "playstation 5": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/PlayStation_5_and_DualSense.jpg/320px-PlayStation_5_and_DualSense.jpg",
    "psp": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/PSP-1000.jpg/320px-PSP-1000.jpg",
    "ps vita": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/PS-Vita-1101-FL.jpg/320px-PS-Vita-1101-FL.jpg",
    "xbox": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Xbox-Console-Set.jpg/320px-Xbox-Console-Set.jpg",
    "xbox 360": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Xbox-360-S-Console.jpg/320px-Xbox-360-S-Console.jpg",
    "xbox one": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/XBox-One.jpg/320px-XBox-One.jpg",
    "xbox series x/s": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Xbox_Series_X_%26_S.jpg/320px-Xbox_Series_X_%26_S.jpg",
    "sega master system": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Sega-Master-System-Set.jpg/320px-Sega-Master-System-Set.jpg",
    "sega genesis/mega drive": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Sega-Genesis-Mod1-Bare.jpg/320px-Sega-Genesis-Mod1-Bare.jpg",
    "sega saturn": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Sega-Saturn-JP-Mk1-Console-Set.jpg/320px-Sega-Saturn-JP-Mk1-Console-Set.jpg",
    "sega dreamcast": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Dreamcast-Console-Set.jpg/320px-Dreamcast-Console-Set.jpg",
    "sega game gear": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Game-Gear-Handheld.jpg/280px-Game-Gear-Handheld.jpg",
}

_igdb_token_cache = {"token": None, "expires_at": 0.0, "client_id": None}
CONSOLE_ALIASES = {
    "ps5": "playstation 5",
    "ps4": "playstation 4",
    "ps3": "playstation 3",
    "ps2": "playstation 2",
    "series x": "xbox series x/s",
    "series s": "xbox series x/s",
    "xbox series x": "xbox series x/s",
    "xbox series s": "xbox series x/s",
    "xbox one s": "xbox one",
    "xbox one x": "xbox one",
}


def _normalize_platform_name(value: str) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_NORMALIZED_CONSOLE_IMAGE_MAP = {
    _normalize_platform_name(k): v for k, v in CONSOLE_IMAGE_MAP.items()
}


def get_console_image(platform_name: str) -> Optional[str]:
    normalized = _normalize_platform_name(platform_name)
    if not normalized:
        return None

    direct = _NORMALIZED_CONSOLE_IMAGE_MAP.get(normalized)
    if direct:
        return direct

    alias_target = CONSOLE_ALIASES.get(normalized)
    if alias_target:
        alias_url = _NORMALIZED_CONSOLE_IMAGE_MAP.get(_normalize_platform_name(alias_target))
        if alias_url:
            return alias_url

    for alias, target in CONSOLE_ALIASES.items():
        if alias in normalized:
            alias_url = _NORMALIZED_CONSOLE_IMAGE_MAP.get(_normalize_platform_name(target))
            if alias_url:
                return alias_url

    # Fallback: fuzzy containment (e.g. "xbox one 500gb", "xbox one wireless controller")
    for key, url in sorted(_NORMALIZED_CONSOLE_IMAGE_MAP.items(), key=lambda kv: len(kv[0]), reverse=True):
        if key and key in normalized:
            return url

    return None


def _uploads_dir() -> str:
    default_uploads = "/app/uploads" if Path("/app").exists() else str(Path(__file__).resolve().parents[2] / "uploads")
    return os.getenv("UPLOADS_DIR", default_uploads)


def _cover_extension(url: str, content_type: str) -> str:
    ctype = (content_type or "").split(";", 1)[0].strip().lower()
    if ctype in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    if ctype == "image/png":
        return ".png"
    if ctype == "image/webp":
        return ".webp"
    if ctype == "image/gif":
        return ".gif"

    path_ext = Path(urlparse(url).path).suffix.lower()
    if path_ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if path_ext == ".jpeg" else path_ext

    guessed = (mimetypes.guess_extension(ctype) or "").lower()
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if guessed == ".jpeg" else guessed
    return ".jpg"


async def cache_remote_cover(url: Optional[str]) -> Optional[str]:
    """
    Cache a remote cover image locally under UPLOADS_DIR.
    Returns /uploads/... on success, otherwise original URL.
    """
    if not url:
        return url
    if not str(url).startswith(("http://", "https://")):
        return url

    try:
        uploads_dir = _uploads_dir()
        os.makedirs(uploads_dir, exist_ok=True)

        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": "Collectabase/1.0"}) as client:
            res = await client.get(url)
        if res.status_code >= 400:
            return url

        body = res.content or b""
        if not body or len(body) > 8 * 1024 * 1024:
            return url

        ext = _cover_extension(str(url), res.headers.get("content-type", ""))
        digest = hashlib.sha1(str(url).encode("utf-8")).hexdigest()
        filename = f"{digest}{ext}"
        path = Path(uploads_dir) / filename

        if not path.exists():
            path.write_bytes(body)

        return f"/uploads/{filename}"
    except Exception:
        return url


async def lookup_igdb_title(title: str):
    client_id = os.getenv("IGDB_CLIENT_ID")
    client_secret = os.getenv("IGDB_CLIENT_SECRET")
    if not client_id or not client_secret:
        return {"error": "IGDB credentials not configured", "results": []}

    try:
        async with httpx.AsyncClient() as client:
            now = time.time()
            token_valid = (
                _igdb_token_cache.get("token")
                and _igdb_token_cache.get("expires_at", 0) > now
                and _igdb_token_cache.get("client_id") == client_id
            )

            if token_valid:
                access_token = _igdb_token_cache["token"]
            else:
                token_response = await client.post(
                    "https://id.twitch.tv/oauth2/token",
                    params={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "client_credentials",
                    },
                )
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 0)
                if not access_token:
                    return {"error": "Failed to get IGDB access token", "results": []}
                _igdb_token_cache["token"] = access_token
                _igdb_token_cache["client_id"] = client_id
                _igdb_token_cache["expires_at"] = now + max(int(expires_in) - 60, 0)

            headers = {"Client-ID": client_id, "Authorization": f"Bearer {access_token}"}
            query = (
                f'search "{title}"; fields '
                "name,first_release_date,genres.name,platforms.name,cover.url,summary,"
                "involved_companies.company.name; limit 5;"
            )
            games_response = await client.post(
                "https://api.igdb.com/v4/games", headers=headers, content=query
            )
            games = games_response.json()
            results = []
            for game in games:
                raw_url = game.get("cover", {}).get("url", "") if game.get("cover") else None
                companies = game.get("involved_companies", [])
                developer = next(
                    (c["company"]["name"] for c in companies if c.get("developer") and c.get("company")),
                    None,
                )
                publisher = next(
                    (c["company"]["name"] for c in companies if c.get("publisher") and c.get("company")),
                    None,
                )
                results.append(
                    {
                        "source": "igdb",
                        "igdb_id": game.get("id"),
                        "title": game.get("name"),
                        "release_date": game.get("first_release_date"),
                        "genre": ", ".join([g.get("name", "") for g in game.get("genres", [])]),
                        "platforms": [p.get("name", "") for p in game.get("platforms", [])],
                        "cover_url": ("https:" + raw_url.replace("t_thumb", "t_cover_big")) if raw_url else None,
                        "description": game.get("summary", ""),
                        "developer": developer,
                        "publisher": publisher,
                    }
                )
            return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}


async def lookup_gametdb_title(title: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.gametdb.com/api.php",
                params={"xml": 1, "lang": "EN", "name": title, "region": "EN"},
                headers={"User-Agent": "Collectabase/1.0"},
            )
            if response.status_code != 200:
                return {"results": []}

            root = ET.fromstring(response.text)
            results = []
            for game in root.findall(".//game")[:5]:
                game_id = game.findtext("id", "")
                platform_elem = game.findtext("type", "")
                title_text = game.findtext('locale[@lang="EN"]/title') or game.findtext("title", "")
                cover_url = None
                if game_id and platform_elem:
                    cover_url = f"https://art.gametdb.com/{platform_elem}/cover/EN/{game_id}.png"
                results.append(
                    {
                        "source": "gametdb",
                        "gametdb_id": game_id,
                        "title": title_text,
                        "platform": platform_elem,
                        "cover_url": cover_url,
                        "cover_front": f"https://art.gametdb.com/{platform_elem}/coverfull/EN/{game_id}.png"
                        if game_id
                        else None,
                        "disc_art": f"https://art.gametdb.com/{platform_elem}/disc/EN/{game_id}.png"
                        if game_id
                        else None,
                    }
                )
            return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}


async def lookup_combined_title(title: str):
    igdb = await lookup_igdb_title(title)
    gametdb = await lookup_gametdb_title(title)
    return {
        "igdb": igdb.get("results", []),
        "gametdb": gametdb.get("results", []),
        "errors": {
            "igdb": igdb.get("error"),
            "gametdb": gametdb.get("error"),
        },
    }


def normalize_barcode(value: str) -> str:
    return re.sub(r"\D+", "", str(value or ""))


async def lookup_upcitemdb_barcode(barcode: str):
    normalized = normalize_barcode(barcode)
    if len(normalized) < 8:
        return {"results": [], "error": "invalid_barcode"}

    api_key = os.getenv("UPCITEMDB_API_KEY", "").strip()
    endpoint = "https://api.upcitemdb.com/prod/v1/lookup" if api_key else "https://api.upcitemdb.com/prod/trial/lookup"
    headers = {
        "User-Agent": "Collectabase/1.0",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = api_key

    try:
        async with httpx.AsyncClient(timeout=12, headers=headers) as client:
            response = await client.get(endpoint, params={"upc": normalized})
        if response.status_code >= 400:
            return {"results": [], "error": f"upcitemdb_status_{response.status_code}"}

        payload = response.json()
        items = payload.get("items", []) if isinstance(payload, dict) else []
        results = []
        for item in items[:5]:
            title = (item.get("title") or item.get("product_name") or "").strip()
            if not title:
                continue
            images = item.get("images") or []
            results.append(
                {
                    "source": "upcitemdb",
                    "title": title,
                    "brand": item.get("brand"),
                    "description": item.get("description") or item.get("category"),
                    "cover_url": images[0] if images else None,
                }
            )
        return {"results": results, "error": None}
    except Exception as e:
        return {"results": [], "error": str(e)}
