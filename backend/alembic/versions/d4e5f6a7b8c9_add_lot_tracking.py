"""add lot tracking tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


def _index_exists(table: str, index_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return index_name in {idx["name"] for idx in inspector.get_indexes(table)}


def upgrade() -> None:
    if not _table_exists("lots"):
        op.create_table(
            "lots",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("purchase_date", sa.String(), nullable=True),
            sa.Column("seller", sa.String(), nullable=True),
            sa.Column("purchase_price_gross", sa.Float(), nullable=False, server_default="0"),
            sa.Column("shipping_in", sa.Float(), nullable=False, server_default="0"),
            sa.Column("fees_in", sa.Float(), nullable=False, server_default="0"),
            sa.Column("other_costs", sa.Float(), nullable=False, server_default="0"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    if not _table_exists("lot_items"):
        op.create_table(
            "lot_items",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title_snapshot", sa.String(), nullable=False),
            sa.Column("platform_snapshot", sa.String(), nullable=True),
            sa.Column("item_type_snapshot", sa.String(), nullable=True, server_default="game"),
            sa.Column("estimated_value", sa.Float(), nullable=True),
            sa.Column("cost_basis_override", sa.Float(), nullable=True),
            sa.Column("allocated_cost_basis", sa.Float(), nullable=False, server_default="0"),
            sa.Column("allocation_method", sa.String(), nullable=False, server_default="estimated"),
            sa.Column("status", sa.String(), nullable=False, server_default="inventory"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    if not _table_exists("lot_sales"):
        op.create_table(
            "lot_sales",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lot_item_id", sa.Integer(), sa.ForeignKey("lot_items.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sold_at", sa.String(), nullable=True),
            sa.Column("channel", sa.String(), nullable=True),
            sa.Column("sale_price_gross", sa.Float(), nullable=False, server_default="0"),
            sa.Column("platform_fees", sa.Float(), nullable=False, server_default="0"),
            sa.Column("shipping_out", sa.Float(), nullable=False, server_default="0"),
            sa.Column("other_costs", sa.Float(), nullable=False, server_default="0"),
            sa.Column("net_proceeds", sa.Float(), nullable=False, server_default="0"),
            sa.Column("realized_profit", sa.Float(), nullable=False, server_default="0"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("lot_item_id", name="uq_lot_sales_lot_item_id"),
        )

    if not _index_exists("lot_items", "idx_lot_items_lot_id"):
        op.create_index("idx_lot_items_lot_id", "lot_items", ["lot_id"])
    if not _index_exists("lot_items", "idx_lot_items_game_id"):
        op.create_index("idx_lot_items_game_id", "lot_items", ["game_id"])
    if not _index_exists("lot_sales", "idx_lot_sales_lot_item_id"):
        op.create_index("idx_lot_sales_lot_item_id", "lot_sales", ["lot_item_id"])


def downgrade() -> None:
    if _table_exists("lot_sales"):
        if _index_exists("lot_sales", "idx_lot_sales_lot_item_id"):
            op.drop_index("idx_lot_sales_lot_item_id", table_name="lot_sales")
        op.drop_table("lot_sales")

    if _table_exists("lot_items"):
        if _index_exists("lot_items", "idx_lot_items_game_id"):
            op.drop_index("idx_lot_items_game_id", table_name="lot_items")
        if _index_exists("lot_items", "idx_lot_items_lot_id"):
            op.drop_index("idx_lot_items_lot_id", table_name="lot_items")
        op.drop_table("lot_items")

    if _table_exists("lots"):
        op.drop_table("lots")
