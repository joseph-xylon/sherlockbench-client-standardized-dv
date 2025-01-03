"""create runs and attempts tables

Revision ID: 441cbfadb3eb
Revises: 
Create Date: 2024-11-23 17:19:19.613385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, INTEGER, VARCHAR

# revision identifiers, used by Alembic.
revision: str = '441cbfadb3eb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the `runs` table
    op.create_table(
        'runs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('model_identifier', sa.String, nullable=False),
        sa.Column('benchmark_version', sa.String, nullable=False),  # SemVer stored as string
        sa.Column('config', JSONB, nullable=False),
        sa.Column('datetime_start', TIMESTAMP, nullable=False),
        sa.Column('total_run_time', sa.Float, nullable=True),  # Storing seconds as float
        sa.Column('final_score', JSONB, nullable=True),
        sa.Column('score_percent', sa.Float, nullable=True),
        sa.Column('total_api_calls', sa.Integer(), nullable=True)
    )

    # Create the `attempts` table
    op.create_table(
        'attempts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.Integer, sa.ForeignKey('runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('function', sa.String, nullable=False),
        sa.Column('result', sa.String, nullable=False),
        sa.Column('attempt_index', sa.Integer, nullable=False),
        sa.Column('time_taken', sa.Float, nullable=False),  # Storing seconds as float
        sa.Column('api_calls', sa.Integer(), nullable=True),
        sa.Column('tool_calls', sa.Integer, nullable=True),
        sa.Column('complete_log', sa.Text, nullable=False)
    )

def downgrade() -> None:
    # Drop the `attempts` table first as it depends on `runs`
    op.drop_table('attempts')
    # Drop the `runs` table
    op.drop_table('runs')
