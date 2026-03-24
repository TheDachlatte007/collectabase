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
            SELECT COALESCE(p.name, 'No Platform') as name,
                   SUM(g.quantity) as count,
                   COALESCE(SUM(COALESCE(g.current_value, 0) * g.quantity), 0) as value,
                   COALESCE(SUM(COALESCE(g.purchase_price, 0) * g.quantity), 0) as invested
            FROM games g
            LEFT JOIN platforms p ON g.platform_id = p.id
            WHERE g.is_wishlist = 0
              AND COALESCE(g.item_type, 'game') IN ('game', 'console', 'controller', 'accessory')
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

        lots_overview = []
        lots_summary = {
            "total_lots": 0,
            "item_count": 0,
            "total_cost_basis": 0.0,
            "net_sales": 0.0,
            "realized_profit": 0.0,
            "remaining_cost_basis": 0.0,
            "expected_remaining_value": 0.0,
            "break_even_gap": 0.0,
        }

        try:
            cursor = db.execute(
                """
                SELECT
                    l.id,
                    l.name,
                    l.purchase_date,
                    COALESCE(l.purchase_price_gross, 0) + COALESCE(l.shipping_in, 0)
                      + COALESCE(l.fees_in, 0) + COALESCE(l.other_costs, 0) AS total_cost_basis,
                    COUNT(li.id) AS item_count,
                    COALESCE(SUM(CASE WHEN ls.id IS NOT NULL THEN ls.net_proceeds ELSE 0 END), 0) AS net_sales,
                    COALESCE(SUM(CASE WHEN ls.id IS NOT NULL THEN ls.realized_profit ELSE 0 END), 0) AS realized_profit,
                    COALESCE(SUM(CASE WHEN ls.id IS NULL AND COALESCE(li.status, 'inventory') != 'discarded'
                                      THEN COALESCE(li.allocated_cost_basis, 0) ELSE 0 END), 0) AS remaining_cost_basis,
                    COALESCE(SUM(CASE WHEN ls.id IS NULL AND COALESCE(li.status, 'inventory') != 'discarded'
                                      THEN COALESCE(li.estimated_value, 0) ELSE 0 END), 0) AS expected_remaining_value
                FROM lots l
                LEFT JOIN lot_items li ON li.lot_id = l.id
                LEFT JOIN lot_sales ls ON ls.lot_item_id = li.id
                GROUP BY l.id, l.name, l.purchase_date, l.purchase_price_gross, l.shipping_in, l.fees_in, l.other_costs
                ORDER BY realized_profit DESC, net_sales DESC, l.updated_at DESC
                """
            )
            for row in cursor.fetchall():
                item = dict_from_row(row)
                total_cost_basis = round(float(item.get("total_cost_basis") or 0), 2)
                net_sales_value = round(float(item.get("net_sales") or 0), 2)
                realized_profit_value = round(float(item.get("realized_profit") or 0), 2)
                remaining_cost_basis_value = round(float(item.get("remaining_cost_basis") or 0), 2)
                expected_remaining_value = round(float(item.get("expected_remaining_value") or 0), 2)
                lots_overview.append(
                    {
                        **item,
                        "total_cost_basis": total_cost_basis,
                        "net_sales": net_sales_value,
                        "realized_profit": realized_profit_value,
                        "remaining_cost_basis": remaining_cost_basis_value,
                        "expected_remaining_value": expected_remaining_value,
                        "break_even_gap": round(max(total_cost_basis - net_sales_value, 0), 2),
                        "recovery_rate_pct": round((net_sales_value / total_cost_basis) * 100, 1) if total_cost_basis else 0.0,
                    }
                )

            if lots_overview:
                lots_summary = {
                    "total_lots": len(lots_overview),
                    "item_count": int(sum(int(item.get("item_count") or 0) for item in lots_overview)),
                    "total_cost_basis": round(sum(item["total_cost_basis"] for item in lots_overview), 2),
                    "net_sales": round(sum(item["net_sales"] for item in lots_overview), 2),
                    "realized_profit": round(sum(item["realized_profit"] for item in lots_overview), 2),
                    "remaining_cost_basis": round(sum(item["remaining_cost_basis"] for item in lots_overview), 2),
                    "expected_remaining_value": round(sum(item["expected_remaining_value"] for item in lots_overview), 2),
                    "break_even_gap": round(sum(item["break_even_gap"] for item in lots_overview), 2),
                }
        except Exception:
            lots_overview = []

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
        "lots_summary": lots_summary,
        "lots_overview": lots_overview,
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
