"""Foundation schema for Vrudhya.ai Phase 2.

Revision ID: 0001_foundation
Revises:
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "merchants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("data_mode", sa.String(length=32), nullable=False),
        sa.Column("autonomy_kill_switch", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_merchants"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("credential_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_users_merchant_id_merchants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("merchant_id", "email", name="uq_users_merchant_id_email"),
    )
    op.create_index("ix_users_merchant_id", "users", ["merchant_id"])

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price_paise", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("cost_paise", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_products_merchant_id_merchants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint("merchant_id", "sku", name="uq_products_merchant_id_sku"),
    )
    op.create_index("ix_products_merchant_id", "products", ["merchant_id"])

    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("visitor_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_customers_merchant_id_merchants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
    )
    op.create_index("ix_customers_merchant_id", "customers", ["merchant_id"])
    op.create_index("ix_customers_visitor_key", "customers", ["visitor_key"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_paise", sa.Integer(), nullable=False),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_orders_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name="fk_orders_customer_id_customers", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
    )
    op.create_index("ix_orders_merchant_id", "orders", ["merchant_id"])
    op.create_index("ix_orders_merchant_placed", "orders", ["merchant_id", "placed_at"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_paise", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_order_items_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_order_items_order_id_orders", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_order_items_product_id_products", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_order_items"),
    )
    op.create_index("ix_order_items_merchant_id", "order_items", ["merchant_id"])
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=True),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_payments_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_payments_order_id_orders", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
    )
    op.create_index("ix_payments_merchant_id", "payments", ["merchant_id"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("visitor_key", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=True),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_events_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_events_product_id_products", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name="fk_events_customer_id_customers", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_events_order_id_orders", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], name="fk_events_payment_id_payments", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
    )
    op.create_index("ix_events_merchant_id", "events", ["merchant_id"])
    op.create_index("ix_events_merchant_occurred", "events", ["merchant_id", "occurred_at"])
    op.create_index("ix_events_merchant_type_occurred", "events", ["merchant_id", "event_type", "occurred_at"])
    op.create_index("ix_events_merchant_product_occurred", "events", ["merchant_id", "product_id", "occurred_at"])
    op.create_index("ix_events_merchant_visitor", "events", ["merchant_id", "visitor_key"])

    op.create_table(
        "permission_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_permission_policies_merchant_id_merchants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_permission_policies"),
        sa.UniqueConstraint("merchant_id", name="uq_permission_policies_merchant_id"),
    )

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("detector_id", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("evidence_fact_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_opportunities_merchant_id_merchants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_opportunities"),
    )
    op.create_index("ix_opportunities_merchant_id", "opportunities", ["merchant_id"])

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=True),
        sa.Column("pinned_fact_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_agent_runs_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name="fk_agent_runs_opportunity_id_opportunities", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_agent_runs"),
    )
    op.create_index("ix_agent_runs_merchant_id", "agent_runs", ["merchant_id"])

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_agent_messages_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], name="fk_agent_messages_agent_run_id_agent_runs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_agent_messages"),
    )
    op.create_index("ix_agent_messages_merchant_id", "agent_messages", ["merchant_id"])
    op.create_index("ix_agent_messages_agent_run_id", "agent_messages", ["agent_run_id"])

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_tool_calls_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], name="fk_tool_calls_agent_run_id_agent_runs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_tool_calls"),
    )
    op.create_index("ix_tool_calls_merchant_id", "tool_calls", ["merchant_id"])
    op.create_index("ix_tool_calls_agent_run_id", "tool_calls", ["agent_run_id"])

    op.create_table(
        "hypotheses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("supporting_fact_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column("contradicting_fact_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_hypotheses_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], name="fk_hypotheses_agent_run_id_agent_runs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_hypotheses"),
    )
    op.create_index("ix_hypotheses_merchant_id", "hypotheses", ["merchant_id"])
    op.create_index("ix_hypotheses_agent_run_id", "hypotheses", ["agent_run_id"])

    op.create_table(
        "strategies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("impact_assumptions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expected_direction", sa.String(length=32), nullable=False),
        sa.Column("cost", sa.String(length=64), nullable=False),
        sa.Column("risk", sa.String(length=64), nullable=False),
        sa.Column("implementation_complexity", sa.String(length=64), nullable=False),
        sa.Column("primary_metric", sa.String(length=128), nullable=False),
        sa.Column("guardrail_metrics", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("proposed_change", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_strategies_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], name="fk_strategies_agent_run_id_agent_runs", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["hypotheses.id"], name="fk_strategies_hypothesis_id_hypotheses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_strategies"),
    )
    op.create_index("ix_strategies_merchant_id", "strategies", ["merchant_id"])
    op.create_index("ix_strategies_agent_run_id", "strategies", ["agent_run_id"])

    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=True),
        sa.Column("hypothesis_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("primary_metric", sa.String(length=128), nullable=False),
        sa.Column("guardrail_metrics", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("window", sa.String(length=32), nullable=False),
        sa.Column("min_sample", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("approval_id", sa.Uuid(), nullable=True),
        sa.Column("control_description", sa.Text(), nullable=False),
        sa.Column("variant_description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_experiments_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name="fk_experiments_opportunity_id_opportunities", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["hypotheses.id"], name="fk_experiments_hypothesis_id_hypotheses", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_experiments"),
    )
    op.create_index("ix_experiments_merchant_id", "experiments", ["merchant_id"])

    op.create_table(
        "fact_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("metric", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("window", sa.String(length=32), nullable=False),
        sa.Column("method", sa.String(length=128), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("experiment_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_fact_snapshots_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_fact_snapshots_product_id_products", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], name="fk_fact_snapshots_experiment_id_experiments", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_fact_snapshots"),
    )
    op.create_index("ix_fact_snapshots_merchant_id", "fact_snapshots", ["merchant_id"])
    op.create_index("ix_fact_snapshots_merchant_metric", "fact_snapshots", ["merchant_id", "metric"])

    op.create_table(
        "experiment_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("visitor_key", sa.String(length=128), nullable=False),
        sa.Column("variant", sa.String(length=32), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_experiment_assignments_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], name="fk_experiment_assignments_experiment_id_experiments", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_experiment_assignments"),
        sa.UniqueConstraint("experiment_id", "visitor_key", name="uq_experiment_assignments_exp_visitor"),
    )
    op.create_index("ix_experiment_assignments_merchant_id", "experiment_assignments", ["merchant_id"])
    op.create_index("ix_experiment_assignments_experiment_id", "experiment_assignments", ["experiment_id"])

    op.create_table(
        "experiment_observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("variant", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("metric", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("claim_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_experiment_observations_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], name="fk_experiment_observations_experiment_id_experiments", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_experiment_observations"),
    )
    op.create_index("ix_experiment_observations_merchant_id", "experiment_observations", ["merchant_id"])
    op.create_index("ix_experiment_observations_experiment_id", "experiment_observations", ["experiment_id"])

    op.create_table(
        "experiment_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("claim_type", sa.String(length=32), nullable=False),
        sa.Column("primary_delta", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("guardrail_breaches", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("method", sa.String(length=128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_experiment_results_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], name="fk_experiment_results_experiment_id_experiments", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_experiment_results"),
        sa.UniqueConstraint("experiment_id", name="uq_experiment_results_experiment_id"),
    )
    op.create_index("ix_experiment_results_merchant_id", "experiment_results", ["merchant_id"])

    op.create_table(
        "simulation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_id", sa.Uuid(), nullable=False),
        sa.Column("assumption_hash", sa.String(length=64), nullable=False),
        sa.Column("outputs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("claim_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_simulation_results_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], name="fk_simulation_results_agent_run_id_agent_runs", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], name="fk_simulation_results_strategy_id_strategies", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_simulation_results"),
    )
    op.create_index("ix_simulation_results_merchant_id", "simulation_results", ["merchant_id"])

    op.create_table(
        "growth_dna",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_experiment_id", sa.Uuid(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("actor", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_growth_dna_merchant_id_merchants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_experiment_id"], ["experiments.id"], name="fk_growth_dna_evidence_experiment_id_experiments", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_growth_dna"),
    )
    op.create_index("ix_growth_dna_merchant_id", "growth_dna", ["merchant_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor", sa.String(length=32), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("permission_outcome", sa.String(length=32), nullable=False),
        sa.Column("kill_switch_state", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_audit_log_merchant_id_merchants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        sa.UniqueConstraint("merchant_id", "idempotency_key", name="uq_audit_log_merchant_idempotency"),
    )
    op.create_index("ix_audit_log_merchant_id", "audit_log", ["merchant_id"])
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_append_only()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_audit_log_no_update
        BEFORE UPDATE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_append_only();

        CREATE TRIGGER trg_audit_log_no_delete
        BEFORE DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_append_only();
        """
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("job_key", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("run_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_jobs_merchant_id_merchants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
        sa.UniqueConstraint("job_key", name="uq_jobs_job_key"),
    )
    op.create_index("ix_jobs_merchant_id", "jobs", ["merchant_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_delete ON audit_log;")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_update ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS audit_log_append_only();")
    op.drop_table("jobs")
    op.drop_table("audit_log")
    op.drop_table("growth_dna")
    op.drop_table("simulation_results")
    op.drop_table("experiment_results")
    op.drop_table("experiment_observations")
    op.drop_table("experiment_assignments")
    op.drop_table("fact_snapshots")
    op.drop_table("experiments")
    op.drop_table("strategies")
    op.drop_table("hypotheses")
    op.drop_table("tool_calls")
    op.drop_table("agent_messages")
    op.drop_table("agent_runs")
    op.drop_table("opportunities")
    op.drop_table("permission_policies")
    op.drop_table("events")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("products")
    op.drop_table("users")
    op.drop_table("merchants")
