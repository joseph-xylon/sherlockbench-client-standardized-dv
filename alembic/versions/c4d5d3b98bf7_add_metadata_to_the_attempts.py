"""add metadata to the attempts

Revision ID: c4d5d3b98bf7
Revises: 68cd64082b3c
Create Date: 2025-05-23 19:03:59.028893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c4d5d3b98bf7'
down_revision: Union[str, None] = '68cd64082b3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('attempts', sa.Column('meta', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('attempts', 'meta')
