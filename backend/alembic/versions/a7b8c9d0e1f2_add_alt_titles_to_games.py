"""add alt_titles to games

Revision ID: a7b8c9d0e1f2
Revises: f7a8b9c0d1e2
Create Date: 2026-10-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    if not _table_exists("games"):
        return

    if not _column_exists("games", "alt_titles"):
        op.add_column("games", sa.Column("alt_titles", sa.Text(), nullable=True))


def downgrade() -> None:
    if not _table_exists("games"):
        return

    if _column_exists("games", "alt_titles"):
        op.drop_column("games", "alt_titles")
