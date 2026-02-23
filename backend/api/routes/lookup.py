from datetime import datetime, timezone

from fastapi import APIRouter

from ..errors import bad_request, not_found
from ..schemas import BarcodeLookup, IGDBSearch
from ...database import dict_from_row, get_db, set_app_meta
from ...services.lookup_service import (
    cache_remote_cover,
    get_console_image,
    lookup_upcitemdb_barcode,
    lookup_combined_title,
    lookup_gametdb_title,
    lookup_igdb_title,
    normalize_barcode,
)

router = APIRouter()


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().replace("/", " ").replace("-", " ").split())


def _should_use_console_placeholder(item: dict) -> bool:
    item_type = str(item.get("item_type") or "").lower()
    if item_type in {"console", "accessory"}:
        return True

    title = _normalize_text(item.get("title") or "")
    platform = _normalize_text(item.get("platform_name") or "")

    keyword_hits = [
        "console",
        "system",
        "bundle",
        "controller",
        "gamepad",
        "joy con",
        "wireless",
        "handheld",
    ]
    if any(k in title for k in keyword_hits):
        return True

    # Imported console titles are often "platform + capacity/model" while item_type may still be "game".
    if platform and platform in title and any(k in title for k in ["gb", "tb", "model", "edition", "set"]):
        return True

    return False


@router.post("/api/lookup/igdb")
async def lookup_igdb(search: IGDBSearch):
    return await lookup_igdb_title(search.title)


@router.post("/api/lookup/gametdb")
async def lookup_gametdb(search: IGDBSearch):
    return await lookup_gametdb_title(search.title)


@router.post("/api/lookup/combined")
async def lookup_combined(search: IGDBSearch):
    return await lookup_combined_title(search.title)


@router.post("/api/lookup/barcode")
async def lookup_barcode(search: BarcodeLookup):
    normalized = normalize_barcode(search.barcode)
    if len(normalized) < 8:
        raise bad_request("Invalid barcode. Please scan a valid UPC/EAN code.")

    with get_db() as db:
        existing = db.execute(
            """
            SELECT g.id, g.title, g.platform_id, g.barcode, g.cover_url, p.name AS platform_name
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE REPLACE(REPLACE(REPLACE(COALESCE(g.barcode, ''), ' ', ''), '-', ''), '.', '') = ?
            ORDER BY g.updated_at DESC
            LIMIT 1
            """,
            (normalized,),
        ).fetchone()

    existing_item = dict_from_row(existing) if existing else None

    upc_lookup = await lookup_upcitemdb_barcode(normalized)
    upc_results = upc_lookup.get("results", [])
    upc_error = upc_lookup.get("error")

    # EAN/UPC variants often differ by one leading zero.
    if not upc_results:
        alt = None
        if len(normalized) == 12:
            alt = f"0{normalized}"
        elif len(normalized) == 13 and normalized.startswith("0"):
            alt = normalized[1:]
        if alt:
            alt_lookup = await lookup_upcitemdb_barcode(alt)
            if alt_lookup.get("results"):
                upc_results = alt_lookup.get("results", [])
                upc_error = alt_lookup.get("error")

    title_candidates = []
    seen_titles = set()
    for item in upc_results:
        title = str(item.get("title") or "").strip()
        key = title.lower()
        if title and key not in seen_titles:
            title_candidates.append(title)
            seen_titles.add(key)

    lookup_title = title_candidates[0] if title_candidates else None
    suggestions = []
    combined_errors = {"igdb": None, "gametdb": None}
    if lookup_title:
        combined = await lookup_combined_title(lookup_title)
        combined_errors = combined.get("errors", combined_errors)
        suggestions = [*(combined.get("igdb", [])), *(combined.get("gametdb", []))]

    return {
        "barcode": search.barcode,
        "normalized_barcode": normalized,
        "existing": existing_item,
        "lookup_title": lookup_title,
        "title_candidates": title_candidates,
        "suggestions": suggestions[:8],
        "external_matches": upc_results,
        "errors": {
            "upcitemdb": upc_error,
            "igdb": combined_errors.get("igdb"),
            "gametdb": combined_errors.get("gametdb"),
        },
    }


