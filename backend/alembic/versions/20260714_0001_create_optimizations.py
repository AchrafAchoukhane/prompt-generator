"""create optimizations table

Revision ID: 20260714_0001
Revises:
Create Date: 2026-07-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "optimizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("original_prompt", sa.Text(), nullable=False),
        sa.Column("optimized_prompt", sa.Text(), nullable=False),
        sa.Column("task_type", sa.String(length=40), nullable=False),
        sa.Column("original_score", sa.Integer(), nullable=False),
        sa.Column("optimized_score", sa.Integer(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("improvements", sa.JSON(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("score_breakdown", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_optimizations_created_at"), "optimizations", ["created_at"], unique=False)
    op.create_index(op.f("ix_optimizations_task_type"), "optimizations", ["task_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_optimizations_task_type"), table_name="optimizations")
    op.drop_index(op.f("ix_optimizations_created_at"), table_name="optimizations")
    op.drop_table("optimizations")

