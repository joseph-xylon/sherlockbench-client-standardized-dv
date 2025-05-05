"""add keeper column

Revision ID: 5f1a34143bbd
Revises: add_failure_info_to_runs
Create Date: 2025-05-05 12:53:07.883310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import BOOLEAN

# revision identifiers, used by Alembic.
revision: str = '5f1a34143bbd'
down_revision: Union[str, None] = 'add_failure_info_to_runs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('runs', sa.Column('keeper', BOOLEAN, nullable=True))


def downgrade() -> None:
    op.drop_column('runs', 'keeper')
