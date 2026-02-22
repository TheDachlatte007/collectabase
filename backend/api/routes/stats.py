from fastapi import APIRouter

from ...database import dict_from_row, get_db

router = APIRouter()


@router.get("/api/stats")
async def get_stats():
    with get_db() as db:
        total_games = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 0").fetchone()[0]
        total_value = db.execute("SELECT COALESCE(SUM(current_value), 0) FROM games WHERE is_wishlist = 0").fetchone()[0]
        purchase_value = db.execute("SELECT COALESCE(SUM(purchase_price), 0) FROM games WHERE is_wishlist = 0").fetchone()[0]
        wishlist_count = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 1").fetchone()[0]

        cursor = db.execute(
            """
            SELECT p.name, COUNT(*) as count, SUM(g.current_value) as value
            FROM games g
            JOIN platforms p ON g.platform_id = p.id
            WHERE g.is_wishlist = 0
            GROUP BY p.name
            ORDER BY count DESC
            """
        )
        by_platform = [dict_from_row(row) for row in cursor.fetchall()]

        cursor = db.execute(
            """
            SELECT condition, COUNT(*) as count
            FROM games
            WHERE is_wishlist = 0 AND condition IS NOT NULL
            GROUP BY condition
            """
        )
        by_condition = [dict_from_row(row) for row in cursor.fetchall()]

        cursor = db.execute(
            """
            SELECT item_type, COUNT(*) as count,
                   COALESCE(SUM(current_value), 0) as value,
                   COALESCE(SUM(purchase_price), 0) as invested
            FROM games
            WHERE is_wishlist = 0
            GROUP BY item_type
            ORDER BY count DESC
            """
        )
        by_type = [dict_from_row(row) for row in cursor.fetchall()]

    return {
        "total_games": total_games,
        "total_value": round(total_value, 2),
        "purchase_value": round(purchase_value, 2),
        "profit_loss": round(total_value - purchase_value, 2),
        "wishlist_count": wishlist_count,
        "by_platform": by_platform,
        "by_condition": by_condition,
        "by_type": by_type,
    }

