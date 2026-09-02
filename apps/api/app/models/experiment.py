"""Experiment lifecycle tables. Assignment and measurement engines come later."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ClaimType, ExperimentStatus, ExperimentVariant


class Experiment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiments"

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        nullable=True,
    )
    hypothesis_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("hypotheses.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    primary_metric: Mapped[str] = mapped_column(String(128), nullable=False)
    guardrail_metrics: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    window: Mapped[str] = mapped_column(String(32), nullable=False)
    min_sample: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ExperimentStatus.draft.value)
    approval_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    control_description: Mapped[str] = mapped_column(Text, nullable=False)
    variant_description: Mapped[str] = mapped_column(Text, nullable=False)


class ExperimentAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "experiment_assignments"
    __table_args__ = (
        UniqueConstraint("experiment_id", "visitor_key", name="uq_experiment_assignments_exp_visitor"),
    )

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visitor_key: Mapped[str] = mapped_column(String(128), nullable=False)
    variant: Mapped[str] = mapped_column(String(32), nullable=False, default=ExperimentVariant.unassigned.value)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExperimentObservation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "experiment_observations"

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observed_on: Mapped[date] = mapped_column(Date, nullable=False)
    variant: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    metric: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(32), nullable=False, default=ClaimType.observation.value)


class ExperimentResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "experiment_results"

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    claim_type: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_delta: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    guardrail_breaches: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    method: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SimulationResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "simulation_results"

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    strategy_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("strategies.id", ondelete="CASCADE"),
        nullable=False,
    )
    assumption_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(32), nullable=False, default=ClaimType.simulation.value)
