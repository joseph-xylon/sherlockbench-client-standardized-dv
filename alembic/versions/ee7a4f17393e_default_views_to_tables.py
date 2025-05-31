"""default views to tables

Revision ID: ee7a4f17393e
Revises: c4d5d3b98bf7
Create Date: 2025-05-31 05:14:28.862411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee7a4f17393e'
down_revision: Union[str, None] = 'c4d5d3b98bf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create default view for runs table
    op.execute("""
        CREATE VIEW runs_view AS
        SELECT id, model_identifier, datetime_start, final_score, labels
        FROM runs
        ORDER BY datetime_start
    """)
    
    # Create default view for attempts table
    op.execute("""
        CREATE VIEW attempts_view AS
        SELECT run_id, function_name, result
        FROM attempts
    """)


def downgrade() -> None:
    # Drop the views in reverse order
    op.execute("DROP VIEW IF EXISTS attempts_view")
    op.execute("DROP VIEW IF EXISTS runs_view")
