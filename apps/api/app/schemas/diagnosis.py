from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    opportunity_id: UUID
    agent_run_id: UUID
    statement: str
    supporting_fact_ids: list[UUID]
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: str
    model_version: str
    created_at: datetime