@router.post("/api/games/{game_id}/enrich")
async def enrich_game_cover(game_id: int):
    with get_db() as db:
        row = db.execute(
            """
            SELECT g.*, p.name as platform_name, p.type as platform_type
            FROM games g LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.id = ?
            """,
            (game_id,),
        ).fetchone()
        if not row:
            raise not_found("Game not found")
        game = dict_from_row(row)

    cover_url = None
    if _should_use_console_placeholder(game):
        cover_url = get_console_image(game.get("platform_name") or game.get("title", ""))

    igdb = await lookup_igdb_title(game["title"])
    igdb_results = igdb.get("results", [])
    if not cover_url and igdb_results and igdb_results[0].get("cover_url"):
        cover_url = igdb_results[0]["cover_url"]

    if not cover_url:
        gametdb = await lookup_gametdb_title(game["title"])
        gametdb_results = gametdb.get("results", [])
        if gametdb_results and gametdb_results[0].get("cover_url"):
            cover_url = gametdb_results[0]["cover_url"]

    if not cover_url and _should_use_console_placeholder(game):
        cover_url = get_console_image(game.get("platform_name") or game.get("title", ""))

    if not cover_url:
        raise not_found("No cover found")

    cover_url = await cache_remote_cover(cover_url)

    with get_db() as db:
        db.execute(
            "UPDATE games SET cover_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (cover_url, game_id),
        )
        db.commit()
    return {"cover_url": cover_url}


@router.post("/api/games/{game_id}/cover-placeholder")
async def set_console_placeholder_cover(game_id: int):
    with get_db() as db:
        row = db.execute(
            """
            SELECT g.*, p.name as platform_name, p.type as platform_type
            FROM games g LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.id = ?
            """,
            (game_id,),
        ).fetchone()
        if not row:
            raise not_found("Game not found")
        item = dict_from_row(row)

    cover_url = get_console_image(item.get("platform_name") or item.get("title", ""))
    if not cover_url:
        raise not_found("No console placeholder available for this item")

    cover_url = await cache_remote_cover(cover_url)
    with get_db() as db:
        db.execute(
            "UPDATE games SET cover_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (cover_url, game_id),
        )
        db.commit()
    return {"cover_url": cover_url}


@router.post("/api/enrich/all")
async def enrich_all_covers(limit: int = 20):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT g.*, p.name as platform_name, p.type as platform_type
            FROM games g LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE (g.cover_url IS NULL OR g.cover_url = '') AND g.is_wishlist = 0
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        items = [dict_from_row(row) for row in rows]

    results = {"success": 0, "failed": 0, "total": len(items)}
    for item in items:
        cover_url = None
        if _should_use_console_placeholder(item):
            cover_url = get_console_image(item.get("platform_name") or item.get("title", ""))

        igdb = await lookup_igdb_title(item["title"])
        igdb_results = igdb.get("results", [])
        if not cover_url and igdb_results and igdb_results[0].get("cover_url"):
            cover_url = igdb_results[0]["cover_url"]

        if not cover_url:
            gametdb = await lookup_gametdb_title(item["title"])
            gametdb_results = gametdb.get("results", [])
            if gametdb_results and gametdb_results[0].get("cover_url"):
                cover_url = gametdb_results[0]["cover_url"]

        if not cover_url and _should_use_console_placeholder(item):
            cover_url = get_console_image(item.get("platform_name") or item.get("title", ""))

        if cover_url:
            cover_url = await cache_remote_cover(cover_url)
            with get_db() as db:
                db.execute(
                    "UPDATE games SET cover_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (cover_url, item["id"]),
                )
                db.commit()
            results["success"] += 1
        else:
            results["failed"] += 1

    finished_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    set_app_meta("last_bulk_enrich_at", finished_at)
    set_app_meta("last_bulk_enrich_success", results["success"])
    set_app_meta("last_bulk_enrich_failed", results["failed"])
    set_app_meta("last_bulk_enrich_total", results["total"])

    return results
