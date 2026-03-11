from fastapi import APIRouter

from ...database import dict_from_row, get_db

router = APIRouter()


@router.get("/api/stats")
async def get_stats():
    with get_db() as db:
        total_games = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 0").fetchone()[0]
        total_value = db.execute(
            "SELECT COALESCE(SUM(COALESCE(current_value, 0) * quantity), 0) FROM games WHERE is_wishlist = 0"
        ).fetchone()[0]
        purchase_value = db.execute(
            "SELECT COALESCE(SUM(COALESCE(purchase_price, 0) * quantity), 0) FROM games WHERE is_wishlist = 0"
        ).fetchone()[0]
        wishlist_count = db.execute("SELECT COUNT(*) FROM games WHERE is_wishlist = 1").fetchone()[0]

        cursor = db.execute(
            """
            SELECT p.name,
                   SUM(g.quantity) as count,
                   COALESCE(SUM(COALESCE(g.current_value, 0) * g.quantity), 0) as value,
                   COALESCE(SUM(COALESCE(g.purchase_price, 0) * g.quantity), 0) as invested
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
            SELECT condition, SUM(quantity) as count
            FROM games
            WHERE is_wishlist = 0 AND condition IS NOT NULL
            GROUP BY condition
            """
        )
        by_condition = [dict_from_row(row) for row in cursor.fetchall()]

        cursor = db.execute(
            """
            SELECT item_type, SUM(quantity) as count,
                   COALESCE(SUM(COALESCE(current_value, 0) * quantity), 0) as value,
                   COALESCE(SUM(COALESCE(purchase_price, 0) * quantity), 0) as invested
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

        cursor = db.execute(
            """
            SELECT id, title, cover_url, current_value, purchase_price, 
                   COALESCE(current_value, 0) - COALESCE(purchase_price, 0) as profit_loss
            FROM games
            WHERE is_wishlist = 0
            ORDER BY current_value DESC
            LIMIT 15
            """
        )
        top_valuable = [dict_from_row(row) for row in cursor.fetchall()]

        cursor = db.execute(
            """
            SELECT id, title, cover_url, current_value, purchase_price, 
                   (COALESCE(current_value, 0) - COALESCE(purchase_price, 0)) as profit_loss,
                   CASE WHEN COALESCE(purchase_price, 0) > 0 
                        THEN ((COALESCE(current_value, 0) - purchase_price) / purchase_price) * 100 
                        ELSE 0 END as percent_gain
            FROM games
            WHERE is_wishlist = 0 AND purchase_price > 0
            ORDER BY percent_gain DESC
            LIMIT 15
            """
        )
        top_gainers = [dict_from_row(row) for row in cursor.fetchall()]

    return {
        "total_games": total_games,
        "total_value": round(total_value, 2),
        "purchase_value": round(purchase_value, 2),
        "profit_loss": round(total_value - purchase_value, 2),
        "wishlist_count": wishlist_count,
        "by_platform": by_platform,
        "by_condition": by_condition,
        "by_type": by_type,
        "top_valuable": top_valuable,
        "top_gainers": top_gainers,
    }


@router.get("/api/stats/history")
async def get_stats_history(days: int = 30):
    with get_db() as db:
        cursor = db.execute(
            """
            SELECT recorded_at, total_value, game_value, hardware_value
            FROM value_history
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (days,)
        )
        rows = cursor.fetchall()

    history = []
    for row in reversed(rows):
        item = dict_from_row(row)
        history.append({
            "date": item["recorded_at"],
            "total": round(item.get("total_value") or 0, 2),
            "games": round(item.get("game_value") or 0, 2),
            "hardware": round(item.get("hardware_value") or 0, 2),
        })

    return history
