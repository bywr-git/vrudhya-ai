from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StrategyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    agent_run_id: UUID
    hypothesis_id: UUID
    action_type: str
    rationale: str
    impact_assumptions: dict[str, Any]
    expected_direction: str
    cost: str
    risk: str
    implementation_complexity: str
    primary_metric: str
    guardrail_metrics: list[str]
    proposed_change: dict[str, Any]
    created_at: datetime