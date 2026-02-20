"""changed products/models v5

Revision ID: 6e39c34be438
Revises: 8e563171e35c
Create Date: 2026-02-21 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6e39c34be438"
down_revision: Union[str, Sequence[str], None] = "8e563171e35c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "fillings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "ingredients",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.alter_column("products", "fillings", server_default=None)
    op.alter_column("products", "ingredients", server_default=None)

    # drop dependent tables first
    op.drop_table("product_ingredients")
    op.drop_table("product_fillings")

    # then referenced tables
    op.drop_table("ingredients")
    op.drop_table("fillings")


def downgrade() -> None:
    op.create_table(
        "fillings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_fillings_owner_name"),
    )
    op.create_index("ix_fillings_owner_id", "fillings", ["owner_id"], unique=False)

    op.create_table(
        "ingredients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("weight_grams", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_ingredients_owner_name"),
    )
    op.create_index("ix_ingredients_owner_id", "ingredients", ["owner_id"], unique=False)

    op.create_table(
        "product_fillings",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("filling_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["filling_id"], ["fillings.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("product_id", "filling_id"),
    )
    op.create_index("ix_product_fillings_product_id", "product_fillings", ["product_id"], unique=False)
    op.create_index("ix_product_fillings_filling_id", "product_fillings", ["filling_id"], unique=False)

    op.create_table(
        "product_ingredients",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("ingredient_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("product_id", "ingredient_id"),
    )
    op.create_index("ix_product_ingredients_product_id", "product_ingredients", ["product_id"], unique=False)
    op.create_index("ix_product_ingredients_ingredient_id", "product_ingredients", ["ingredient_id"], unique=False)

    op.drop_column("products", "ingredients")
    op.drop_column("products", "fillings")