from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.diagnosis import DiagnosisOut
from app.schemas.hypotheses import HypothesisOut
from app.schemas.strategies import StrategyOut


class OpportunityDiagnosisOut(DiagnosisOut):
    pass


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


class ExperimentResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    experiment_id: UUID
    claim_type: str
    primary_delta: Decimal | None
    guardrail_breaches: dict[str, Any] | None
    method: str
    notes: str | None
    created_at: datetime


class OpportunityHypothesesOut(BaseModel):
    opportunity_id: UUID
    hypotheses: list[HypothesisOut]


class OpportunityStrategiesOut(BaseModel):
    opportunity_id: UUID
    strategies: list[StrategyOut]