"""Add evidence-grounded diagnoses for Phase 3.

Revision ID: 0003_diagnose_hypothesize_strategy
Revises: 0002_observe_detect
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0003_diagnose_hypothesize_strategy"
down_revision: str | None = "0002_observe_detect"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "diagnoses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column(
            "supporting_fact_ids",
            postgresql.ARRAY(sa.Uuid()),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Numeric(precision=5, scale=4),
            nullable=False,
        ),
        sa.Column("uncertainty", sa.Text(), nullable=False),
        sa.Column(
            "model_version",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name="fk_diagnoses_merchant_id_merchants",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name="fk_diagnoses_opportunity_id_opportunities",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id"],
            ["agent_runs.id"],
            name="fk_diagnoses_agent_run_id_agent_runs",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_diagnoses"),
    )

    op.create_index(
        "ix_diagnoses_merchant_id",
        "diagnoses",
        ["merchant_id"],
    )

    op.create_index(
        "ix_diagnoses_opportunity_id",
        "diagnoses",
        ["opportunity_id"],
    )

    op.create_index(
        "ix_diagnoses_agent_run_id",
        "diagnoses",
        ["agent_run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_diagnoses_agent_run_id",
        table_name="diagnoses",
    )
    op.drop_index(
        "ix_diagnoses_opportunity_id",
        table_name="diagnoses",
    )
    op.drop_index(
        "ix_diagnoses_merchant_id",
        table_name="diagnoses",
    )
    op.drop_table("diagnoses")