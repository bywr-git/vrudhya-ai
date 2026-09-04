"""Synthetic storefront event contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EventType


class StorefrontEventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: EventType
    occurred_at: datetime
    product_id: UUID | None = None
    visitor_key: str | None = Field(default=None, max_length=128)
    order_id: UUID | None = None
    payment_id: UUID | None = None
    channel: str = Field(default="synthetic", max_length=64)
    variant: str = Field(default="unassigned", max_length=32)
    revenue_paise: int = Field(default=0, ge=0)


class EventIngestResult(BaseModel):
    accepted: int
    duplicates: int