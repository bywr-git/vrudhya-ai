"""Opportunities created only by the detection engine (later phase)."""

from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Uuid, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import OpportunityStatus


class Opportunity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (UniqueConstraint("merchant_id", "detector_id", "entity_id", name="uq_opportunities_detector_entity"),)

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    detector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    evidence_fact_ids: Mapped[list[UUID]] = mapped_column(ARRAY(Uuid(as_uuid=True)), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=OpportunityStatus.open.value)
