from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SimulationOut(BaseModel):
    id: UUID
    merchant_id: UUID
    agent_run_id: UUID
    strategy_id: UUID
    assumption_hash: str
    outputs: dict[str, Any]
    claim_type: str
    created_at: datetime