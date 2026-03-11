"""phase_2_enhancements

Revision ID: 69ef002b9879
Revises: 98e0da0f0c11
Create Date: 2026-03-11 09:48:39.489475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69ef002b9879'
down_revision: Union[str, Sequence[str], None] = '98e0da0f0c11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('games', sa.Column('quantity', sa.Integer(), server_default='1', nullable=False))

    op.create_table(
        'value_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('recorded_at', sa.Date(), nullable=False),
        sa.Column('total_value', sa.Float(), nullable=False),
        sa.Column('game_value', sa.Float(), nullable=False),
        sa.Column('hardware_value', sa.Float(), nullable=False),
    )

    op.create_table(
        'item_images',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('games.id', ondelete='CASCADE'), nullable=False),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('item_images')
    op.drop_table('value_history')
    op.drop_column('games', 'quantity')
