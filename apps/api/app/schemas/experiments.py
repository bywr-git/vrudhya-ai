from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.permissions import PermissionOut
from app.schemas.simulations import SimulationOut


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    opportunity_id: UUID | None
    hypothesis_id: UUID | None
    action_type: str
    params: dict[str, Any]
    primary_metric: str
    guardrail_metrics: list[str]
    window: str
    min_sample: int
    status: str
    approval_id: UUID | None
    control_description: str
    variant_description: str
    created_at: datetime
    updated_at: datetime


class ExperimentDraftOut(BaseModel):
    simulation: SimulationOut
    permission: PermissionOut
    experiment: ExperimentOut | None