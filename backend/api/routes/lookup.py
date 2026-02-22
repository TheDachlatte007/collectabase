from fastapi import APIRouter

from ..errors import not_found
from ..schemas import IGDBSearch
from ...database import dict_from_row, get_db
from ...services.lookup_service import (
    get_console_image,
    lookup_combined_title,
    lookup_gametdb_title,
    lookup_igdb_title,
)

router = APIRouter()


@router.post("/api/lookup/igdb")
async def lookup_igdb(search: IGDBSearch):
    return await lookup_igdb_title(search.title)


@router.post("/api/lookup/gametdb")
async def lookup_gametdb(search: IGDBSearch):
    return await lookup_gametdb_title(search.title)


@router.post("/api/lookup/combined")
async def lookup_combined(search: IGDBSearch):
    return await lookup_combined_title(search.title)


@router.post("/api/games/{game_id}/enrich")
async def enrich_game_cover(game_id: int):
    with get_db() as db:
        row = db.execute(
            """
            SELECT g.*, p.name as platform_name
            FROM games g LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.id = ?
            """,
            (game_id,),
        ).fetchone()
        if not row:
            raise not_found("Game not found")
        game = dict_from_row(row)

    cover_url = None
    igdb = await lookup_igdb_title(game["title"])
    igdb_results = igdb.get("results", [])
    if igdb_results and igdb_results[0].get("cover_url"):
        cover_url = igdb_results[0]["cover_url"]

    if not cover_url:
        gametdb = await lookup_gametdb_title(game["title"])
        gametdb_results = gametdb.get("results", [])
        if gametdb_results and gametdb_results[0].get("cover_url"):
            cover_url = gametdb_results[0]["cover_url"]

    if not cover_url and game.get("item_type") == "console":
        cover_url = get_console_image(game.get("platform_name") or game.get("title", ""))

    if not cover_url:
        raise not_found("No cover found")

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
            SELECT g.*, p.name as platform_name
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
        igdb = await lookup_igdb_title(item["title"])
        igdb_results = igdb.get("results", [])
        if igdb_results and igdb_results[0].get("cover_url"):
            cover_url = igdb_results[0]["cover_url"]

        if not cover_url:
            gametdb = await lookup_gametdb_title(item["title"])
            gametdb_results = gametdb.get("results", [])
            if gametdb_results and gametdb_results[0].get("cover_url"):
                cover_url = gametdb_results[0]["cover_url"]

        if not cover_url and item.get("item_type") == "console":
            cover_url = get_console_image(item.get("platform_name") or item.get("title", ""))

        if cover_url:
            with get_db() as db:
                db.execute(
                    "UPDATE games SET cover_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (cover_url, item["id"]),
                )
                db.commit()
            results["success"] += 1
        else:
            results["failed"] += 1
    return results

