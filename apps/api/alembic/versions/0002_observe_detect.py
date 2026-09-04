"""Add deterministic observe/detect storage."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_observe_detect"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("events", sa.Column("client_event_id", sa.Uuid(), nullable=True))
    op.execute("UPDATE events SET client_event_id = id WHERE client_event_id IS NULL")
    op.alter_column("events", "client_event_id", nullable=False)
    op.create_unique_constraint("uq_events_merchant_client_event", "events", ["merchant_id", "client_event_id"])
    op.create_unique_constraint(
        "uq_opportunities_detector_entity", "opportunities", ["merchant_id", "detector_id", "entity_id"]
    )

    op.create_table(
        "events_daily",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("channel", sa.String(length=64), nullable=False),
        sa.Column("variant", sa.String(length=32), nullable=False),
        sa.Column("sessions", sa.Integer(), nullable=False),
        sa.Column("pdp_views", sa.Integer(), nullable=False),
        sa.Column("atc", sa.Integer(), nullable=False),
        sa.Column("checkouts", sa.Integer(), nullable=False),
        sa.Column("orders", sa.Integer(), nullable=False),
        sa.Column("revenue_paise", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_events_daily"),
        sa.UniqueConstraint("merchant_id", "product_id", "day", "channel", "variant", name="uq_events_daily_scope"),
    )
    op.create_index("ix_events_daily_merchant_day", "events_daily", ["merchant_id", "day"])
    op.create_index("ix_events_daily_merchant_product", "events_daily", ["merchant_id", "product_id"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fact_snapshots_immutable()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'fact_snapshots is immutable';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_fact_snapshots_no_update
        BEFORE UPDATE ON fact_snapshots FOR EACH ROW EXECUTE FUNCTION fact_snapshots_immutable();
        CREATE TRIGGER trg_fact_snapshots_no_delete
        BEFORE DELETE ON fact_snapshots FOR EACH ROW EXECUTE FUNCTION fact_snapshots_immutable();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_fact_snapshots_no_delete ON fact_snapshots")
    op.execute("DROP TRIGGER IF EXISTS trg_fact_snapshots_no_update ON fact_snapshots")
    op.execute("DROP FUNCTION IF EXISTS fact_snapshots_immutable()")
    op.drop_index("ix_events_daily_merchant_product", table_name="events_daily")
    op.drop_index("ix_events_daily_merchant_day", table_name="events_daily")
    op.drop_table("events_daily")
    op.drop_constraint("uq_events_merchant_client_event", "events", type_="unique")
    op.drop_constraint("uq_opportunities_detector_entity", "opportunities", type_="unique")
    op.drop_column("events", "client_event_id")