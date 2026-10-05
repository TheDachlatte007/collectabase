"""normalize price catalog platforms

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
"""

from alembic import op
import sqlalchemy as sa

from backend.services.price.platforms import canonicalize_platform


revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "price_catalog" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("price_catalog")}
    if "platform_key" not in columns:
        op.add_column("price_catalog", sa.Column("platform_key", sa.String(), nullable=True))

    rows = connection.execute(sa.text("SELECT id, platform FROM price_catalog")).mappings()
    for row in rows:
        identity = canonicalize_platform(row["platform"])
        connection.execute(
            sa.text("UPDATE price_catalog SET platform = :label, platform_key = :key WHERE id = :id"),
            {"id": row["id"], "label": identity.label, "key": identity.key},
        )
    indexes = {index["name"] for index in inspector.get_indexes("price_catalog")}
    if "idx_price_catalog_platform_key" not in indexes:
        op.create_index("idx_price_catalog_platform_key", "price_catalog", ["platform_key"])


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "price_catalog" not in inspector.get_table_names():
        return
    indexes = {index["name"] for index in inspector.get_indexes("price_catalog")}
    if "idx_price_catalog_platform_key" in indexes:
        op.drop_index("idx_price_catalog_platform_key", table_name="price_catalog")
    columns = {column["name"] for column in inspector.get_columns("price_catalog")}
    if "platform_key" in columns:
        op.drop_column("price_catalog", "platform_key")
