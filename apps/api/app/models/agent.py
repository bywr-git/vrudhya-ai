"""Agent run traces, hypotheses, and strategies. No LLM calls in this phase."""

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AgentRunState, HypothesisStatus


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"

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
    pinned_fact_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)),
        nullable=False,
        default=list,
    )
    state: Mapped[str] = mapped_column(String(32), nullable=False, default=AgentRunState.created.value)


class AgentMessage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "agent_messages"

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
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class ToolCall(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "tool_calls"

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
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class Hypothesis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hypotheses"

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
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_fact_ids: Mapped[list[UUID]] = mapped_column(ARRAY(Uuid(as_uuid=True)), nullable=False)
    contradicting_fact_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)),
        nullable=False,
        default=list,
    )
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    uncertainty: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=HypothesisStatus.proposed.value)


class Strategy(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "strategies"

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
        index=True,
    )
    hypothesis_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("hypotheses.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    impact_assumptions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    expected_direction: Mapped[str] = mapped_column(String(32), nullable=False)
    cost: Mapped[str] = mapped_column(String(64), nullable=False)
    risk: Mapped[str] = mapped_column(String(64), nullable=False)
    implementation_complexity: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_metric: Mapped[str] = mapped_column(String(128), nullable=False)
    guardrail_metrics: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    proposed_change: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
