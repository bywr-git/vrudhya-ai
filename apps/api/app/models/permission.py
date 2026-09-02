"""Per-merchant permission policy JSON. Permission engine is a later phase."""

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PermissionPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "permission_policies"

    merchant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    policy: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
