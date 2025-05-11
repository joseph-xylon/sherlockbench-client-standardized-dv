"""make attempts nullable

Revision ID: 087a241fea8b
Revises: 48959fd34844
Create Date: 2025-05-11 12:24:22.074024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '087a241fea8b'
down_revision: Union[str, None] = '48959fd34844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('attempts', 'complete_log',
               existing_type=sa.TEXT(),
               nullable=True)
    op.alter_column('attempts', 'time_taken',
               existing_type=sa.DOUBLE_PRECISION(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('attempts', 'time_taken',
               existing_type=sa.DOUBLE_PRECISION(),
               nullable=False)
    op.alter_column('attempts', 'complete_log',
               existing_type=sa.TEXT(),
               nullable=False)
