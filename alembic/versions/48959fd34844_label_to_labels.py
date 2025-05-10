"""label to labels

Revision ID: 48959fd34844
Revises: 38569312034d
Create Date: 2025-05-10 19:14:38.846468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48959fd34844'
down_revision: Union[str, None] = '38569312034d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new 'labels' column as a text array
    op.add_column('runs', sa.Column('labels', sa.ARRAY(sa.Text()), nullable=True))

    # Migrate data from 'label' column to 'labels' array
    # If label is not null, set it as the first element in the labels array
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE runs SET labels = ARRAY[label] WHERE label IS NOT NULL"))

    # Drop the old 'label' column
    op.drop_column('runs', 'label')


def downgrade() -> None:
    # Add back the 'label' column
    op.add_column('runs', sa.Column('label', sa.Text(), nullable=True))

    # Migrate data back: take the first element of the array if it exists
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE runs SET label = labels[1] WHERE array_length(labels, 1) > 0"))

    # Drop the 'labels' column
    op.drop_column('runs', 'labels')
