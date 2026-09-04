"""Deterministic daily aggregates derived from canonical storefront events."""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class EventDaily(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "events_daily"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id", "product_id", "day", "channel", "variant",
            name="uq_events_daily_scope",
        ),
    )

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False, default="synthetic")
    variant: Mapped[str] = mapped_column(String(32), nullable=False, default="unassigned")
    sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pdp_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    atc: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checkouts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)