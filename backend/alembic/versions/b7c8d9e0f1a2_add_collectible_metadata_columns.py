"""add collectible metadata columns

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
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

    for column_name in ["comicvine_id", "hobbydb_id", "mfc_id"]:
        if not _column_exists("games", column_name):
            op.add_column("games", sa.Column(column_name, sa.String(), nullable=True))


def downgrade() -> None:
    if not _table_exists("games"):
        return

    for column_name in ["mfc_id", "hobbydb_id", "comicvine_id"]:
        if _column_exists("games", column_name):
            op.drop_column("games", column_name)
