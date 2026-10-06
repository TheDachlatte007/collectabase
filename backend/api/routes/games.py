import json
import re
import sqlite3
from typing import Optional

from fastapi import APIRouter

from ..errors import conflict, not_found
from ..schemas import GameCreate, GameUpdate, PlatformCreate
from ...database import dict_from_row, get_db
from ...services.lookup_service import cache_remote_cover

router = APIRouter()


def _normalize_alt_titles(val) -> Optional[str]:
    if not val:
        return None
    if isinstance(val, list):
        items = [str(x).strip() for x in val if str(x).strip()]
        return json.dumps(items, ensure_ascii=False) if items else None
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        if val.startswith("[") and val.endswith("]"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    items = [str(x).strip() for x in parsed if str(x).strip()]
                    return json.dumps(items, ensure_ascii=False) if items else None
            except Exception:
                pass
        parts = [p.strip() for p in re.split(r"[,;\n]+", val) if p.strip()]
        return json.dumps(parts, ensure_ascii=False) if parts else None
    return None


def _parse_alt_titles(val) -> list[str]:
    if not val:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return []
        if val.startswith("[") and val.endswith("]"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        return [p.strip() for p in re.split(r"[,;\n]+", val) if p.strip()]
    return []


def _enhance_game_row(row_dict: dict) -> dict:
    if not row_dict:
        return row_dict
    row_dict["alt_titles_list"] = _parse_alt_titles(row_dict.get("alt_titles"))
    return row_dict


@router.get("/api/games")
async def list_games(
    platform: Optional[int] = None,
    wishlist: Optional[bool] = None,
    search: Optional[str] = None,
):
    with get_db() as db:
        query = """
            SELECT g.*, p.name as platform_name,
                   (SELECT MAX(ph.fetched_at) FROM price_history ph WHERE ph.game_id = g.id) AS last_price_at
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE 1=1
        """
        params = []

        if platform:
            query += " AND g.platform_id = ?"
            params.append(platform)
        if wishlist is not None:
            query += " AND g.is_wishlist = ?"
            params.append(1 if wishlist else 0)
        if search:
            query += " AND (g.title LIKE ? OR g.publisher LIKE ? OR g.developer LIKE ? OR COALESCE(p.name, '') LIKE ? OR COALESCE(g.item_type, '') LIKE ? OR COALESCE(g.barcode, '') LIKE ? OR COALESCE(g.location, '') LIKE ? OR COALESCE(g.alt_titles, '') LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param, search_param, search_param, search_param, search_param])

        query += " ORDER BY g.updated_at DESC"
        if search:
            query += " LIMIT 20"
        cursor = db.execute(query, tuple(params))
        return [_enhance_game_row(dict_from_row(row)) for row in cursor.fetchall()]


@router.post("/api/games")
async def create_game(game: GameCreate, force: bool = False):
    if not force:
        with get_db() as db:
            existing = db.execute(
                "SELECT id FROM games WHERE LOWER(title) = LOWER(?) AND platform_id = ?",
                (game.title, game.platform_id),
            ).fetchone()
            if existing:
                raise conflict("Game already exists", {"existing_id": existing[0]})

    # Cache remote cover image locally before saving
    cover_url = await cache_remote_cover(game.cover_url)
    alt_titles_serialized = _normalize_alt_titles(game.alt_titles)

    with get_db() as db:
        cursor = db.execute(
            '''
            INSERT INTO games (
                title, alt_titles, platform_id, item_type, quantity, barcode, igdb_id, comicvine_id, hobbydb_id, mfc_id, release_date,
                publisher, developer, genre, description, cover_url,
                region, condition, completeness, location,
                purchase_date, purchase_price, current_value, notes,
                is_wishlist, wishlist_max_price,
                character_name, series_name, scale, funko_number, vinyl_format
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                game.title,
                alt_titles_serialized,
                game.platform_id,
                game.item_type,
                game.quantity,
                game.barcode,
                game.igdb_id,
                game.comicvine_id,
                game.hobbydb_id,
                game.mfc_id,
                game.release_date,
                game.publisher,
                game.developer,
                game.genre,
                game.description,
                cover_url,
                game.region,
                game.condition,
                game.completeness,
                game.location,
                game.purchase_date,
                game.purchase_price,
                game.current_value,
                game.notes,
                1 if game.is_wishlist else 0,
                game.wishlist_max_price,
                game.character_name,
                game.series_name,
                game.scale,
                game.funko_number,
                game.vinyl_format,
            ),
        )
        db.commit()
        return {"id": cursor.lastrowid, "message": "Game created successfully"}


@router.get("/api/games/{game_id}")
async def get_game(game_id: int):
    with get_db() as db:
        cursor = db.execute(
            """
            SELECT g.*, p.name as platform_name
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.id = ?
            """,
            (game_id,),
        )
        game = dict_from_row(cursor.fetchone())
        if not game:
            raise not_found("Game not found")
        return _enhance_game_row(game)


@router.put("/api/games/{game_id}")
async def update_game(game_id: int, game: GameUpdate):
    with get_db() as db:
        existing = db.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not existing:
            raise not_found("Game not found")

        existing_data = dict_from_row(existing)

        # Cache remote cover image locally if it changed
        new_cover = game.cover_url if game.cover_url is not None else existing_data["cover_url"]
        if new_cover and new_cover != existing_data.get("cover_url"):
            new_cover = await cache_remote_cover(new_cover)

        alt_titles_val = existing_data.get("alt_titles")
        if game.alt_titles is not None:
            alt_titles_val = _normalize_alt_titles(game.alt_titles)

        merged = {
            "title": game.title or existing_data["title"],
            "alt_titles": alt_titles_val,
            "platform_id": game.platform_id if game.platform_id is not None else existing_data["platform_id"],
            "item_type": game.item_type or existing_data["item_type"],
            "quantity": game.quantity if game.quantity is not None else existing_data["quantity"],
            "barcode": game.barcode if game.barcode is not None else existing_data["barcode"],
            "igdb_id": game.igdb_id if game.igdb_id is not None else existing_data["igdb_id"],
            "comicvine_id": game.comicvine_id if game.comicvine_id is not None else existing_data["comicvine_id"],
            "hobbydb_id": game.hobbydb_id if game.hobbydb_id is not None else existing_data["hobbydb_id"],
            "mfc_id": game.mfc_id if game.mfc_id is not None else existing_data["mfc_id"],
            "release_date": game.release_date if game.release_date is not None else existing_data["release_date"],
            "publisher": game.publisher if game.publisher is not None else existing_data["publisher"],
            "developer": game.developer if game.developer is not None else existing_data["developer"],
            "genre": game.genre if game.genre is not None else existing_data["genre"],
            "description": game.description if game.description is not None else existing_data["description"],
            "cover_url": new_cover if new_cover is not None else existing_data["cover_url"],
            "region": game.region if game.region is not None else existing_data["region"],
            "condition": game.condition if game.condition is not None else existing_data["condition"],
            "completeness": game.completeness if game.completeness is not None else existing_data["completeness"],
            "location": game.location if game.location is not None else existing_data["location"],
            "purchase_date": game.purchase_date if game.purchase_date is not None else existing_data["purchase_date"],
            "purchase_price": game.purchase_price if game.purchase_price is not None else existing_data["purchase_price"],
            "current_value": game.current_value if game.current_value is not None else existing_data["current_value"],
            "notes": game.notes if game.notes is not None else existing_data["notes"],
            "is_wishlist": (
                game.is_wishlist if game.is_wishlist is not None else bool(existing_data["is_wishlist"])
            ),
            "wishlist_max_price": (
                game.wishlist_max_price
                if game.wishlist_max_price is not None
                else existing_data["wishlist_max_price"]
            ),
            "character_name": game.character_name if game.character_name is not None else existing_data.get("character_name"),
            "series_name": game.series_name if game.series_name is not None else existing_data.get("series_name"),
            "scale": game.scale if game.scale is not None else existing_data.get("scale"),
            "funko_number": game.funko_number if game.funko_number is not None else existing_data.get("funko_number"),
            "vinyl_format": game.vinyl_format if game.vinyl_format is not None else existing_data.get("vinyl_format"),
        }

        db.execute(
            """
            UPDATE games SET
                title = ?, alt_titles = ?, platform_id = ?, item_type = ?, quantity = ?, barcode = ?, igdb_id = ?, comicvine_id = ?, hobbydb_id = ?, mfc_id = ?, release_date = ?,
                publisher = ?, developer = ?, genre = ?, description = ?, cover_url = ?,
                region = ?, condition = ?, completeness = ?, location = ?,
                purchase_date = ?, purchase_price = ?, current_value = ?, notes = ?,
                is_wishlist = ?, wishlist_max_price = ?,
                character_name = ?, series_name = ?, scale = ?, funko_number = ?, vinyl_format = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                merged["title"],
                merged["alt_titles"],
                merged["platform_id"],
                merged["item_type"],
                merged["quantity"],
                merged["barcode"],
                merged["igdb_id"],
                merged["comicvine_id"],
                merged["hobbydb_id"],
                merged["mfc_id"],
                merged["release_date"],
                merged["publisher"],
                merged["developer"],
                merged["genre"],
                merged["description"],
                merged["cover_url"],
                merged["region"],
                merged["condition"],
                merged["completeness"],
                merged["location"],
                merged["purchase_date"],
                merged["purchase_price"],
                merged["current_value"],
                merged["notes"],
                1 if merged["is_wishlist"] else 0,
                merged["wishlist_max_price"],
                merged["character_name"],
                merged["series_name"],
                merged["scale"],
                merged["funko_number"],
                merged["vinyl_format"],
                game_id,
            ),
        )
        db.commit()
        return {"id": game_id, "message": "Game updated successfully"}


@router.delete("/api/games/{game_id}")
async def delete_game(game_id: int):
    with get_db() as db:
        existing = db.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if not existing:
            raise not_found("Game not found")
        db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        db.commit()
        return {"message": "Game deleted successfully"}


@router.get("/api/games/{game_id}/images")
async def get_game_images(game_id: int):
    with get_db() as db:
        cursor = db.execute(
            "SELECT id, image_url, is_primary, sort_order FROM item_images WHERE game_id = ? ORDER BY sort_order ASC, id ASC",
            (game_id,)
        )
        return [dict_from_row(row) for row in cursor.fetchall()]


@router.post("/api/games/{game_id}/images")
async def add_game_image(game_id: int, payload: dict):
    url = payload.get("image_url")
    if not url:
        raise conflict("image_url is required")

    with get_db() as db:
        existing = db.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if not existing:
            raise not_found("Game not found")

        # if it's the first image, make it primary
        count = db.execute("SELECT COUNT(*) FROM item_images WHERE game_id = ?", (game_id,)).fetchone()[0]
        is_primary = 1 if count == 0 else 0

        cursor = db.execute(
            "INSERT INTO item_images (game_id, image_url, is_primary, sort_order) VALUES (?, ?, ?, ?)",
            (game_id, url, is_primary, count)
        )
        new_id = cursor.lastrowid
        
        if is_primary:
            db.execute("UPDATE games SET cover_url = ? WHERE id = ?", (url, game_id))
            
        db.commit()
        return {"id": new_id, "image_url": url, "is_primary": bool(is_primary)}


@router.post("/api/games/{game_id}/images/{image_id}/primary")
async def set_primary_image(game_id: int, image_id: int):
    with get_db() as db:
        img = db.execute("SELECT image_url FROM item_images WHERE id = ? AND game_id = ?", (image_id, game_id)).fetchone()
        if not img:
            raise not_found("Image not found")

        db.execute("UPDATE item_images SET is_primary = 0 WHERE game_id = ?", (game_id,))
        db.execute("UPDATE item_images SET is_primary = 1 WHERE id = ?", (image_id,))
        db.execute("UPDATE games SET cover_url = ? WHERE id = ?", (img[0], game_id))
        db.commit()
        return {"message": "Primary image updated"}


@router.delete("/api/games/{game_id}/images/{image_id}")
async def delete_game_image(game_id: int, image_id: int):
    with get_db() as db:
        img = db.execute("SELECT is_primary FROM item_images WHERE id = ? AND game_id = ?", (image_id, game_id)).fetchone()
        if not img:
            raise not_found("Image not found")
        
        db.execute("DELETE FROM item_images WHERE id = ?", (image_id,))
        
        if img[0]:
            # If deleted primary, pick another one
            next_img = db.execute("SELECT id, image_url FROM item_images WHERE game_id = ? ORDER BY sort_order ASC, id ASC LIMIT 1", (game_id,)).fetchone()
            if next_img:
                db.execute("UPDATE item_images SET is_primary = 1 WHERE id = ?", (next_img[0],))
                db.execute("UPDATE games SET cover_url = ? WHERE id = ?", (next_img[1], game_id))
            else:
                db.execute("UPDATE games SET cover_url = NULL WHERE id = ?", (game_id,))
                
        db.commit()
        return {"message": "Image deleted"}


@router.get("/api/platforms")
async def list_platforms():
    with get_db() as db:
        cursor = db.execute("SELECT * FROM platforms ORDER BY name")
        return [dict_from_row(row) for row in cursor.fetchall()]


@router.get("/api/locations")
async def list_locations():
    """Return existing collection locations for form suggestions without imposing a fixed taxonomy."""
    with get_db() as db:
        rows = db.execute(
            """
            SELECT TRIM(location) AS name, COUNT(*) AS item_count
            FROM games
            WHERE TRIM(COALESCE(location, '')) != ''
            GROUP BY TRIM(location)
            ORDER BY item_count DESC, name COLLATE NOCASE ASC
            """
        ).fetchall()
        return [dict_from_row(row) for row in rows]


@router.post("/api/platforms")
async def create_platform(platform: PlatformCreate):
    with get_db() as db:
        try:
            cursor = db.execute(
                "INSERT INTO platforms (name, manufacturer, type) VALUES (?, ?, ?)",
                (platform.name, platform.manufacturer, platform.type),
            )
            db.commit()
            return {"id": cursor.lastrowid, "message": "Platform created successfully"}
        except sqlite3.IntegrityError:
            raise conflict("Platform already exists")
