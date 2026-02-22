import os

from fastapi import APIRouter

from ...database import get_db

router = APIRouter()


@router.get("/api/settings/info")
async def settings_info():
    client_id = os.getenv("IGDB_CLIENT_ID")
    db_path = os.getenv("DATABASE_URL", "sqlite:////app/app/data/games.db").replace("sqlite:///", "")
    try:
        db_size_bytes = os.path.getsize(db_path)
        if db_size_bytes < 1024 * 1024:
            db_size = f"{db_size_bytes / 1024:.1f} KB"
        else:
            db_size = f"{db_size_bytes / 1024 / 1024:.1f} MB"
    except Exception:
        db_size = "Unknown"

    with get_db() as db:
        total_items = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 0").fetchone()[0]
        missing_covers = db.execute(
            "SELECT COUNT(*) FROM games WHERE (cover_url IS NULL OR cover_url = '') AND is_wishlist = 0"
        ).fetchone()[0]
        wishlist_count = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 1").fetchone()[0]

    return {
        "version": "1.0.0",
        "igdb_configured": bool(client_id),
        "total_items": total_items,
        "missing_covers": missing_covers,
        "wishlist_count": wishlist_count,
        "db_size": db_size,
    }


@router.post("/api/settings/clear-covers")
async def clear_all_covers():
    with get_db() as db:
        db.execute("UPDATE games SET cover_url = NULL")
        db.commit()
    return {"message": "All covers cleared"}


@router.delete("/api/database/clear")
async def clear_database():
    with get_db() as db:
        db.execute("DELETE FROM games")
        db.commit()
    return {"message": "Database cleared successfully"}

