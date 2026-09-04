from typing import Any
from uuid import UUID

from pydantic import BaseModel


class LearningOut(BaseModel):
    experiment_id: UUID
    experiment_result_id: UUID
    outcome: str
    claim_type: str
    explanation: str
    evidence: dict[str, Any]
    growth_dna_updated: bool
    growth_dna_id: UUID | None


class LearningRequest(BaseModel):
    create_next_opportunity: bool = True