"""remove attempt_index

Revision ID: 68cd64082b3c
Revises: 087a241fea8b
Create Date: 2025-05-11 15:37:24.125207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68cd64082b3c'
down_revision: Union[str, None] = '087a241fea8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('attempts', 'attempt_index')


def downgrade() -> None:
    op.add_column('attempts', sa.Column('attempt_index', sa.Integer(), nullable=True))
