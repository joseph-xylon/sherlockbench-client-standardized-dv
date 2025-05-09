"""remove_keeper_add_label

Revision ID: 38569312034d
Revises: 5f1a34143bbd
Create Date: 2025-05-09 19:20:12.515782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38569312034d'
down_revision: Union[str, None] = '5f1a34143bbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new 'label' column
    op.add_column('runs', sa.Column('label', sa.Text(), nullable=True))

    # Update the data: set label='keeper' where keeper=True
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE runs SET label = 'keeper' WHERE keeper = TRUE"))

    # Remove the 'keeper' column
    op.drop_column('runs', 'keeper')


def downgrade() -> None:
    # Add back the 'keeper' column
    op.add_column('runs', sa.Column('keeper', sa.Boolean(), nullable=True))

    # Restore the data: set keeper=True where label='keeper'
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE runs SET keeper = TRUE WHERE label = 'keeper'"))

    # Remove the 'label' column
    op.drop_column('runs', 'label')
