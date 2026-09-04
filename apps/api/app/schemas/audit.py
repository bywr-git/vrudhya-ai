from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor: str
    merchant_id: UUID
    action: str
    target: dict[str, Any]
    timestamp: datetime
    idempotency_key: str
    result: str
    permission_outcome: str
    kill_switch_state: bool
