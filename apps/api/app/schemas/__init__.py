"""Pydantic response schemas for foundation read APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MerchantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    data_mode: str
    autonomy_kill_switch: bool
    created_at: datetime


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    sku: str
    name: str
    price_paise: int
    category: str
    status: str
    cost_paise: int | None
    created_at: datetime
    updated_at: datetime


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity: int
    unit_price_paise: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    customer_id: UUID | None
    status: str
    total_paise: int
    placed_at: datetime
    items: list[OrderItemOut] = Field(default_factory=list)


class HealthOut(BaseModel):
    status: str
    database: str
