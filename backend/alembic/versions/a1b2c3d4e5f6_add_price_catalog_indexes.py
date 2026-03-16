"""add price_catalog indexes

Revision ID: a1b2c3d4e5f6
Revises: 7b5a4fab11fd
Create Date: 2026-03-16

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7b5a4fab11fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_price_catalog_platform', 'price_catalog', ['platform'])
    op.create_index('idx_price_catalog_title', 'price_catalog', ['title'])
    op.create_index('idx_price_catalog_platform_title', 'price_catalog', ['platform', 'title'])


def downgrade() -> None:
    op.drop_index('idx_price_catalog_platform_title', table_name='price_catalog')
    op.drop_index('idx_price_catalog_title', table_name='price_catalog')
    op.drop_index('idx_price_catalog_platform', table_name='price_catalog')
