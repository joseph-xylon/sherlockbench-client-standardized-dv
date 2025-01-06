"""id should be uuid

Revision ID: e0b50b00d716
Revises: 441cbfadb3eb
Create Date: 2025-01-06 10:20:21.720326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, INTEGER, VARCHAR, UUID

# revision identifiers, used by Alembic.
revision: str = 'e0b50b00d716'
down_revision: Union[str, None] = '441cbfadb3eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the `attempts` table first (it depends on `runs`)
    op.drop_table("attempts")
    # Drop the `runs` table
    op.drop_table("runs")

    # Recreate the `runs` table with UUID primary key
    op.create_table(
        "runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("model_identifier", sa.String, nullable=False),
        sa.Column("benchmark_version", sa.String, nullable=False),  # SemVer stored as string
        sa.Column("config", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("datetime_start", sa.dialects.postgresql.TIMESTAMP, nullable=False),
        sa.Column("total_run_time", sa.Float, nullable=True),  # Storing seconds as float
        sa.Column("final_score", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("score_percent", sa.Float, nullable=True),
        sa.Column("total_api_calls", sa.Integer(), nullable=True),
    )

    # Recreate the `attempts` table with UUID primary key and updated foreign key
    op.create_table(
        "attempts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("function", sa.String, nullable=False),
        sa.Column("result", sa.String, nullable=False),
        sa.Column("attempt_index", sa.Integer, nullable=False),
        sa.Column("time_taken", sa.Float, nullable=False),  # Storing seconds as float
        sa.Column("api_calls", sa.Integer(), nullable=True),
        sa.Column("tool_calls", sa.Integer, nullable=True),
        sa.Column("complete_log", sa.Text, nullable=False),
    )

def downgrade() -> None:
    # Drop the `attempts` table first (it depends on `runs`)
    op.drop_table("attempts")
    # Drop the `runs` table
    op.drop_table("runs")

    # Recreate the `runs` table with Integer primary key
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model_identifier", sa.String, nullable=False),
        sa.Column("benchmark_version", sa.String, nullable=False),  # SemVer stored as string
        sa.Column("config", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("datetime_start", sa.dialects.postgresql.TIMESTAMP, nullable=False),
        sa.Column("total_run_time", sa.Float, nullable=True),  # Storing seconds as float
        sa.Column("final_score", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("score_percent", sa.Float, nullable=True),
        sa.Column("total_api_calls", sa.Integer(), nullable=True),
    )

    # Recreate the `attempts` table with Integer primary key and original foreign key
    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("function", sa.String, nullable=False),
        sa.Column("result", sa.String, nullable=False),
        sa.Column("attempt_index", sa.Integer, nullable=False),
        sa.Column("time_taken", sa.Float, nullable=False),  # Storing seconds as float
        sa.Column("api_calls", sa.Integer(), nullable=True),
        sa.Column("tool_calls", sa.Integer, nullable=True),
        sa.Column("complete_log", sa.Text, nullable=False),
    )
