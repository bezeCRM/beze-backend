"""add cascade delete for user data

Revision ID: e6341eb15a4d
Revises: b463e630c707
Create Date: 2026-05-19 21:25:30.725785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e6341eb15a4d'
down_revision: Union[str, Sequence[str], None] = 'b463e630c707'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("categories_owner_id_fkey", "categories", type_="foreignkey")
    op.create_foreign_key(
        "categories_owner_id_fkey",
        "categories",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("orders_owner_id_fkey", "orders", type_="foreignkey")
    op.create_foreign_key(
        "orders_owner_id_fkey",
        "orders",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("order_lines_order_id_fkey", "order_lines", type_="foreignkey")
    op.create_foreign_key(
        "order_lines_order_id_fkey",
        "order_lines",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("planner_tasks_owner_id_fkey", "planner_tasks", type_="foreignkey")
    op.create_foreign_key(
        "planner_tasks_owner_id_fkey",
        "planner_tasks",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("products_owner_id_fkey", "products", type_="foreignkey")
    op.create_foreign_key(
        "products_owner_id_fkey",
        "products",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("product_photos_product_id_fkey", "product_photos", type_="foreignkey")
    op.create_foreign_key(
        "product_photos_product_id_fkey",
        "product_photos",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("profile_settings_owner_id_fkey", "profile_settings", type_="foreignkey")
    op.create_foreign_key(
        "profile_settings_owner_id_fkey",
        "profile_settings",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("profile_settings_owner_id_fkey", "profile_settings", type_="foreignkey")
    op.create_foreign_key(
        "profile_settings_owner_id_fkey",
        "profile_settings",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.drop_constraint("product_photos_product_id_fkey", "product_photos", type_="foreignkey")
    op.create_foreign_key(
        "product_photos_product_id_fkey",
        "product_photos",
        "products",
        ["product_id"],
        ["id"],
    )

    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
    )

    op.drop_constraint("products_owner_id_fkey", "products", type_="foreignkey")
    op.create_foreign_key(
        "products_owner_id_fkey",
        "products",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.drop_constraint("planner_tasks_owner_id_fkey", "planner_tasks", type_="foreignkey")
    op.create_foreign_key(
        "planner_tasks_owner_id_fkey",
        "planner_tasks",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.drop_constraint("order_lines_order_id_fkey", "order_lines", type_="foreignkey")
    op.create_foreign_key(
        "order_lines_order_id_fkey",
        "order_lines",
        "orders",
        ["order_id"],
        ["id"],
    )

    op.drop_constraint("orders_owner_id_fkey", "orders", type_="foreignkey")
    op.create_foreign_key(
        "orders_owner_id_fkey",
        "orders",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.drop_constraint("categories_owner_id_fkey", "categories", type_="foreignkey")
    op.create_foreign_key(
        "categories_owner_id_fkey",
        "categories",
        "users",
        ["owner_id"],
        ["id"],
    )