"""Authenticated merchant context. merchant_id is never taken from tool arguments."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MerchantContext:
    merchant_id: UUID
    name: str
    data_mode: str
    autonomy_kill_switch: bool
