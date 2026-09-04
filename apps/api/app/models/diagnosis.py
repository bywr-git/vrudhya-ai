"""Evidence-grounded diagnoses for detected opportunities."""

from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class Diagnosis(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "diagnoses"

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    agent_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    supporting_fact_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    uncertainty: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="deterministic_v1",
    )