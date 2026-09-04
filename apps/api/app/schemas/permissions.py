from uuid import UUID

from pydantic import BaseModel


class PermissionOut(BaseModel):
    merchant_id: UUID
    strategy_id: UUID
    action_type: str
    outcome: str
    reason: str