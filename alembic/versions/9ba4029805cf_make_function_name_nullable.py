"""make function name nullable

Revision ID: 9ba4029805cf
Revises: e0b50b00d716
Create Date: 2025-01-09 19:59:30.164877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ba4029805cf'
down_revision: Union[str, None] = 'e0b50b00d716'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('attempts', 'function', new_column_name='function_name', nullable=True)
    op.alter_column('attempts', 'attempt_index', nullable=True)

def downgrade() -> None:
    op.alter_column('attempts', 'function_name', new_column_name='function', nullable=False)
    op.alter_column('attempts', 'attempt_index', nullable=False)
