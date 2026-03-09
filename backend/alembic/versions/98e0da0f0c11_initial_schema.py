"""Initial schema

Revision ID: 98e0da0f0c11
Revises: 
Create Date: 2026-03-09 14:58:39.328889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98e0da0f0c11'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    """Check if a table already exists (handles pre-Alembic databases)."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


def _column_exists(table: str, column: str) -> bool:
    """Check if a column already exists in a table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def _index_exists(name: str) -> bool:
    """Check if an index already exists."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=:name"
    ), {"name": name})
    return result.scalar() > 0


def upgrade() -> None:
    """Upgrade schema — safe to run on both fresh and pre-existing databases."""

    # --- Tables that may already exist from the old init_db() ---

    if not _table_exists('platforms'):
        op.create_table('platforms',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False, unique=True),
            sa.Column('manufacturer', sa.String(), nullable=True),
            sa.Column('type', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    if not _table_exists('games'):
        op.create_table('games',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('platform_id', sa.Integer(), sa.ForeignKey('platforms.id'), nullable=True),
            sa.Column('barcode', sa.String(), nullable=True),
            sa.Column('igdb_id', sa.Integer(), nullable=True),
            sa.Column('release_date', sa.String(), nullable=True),
            sa.Column('publisher', sa.String(), nullable=True),
            sa.Column('developer', sa.String(), nullable=True),
            sa.Column('genre', sa.String(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('cover_url', sa.String(), nullable=True),
            sa.Column('region', sa.String(), nullable=True),
            sa.Column('condition', sa.String(), nullable=True),
            sa.Column('completeness', sa.String(), nullable=True),
            sa.Column('location', sa.String(), nullable=True),
            sa.Column('purchase_date', sa.String(), nullable=True),
            sa.Column('purchase_price', sa.Float(), nullable=True),
            sa.Column('current_value', sa.Float(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_wishlist', sa.Integer(), server_default='0', nullable=True),
            sa.Column('wishlist_max_price', sa.Float(), nullable=True),
            sa.Column('item_type', sa.String(), server_default='game', nullable=True),
            sa.Column('created_at', sa.String(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.String(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    if not _table_exists('app_meta'):
        op.create_table('app_meta',
            sa.Column('key', sa.String(), nullable=False),
            sa.Column('value', sa.String(), nullable=True),
            sa.Column('updated_at', sa.String(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.PrimaryKeyConstraint('key')
        )

    if not _table_exists('price_catalog'):
        op.create_table('price_catalog',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('pricecharting_id', sa.String(), nullable=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('platform', sa.String(), nullable=False),
            sa.Column('loose_usd', sa.Float(), nullable=True),
            sa.Column('cib_usd', sa.Float(), nullable=True),
            sa.Column('new_usd', sa.Float(), nullable=True),
            sa.Column('loose_eur', sa.Float(), nullable=True),
            sa.Column('cib_eur', sa.Float(), nullable=True),
            sa.Column('new_eur', sa.Float(), nullable=True),
            sa.Column('page_url', sa.String(), nullable=True),
            sa.Column('scraped_at', sa.String(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('changed_at', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    if not _table_exists('price_history'):
        op.create_table('price_history',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('game_id', sa.Integer(), nullable=False),
            sa.Column('source', sa.String(), server_default='pricecharting', nullable=True),
            sa.Column('loose_price', sa.Float(), nullable=True),
            sa.Column('complete_price', sa.Float(), nullable=True),
            sa.Column('new_price', sa.Float(), nullable=True),
            sa.Column('eur_rate', sa.Float(), nullable=True),
            sa.Column('pricecharting_id', sa.String(), nullable=True),
            sa.Column('fetched_at', sa.String(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # --- Indexes (safe to skip if they already exist) ---
    for idx_name, table, columns in [
        ('idx_price_catalog_platform', 'price_catalog', ['platform']),
        ('idx_price_catalog_platform_pcid', 'price_catalog', ['platform', 'pricecharting_id']),
        ('idx_price_catalog_platform_title', 'price_catalog', ['platform', 'title']),
        ('idx_price_catalog_title', 'price_catalog', ['title']),
    ]:
        if _table_exists(table) and not _index_exists(idx_name):
            op.create_index(idx_name, table, columns, unique=False)

    # --- Columns that might be missing on older databases ---
    if _table_exists('games') and not _column_exists('games', 'item_type'):
        op.add_column('games', sa.Column('item_type', sa.String(), server_default='game', nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists('games') and _column_exists('games', 'item_type'):
        op.drop_column('games', 'item_type')
    if _table_exists('price_history'):
        op.drop_table('price_history')
    for idx in ['idx_price_catalog_title', 'idx_price_catalog_platform_title',
                'idx_price_catalog_platform_pcid', 'idx_price_catalog_platform']:
        if _index_exists(idx):
            op.drop_index(idx, table_name='price_catalog')
    if _table_exists('price_catalog'):
        op.drop_table('price_catalog')
    if _table_exists('app_meta'):
        op.drop_table('app_meta')
