"""users_email_not_null

Revision ID: 81a1052e8288
Revises: 0874b540258e
Create Date: 2026-03-26 00:07:37.370587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '81a1052e8288'
down_revision: Union[str, Sequence[str], None] = '0874b540258e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Заполняем NULL-значения заглушкой, чтобы не сломать NOT NULL constraint
    op.execute("""
        UPDATE users
        SET email = 'unknown_' || id::text || '@placeholder.invalid'
        WHERE email IS NULL
    """)

    # 2. Теперь безопасно ставим NOT NULL
    op.alter_column('users', 'email',
        existing_type=sa.String(320),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column('users', 'email',
        existing_type=sa.String(320),
        nullable=True,
    )
    # ### end Alembic commands ###
