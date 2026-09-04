from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GrowthDnaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    kind: str
    key: str
    body: dict[str, Any]
    evidence_experiment_id: UUID | None
    active: bool
    actor: str | None
    created_at: datetime
    updated_at: datetime