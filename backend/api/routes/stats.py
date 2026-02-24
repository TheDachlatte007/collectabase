from fastapi import APIRouter

from ...database import dict_from_row, get_db

router = APIRouter()


@router.get("/api/stats")
async def get_stats():
    with get_db() as db:
        total_games = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 0").fetchone()[0]
        total_value = db.execute(
            "SELECT COALESCE(SUM(COALESCE(current_value, 0)), 0) FROM games WHERE is_wishlist = 0"
        ).fetchone()[0]
        purchase_value = db.execute(
            "SELECT COALESCE(SUM(COALESCE(purchase_price, 0)), 0) FROM games WHERE is_wishlist = 0"
        ).fetchone()[0]
        wishlist_count = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 1").fetchone()[0]

        cursor = db.execute(
            """
            SELECT p.name,
                   COUNT(*) as count,
                   COALESCE(SUM(COALESCE(g.current_value, 0)), 0) as value,
                   COALESCE(SUM(COALESCE(g.purchase_price, 0)), 0) as invested
            FROM games g
            JOIN platforms p ON g.platform_id = p.id
            WHERE g.is_wishlist = 0
            GROUP BY p.name
            ORDER BY count DESC
            """
        )
        by_platform = []
        for row in cursor.fetchall():
            item = dict_from_row(row)
            value = float(item.get("value") or 0)
            invested = float(item.get("invested") or 0)
            item["value"] = round(value, 2)
            item["invested"] = round(invested, 2)
            item["profit_loss"] = round(value - invested, 2)
            by_platform.append(item)

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
                   COALESCE(SUM(COALESCE(current_value, 0)), 0) as value,
                   COALESCE(SUM(COALESCE(purchase_price, 0)), 0) as invested
            FROM games
            WHERE is_wishlist = 0
            GROUP BY item_type
            ORDER BY count DESC
            """
        )
        by_type = []
        for row in cursor.fetchall():
            item = dict_from_row(row)
            item["value"] = round(float(item.get("value") or 0), 2)
            item["invested"] = round(float(item.get("invested") or 0), 2)
            by_type.append(item)

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
