"""FactSnapshot API contracts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class FactSnapshotOut(BaseModel):
    fact_id: UUID
    merchant_id: UUID
    metric: str
    value: Decimal
    unit: str
    window: str
    method: str
    source: str
    sample_size: int
    computed_at: datetime
    product_id: UUID | None
    experiment_id: UUID | None
    claim_type: str = "observation"