from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    approved: bool


class ExecutionOut(BaseModel):
    experiment_id: UUID
    status: str
    approval_id: UUID | None = None
    detail: str


class MetricComparison(BaseModel):
    metric: str
    control_metric: str
    variant_metric: str
    absolute_difference: str
    relative_difference: str | None


class MeasurementOut(BaseModel):
    experiment_id: UUID
    status: str
    claim_type: str
    primary: MetricComparison
    guardrails: list[MetricComparison]
    observation_ids: list[UUID]
    result_id: UUID


class RunOut(BaseModel):
    experiment_id: UUID
    status: str
    assignments: int
    observations: int