"""Opportunity Radar API contracts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.facts import FactSnapshotOut


class OpportunityOut(BaseModel):
    id: UUID
    merchant_id: UUID
    detector_id: str
    entity_type: str
    entity_id: UUID
    score: Decimal
    evidence_fact_ids: list[UUID]
    status: str
    created_at: datetime
    updated_at: datetime


class OpportunityDetailOut(OpportunityOut):
    evidence: list[FactSnapshotOut]