from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import APIRouter

from ..errors import bad_request, not_found
from ..schemas import LotCreate, LotItemCreate, LotItemUpdate, LotSaleUpsert, LotUpdate
from ...database import dict_from_row, get_db

router = APIRouter()

VALID_ITEM_STATUSES = {"inventory", "sold", "kept", "discarded"}


def _money(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return round(default, 2)
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _nullable_money(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return _money(value)


def _lot_total_cost(row: dict) -> float:
    return round(
        _money(row.get("purchase_price_gross"))
        + _money(row.get("shipping_in"))
        + _money(row.get("fees_in"))
        + _money(row.get("other_costs")),
        2,
    )


def _ensure_status(status: str | None) -> str:
    normalized = str(status or "inventory").strip().lower()
    if normalized not in VALID_ITEM_STATUSES:
        raise bad_request(f"Invalid item status '{status}'")
    return normalized


def _get_lot_or_404(db, lot_id: int) -> dict:
    row = db.execute("SELECT * FROM lots WHERE id = ?", (lot_id,)).fetchone()
    lot = dict_from_row(row)
    if not lot:
        raise not_found("Lot not found")
    return lot


def _get_lot_item_or_404(db, item_id: int) -> dict:
    row = db.execute("SELECT * FROM lot_items WHERE id = ?", (item_id,)).fetchone()
    item = dict_from_row(row)
    if not item:
        raise not_found("Lot item not found")
    return item


def _load_lot_items(db, lot_id: int) -> list[dict]:
    cursor = db.execute(
        """
        SELECT li.*, g.title AS linked_game_title, p.name AS linked_platform_name
        FROM lot_items li
        LEFT JOIN games g ON li.game_id = g.id
        LEFT JOIN platforms p ON g.platform_id = p.id
        WHERE li.lot_id = ?
        ORDER BY li.id ASC
        """,
        (lot_id,),
    )
    return [dict_from_row(row) for row in cursor.fetchall()]


def _load_sale_for_item(db, item_id: int) -> dict | None:
    row = db.execute("SELECT * FROM lot_sales WHERE lot_item_id = ?", (item_id,)).fetchone()
    return dict_from_row(row) if row else None


def _recalculate_lot_allocations(db, lot_id: int) -> None:
    lot = _get_lot_or_404(db, lot_id)
    items = _load_lot_items(db, lot_id)
    if not items:
        return

    total_cost = _lot_total_cost(lot)
    manual_items = [item for item in items if item.get("cost_basis_override") is not None]
    automatic_items = [item for item in items if item.get("cost_basis_override") is None]
    manual_total = round(sum(_money(item.get("cost_basis_override")) for item in manual_items), 2)

    if manual_total > total_cost + 0.009:
        raise bad_request("Manual cost basis overrides exceed the total lot cost")

    for item in manual_items:
        allocated = _money(item.get("cost_basis_override"))
        db.execute(
            """
            UPDATE lot_items
            SET allocated_cost_basis = ?, allocation_method = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (allocated, "manual", item["id"]),
        )

    if not automatic_items:
        return

    remaining_pool = round(total_cost - manual_total, 2)
    positive_estimates = [_money(item.get("estimated_value")) for item in automatic_items if _money(item.get("estimated_value")) > 0]
    use_estimated = len(positive_estimates) > 0
    weights = []
    if use_estimated:
        total_weight = round(sum(_money(item.get("estimated_value")) for item in automatic_items), 2)
        if total_weight <= 0:
            use_estimated = False
    if use_estimated:
        for item in automatic_items:
            weights.append(_money(item.get("estimated_value")))
    else:
        weights = [1.0 for _ in automatic_items]
    total_weight = sum(weights)

    allocated_sum = 0.0
    for index, item in enumerate(automatic_items):
        if index == len(automatic_items) - 1:
            allocated = round(remaining_pool - allocated_sum, 2)
        else:
            share = 0 if total_weight == 0 else remaining_pool * (weights[index] / total_weight)
            allocated = _money(share)
            allocated_sum = round(allocated_sum + allocated, 2)
        db.execute(
            """
            UPDATE lot_items
            SET allocated_cost_basis = ?, allocation_method = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (allocated, "estimated" if use_estimated else "equal", item["id"]),
        )


def _build_lot_payload(db, lot: dict) -> dict:
    lot_id = lot["id"]
    total_cost_basis = _lot_total_cost(lot)
    items = _load_lot_items(db, lot_id)
    payload_items = []
    sales = []

    sold_count = 0
    inventory_count = 0
    kept_count = 0
    discarded_count = 0
    estimated_total_value = 0.0
    allocated_total = 0.0
    net_sales = 0.0
    realized_profit = 0.0
    remaining_cost_basis = 0.0
    written_off_cost_basis = 0.0
    expected_remaining_value = 0.0

    for item in items:
        sale = _load_sale_for_item(db, item["id"])
        estimated_value = _nullable_money(item.get("estimated_value"))
        allocated_cost_basis = _money(item.get("allocated_cost_basis"))
        estimated_total_value += estimated_value or 0.0
        allocated_total += allocated_cost_basis

        if sale:
            sold_count += 1
            net_sales += _money(sale.get("net_proceeds"))
            realized_profit += _money(sale.get("realized_profit"))
        else:
            status = item.get("status") or "inventory"
            if status == "discarded":
                discarded_count += 1
                written_off_cost_basis += allocated_cost_basis
            elif status == "kept":
                kept_count += 1
                remaining_cost_basis += allocated_cost_basis
                expected_remaining_value += estimated_value or 0.0
            else:
                inventory_count += 1
                remaining_cost_basis += allocated_cost_basis
                expected_remaining_value += estimated_value or 0.0

        if sale:
            sale_payload = {
                **sale,
                "sale_price_gross": _money(sale.get("sale_price_gross")),
                "platform_fees": _money(sale.get("platform_fees")),
                "shipping_out": _money(sale.get("shipping_out")),
                "other_costs": _money(sale.get("other_costs")),
                "net_proceeds": _money(sale.get("net_proceeds")),
                "realized_profit": _money(sale.get("realized_profit")),
                "item_title": item.get("title_snapshot"),
                "item_status": item.get("status"),
            }
            sales.append(sale_payload)
        else:
            sale_payload = None

        payload_items.append(
            {
                **item,
                "estimated_value": estimated_value,
                "cost_basis_override": _nullable_money(item.get("cost_basis_override")),
                "allocated_cost_basis": allocated_cost_basis,
                "sale": sale_payload,
            }
        )

    break_even_gap = max(round(total_cost_basis - net_sales, 2), 0.0)
    roi_realized_pct = round((realized_profit / total_cost_basis) * 100, 1) if total_cost_basis else 0.0
    recovery_rate_pct = round((net_sales / total_cost_basis) * 100, 1) if total_cost_basis else 0.0

    return {
        **lot,
        "purchase_price_gross": _money(lot.get("purchase_price_gross")),
        "shipping_in": _money(lot.get("shipping_in")),
        "fees_in": _money(lot.get("fees_in")),
        "other_costs": _money(lot.get("other_costs")),
        "total_cost_basis": total_cost_basis,
        "items": payload_items,
        "sales": sorted(sales, key=lambda sale: str(sale.get("sold_at") or "")),
        "summary": {
            "item_count": len(payload_items),
            "sold_count": sold_count,
            "inventory_count": inventory_count,
            "kept_count": kept_count,
            "discarded_count": discarded_count,
            "estimated_total_value": round(estimated_total_value, 2),
            "allocated_total_cost": round(allocated_total, 2),
            "net_sales": round(net_sales, 2),
            "realized_profit": round(realized_profit, 2),
            "remaining_cost_basis": round(remaining_cost_basis, 2),
            "written_off_cost_basis": round(written_off_cost_basis, 2),
            "expected_remaining_value": round(expected_remaining_value, 2),
            "break_even_gap": round(break_even_gap, 2),
            "roi_realized_pct": roi_realized_pct,
            "recovery_rate_pct": recovery_rate_pct,
        },
    }


def _hydrate_item_from_game(db, game_id: int) -> dict:
    row = db.execute(
        """
        SELECT g.id, g.title, g.item_type, p.name AS platform_name
        FROM games g
        LEFT JOIN platforms p ON g.platform_id = p.id
        WHERE g.id = ?
        """,
        (game_id,),
    ).fetchone()
    game = dict_from_row(row)
    if not game:
        raise not_found("Linked collection item not found")
    return game


@router.get("/api/lots")
async def list_lots():
    with get_db() as db:
        cursor = db.execute("SELECT * FROM lots ORDER BY updated_at DESC, id DESC")
        lots = [dict_from_row(row) for row in cursor.fetchall()]
        return [_build_lot_payload(db, lot) for lot in lots]


@router.post("/api/lots")
async def create_lot(payload: LotCreate):
    with get_db() as db:
        name = payload.name.strip()
        if not name:
            raise bad_request("Lot name is required")
        cursor = db.execute(
            """
            INSERT INTO lots (
                name, purchase_date, seller, purchase_price_gross,
                shipping_in, fees_in, other_costs, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                payload.purchase_date,
                payload.seller,
                _money(payload.purchase_price_gross),
                _money(payload.shipping_in),
                _money(payload.fees_in),
                _money(payload.other_costs),
                payload.notes,
            ),
        )
        lot = _get_lot_or_404(db, cursor.lastrowid)
        response = _build_lot_payload(db, lot)
        db.commit()
        return response


@router.get("/api/lots/{lot_id}")
async def get_lot(lot_id: int):
    with get_db() as db:
        lot = _get_lot_or_404(db, lot_id)
        return _build_lot_payload(db, lot)


@router.put("/api/lots/{lot_id}")
async def update_lot(lot_id: int, payload: LotUpdate):
    with get_db() as db:
        existing = _get_lot_or_404(db, lot_id)
        merged_name = payload.name.strip() if payload.name is not None else existing["name"]
        if not merged_name:
            raise bad_request("Lot name is required")
        merged = {
            "name": merged_name,
            "purchase_date": payload.purchase_date if payload.purchase_date is not None else existing.get("purchase_date"),
            "seller": payload.seller if payload.seller is not None else existing.get("seller"),
            "purchase_price_gross": _money(payload.purchase_price_gross) if payload.purchase_price_gross is not None else _money(existing.get("purchase_price_gross")),
            "shipping_in": _money(payload.shipping_in) if payload.shipping_in is not None else _money(existing.get("shipping_in")),
            "fees_in": _money(payload.fees_in) if payload.fees_in is not None else _money(existing.get("fees_in")),
            "other_costs": _money(payload.other_costs) if payload.other_costs is not None else _money(existing.get("other_costs")),
            "notes": payload.notes if payload.notes is not None else existing.get("notes"),
        }
        db.execute(
            """
            UPDATE lots
            SET name = ?, purchase_date = ?, seller = ?, purchase_price_gross = ?,
                shipping_in = ?, fees_in = ?, other_costs = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                merged["name"],
                merged["purchase_date"],
                merged["seller"],
                merged["purchase_price_gross"],
                merged["shipping_in"],
                merged["fees_in"],
                merged["other_costs"],
                merged["notes"],
                lot_id,
            ),
        )
        _recalculate_lot_allocations(db, lot_id)
        response = _build_lot_payload(db, _get_lot_or_404(db, lot_id))
        db.commit()
        return response


@router.delete("/api/lots/{lot_id}")
async def delete_lot(lot_id: int):
    with get_db() as db:
        _get_lot_or_404(db, lot_id)
        db.execute("DELETE FROM lots WHERE id = ?", (lot_id,))
        db.commit()
        return {"message": "Lot deleted successfully"}


@router.post("/api/lots/{lot_id}/items")
async def create_lot_item(lot_id: int, payload: LotItemCreate):
    with get_db() as db:
        _get_lot_or_404(db, lot_id)
        linked_game = _hydrate_item_from_game(db, payload.game_id) if payload.game_id else None
        title_snapshot = payload.title_snapshot or (linked_game or {}).get("title")
        if not title_snapshot:
            raise bad_request("Lot items require either a linked collection item or a title")
        platform_snapshot = payload.platform_snapshot or (linked_game or {}).get("platform_name")
        item_type_snapshot = payload.item_type_snapshot or (linked_game or {}).get("item_type") or "game"
        status = _ensure_status(payload.status)
        cursor = db.execute(
            """
            INSERT INTO lot_items (
                lot_id, game_id, title_snapshot, platform_snapshot, item_type_snapshot,
                estimated_value, cost_basis_override, allocated_cost_basis, allocation_method, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'estimated', ?, ?)
            """,
            (
                lot_id,
                payload.game_id,
                title_snapshot,
                platform_snapshot,
                item_type_snapshot,
                _nullable_money(payload.estimated_value),
                _nullable_money(payload.cost_basis_override),
                status,
                payload.notes,
            ),
        )
        _recalculate_lot_allocations(db, lot_id)
        item = _get_lot_item_or_404(db, cursor.lastrowid)
        response = {"item_id": item["id"], "lot": _build_lot_payload(db, _get_lot_or_404(db, lot_id))}
        db.commit()
        return response


@router.put("/api/lots/{lot_id}/items/{item_id}")
async def update_lot_item(lot_id: int, item_id: int, payload: LotItemUpdate):
    with get_db() as db:
        _get_lot_or_404(db, lot_id)
        item = _get_lot_item_or_404(db, item_id)
        if item["lot_id"] != lot_id:
            raise not_found("Lot item not found")

        linked_game = _hydrate_item_from_game(db, payload.game_id) if payload.game_id is not None and payload.game_id else None
        game_id = payload.game_id if payload.game_id is not None else item.get("game_id")
        if payload.unlink_game or payload.game_id == 0:
            game_id = None
            linked_game = None

        title_snapshot = payload.title_snapshot if payload.title_snapshot is not None else item.get("title_snapshot")
        platform_snapshot = payload.platform_snapshot if payload.platform_snapshot is not None else item.get("platform_snapshot")
        item_type_snapshot = payload.item_type_snapshot if payload.item_type_snapshot is not None else item.get("item_type_snapshot")

        if linked_game and payload.title_snapshot is None:
            title_snapshot = linked_game.get("title")
        if linked_game and payload.platform_snapshot is None:
            platform_snapshot = linked_game.get("platform_name")
        if linked_game and payload.item_type_snapshot is None:
            item_type_snapshot = linked_game.get("item_type")

        if not title_snapshot:
            raise bad_request("Lot items require a title")

        status = _ensure_status(payload.status if payload.status is not None else item.get("status"))

        existing_override = _nullable_money(item.get("cost_basis_override"))
        if payload.clear_cost_basis_override:
            override_value = None
        elif payload.cost_basis_override is not None:
            override_value = _nullable_money(payload.cost_basis_override)
        else:
            override_value = existing_override

        db.execute(
            """
            UPDATE lot_items
            SET game_id = ?, title_snapshot = ?, platform_snapshot = ?, item_type_snapshot = ?,
                estimated_value = ?, cost_basis_override = ?, status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                game_id,
                title_snapshot,
                platform_snapshot,
                item_type_snapshot,
                _nullable_money(payload.estimated_value) if payload.estimated_value is not None else _nullable_money(item.get("estimated_value")),
                override_value,
                status,
                payload.notes if payload.notes is not None else item.get("notes"),
                item_id,
            ),
        )
        _recalculate_lot_allocations(db, lot_id)

        sale = _load_sale_for_item(db, item_id)
        if sale:
            allocated = _money(
                db.execute("SELECT allocated_cost_basis FROM lot_items WHERE id = ?", (item_id,)).fetchone()[0]
            )
            net_proceeds = _money(sale.get("net_proceeds"))
            db.execute(
                "UPDATE lot_sales SET realized_profit = ?, updated_at = CURRENT_TIMESTAMP WHERE lot_item_id = ?",
                (round(net_proceeds - allocated, 2), item_id),
            )

        response = _build_lot_payload(db, _get_lot_or_404(db, lot_id))
        db.commit()
        return response


@router.delete("/api/lots/{lot_id}/items/{item_id}")
async def delete_lot_item(lot_id: int, item_id: int):
    with get_db() as db:
        _get_lot_or_404(db, lot_id)
        item = _get_lot_item_or_404(db, item_id)
        if item["lot_id"] != lot_id:
            raise not_found("Lot item not found")
        db.execute("DELETE FROM lot_items WHERE id = ?", (item_id,))
        _recalculate_lot_allocations(db, lot_id)
        response = _build_lot_payload(db, _get_lot_or_404(db, lot_id))
        db.commit()
        return response


@router.post("/api/lots/items/{item_id}/sale")
async def upsert_lot_item_sale(item_id: int, payload: LotSaleUpsert):
    with get_db() as db:
        item = _get_lot_item_or_404(db, item_id)
        lot_id = item["lot_id"]
        allocated = _money(item.get("allocated_cost_basis"))
        gross = _money(payload.sale_price_gross)
        fees = _money(payload.platform_fees)
        shipping = _money(payload.shipping_out)
        other = _money(payload.other_costs)
        net_proceeds = round(gross - fees - shipping - other, 2)
        realized_profit = round(net_proceeds - allocated, 2)

        existing_sale = _load_sale_for_item(db, item_id)
        if existing_sale:
            db.execute(
                """
                UPDATE lot_sales
                SET sold_at = ?, channel = ?, sale_price_gross = ?, platform_fees = ?,
                    shipping_out = ?, other_costs = ?, net_proceeds = ?, realized_profit = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE lot_item_id = ?
                """,
                (
                    payload.sold_at,
                    payload.channel,
                    gross,
                    fees,
                    shipping,
                    other,
                    net_proceeds,
                    realized_profit,
                    payload.notes,
                    item_id,
                ),
            )
        else:
            db.execute(
                """
                INSERT INTO lot_sales (
                    lot_item_id, sold_at, channel, sale_price_gross, platform_fees,
                    shipping_out, other_costs, net_proceeds, realized_profit, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    payload.sold_at,
                    payload.channel,
                    gross,
                    fees,
                    shipping,
                    other,
                    net_proceeds,
                    realized_profit,
                    payload.notes,
                ),
            )
        current_status = str(item.get("status") or "inventory")
        if current_status == "inventory":
            db.execute(
                "UPDATE lot_items SET status = 'sold', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (item_id,),
            )
        response = _build_lot_payload(db, _get_lot_or_404(db, lot_id))
        db.commit()
        return response


@router.delete("/api/lots/items/{item_id}/sale")
async def delete_lot_item_sale(item_id: int):
    with get_db() as db:
        item = _get_lot_item_or_404(db, item_id)
        lot_id = item["lot_id"]
        existing_sale = _load_sale_for_item(db, item_id)
        if not existing_sale:
            raise not_found("Sale record not found")
        db.execute("DELETE FROM lot_sales WHERE lot_item_id = ?", (item_id,))
        if str(item.get("status") or "") == "sold":
            db.execute(
                "UPDATE lot_items SET status = 'inventory', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (item_id,),
            )
        response = _build_lot_payload(db, _get_lot_or_404(db, lot_id))
        db.commit()
        return response
