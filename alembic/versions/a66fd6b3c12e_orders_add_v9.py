"""orders add v9

Revision ID: a66fd6b3c12e
Revises: 9ad37be5e776
Create Date: 2026-02-21 17:23:45.789389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a66fd6b3c12e'
down_revision: Union[str, Sequence[str], None] = '9ad37be5e776'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "order_lines",
        "amount",
        existing_type=sa.INTEGER(),
        type_=sa.Numeric(precision=12, scale=3),
        existing_nullable=False,
        postgresql_using="amount::numeric",
    )


def downgrade() -> None:
    op.alter_column(
        "order_lines",
        "amount",
        existing_type=sa.Numeric(precision=12, scale=3),
        type_=sa.INTEGER(),
        existing_nullable=False,
        postgresql_using="round(amount)::int",
    )
    # ### end Alembic commands ###
