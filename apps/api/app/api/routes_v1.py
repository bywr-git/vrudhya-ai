"""Merchant-scoped foundation read endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_merchant, get_tenant_access
from app.schemas import MerchantOut, OrderOut, ProductOut
from app.services.access import TenantAccess
from app.services.context import MerchantContext

router = APIRouter(prefix="/v1", tags=["merchant"])


@router.get("/merchant", response_model=MerchantOut)
async def get_merchant(
    ctx: MerchantContext = Depends(get_current_merchant),
    access: TenantAccess = Depends(get_tenant_access),
) -> MerchantOut:
    merchant = await access.get_merchant()
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return MerchantOut.model_validate(merchant)


@router.get("/products", response_model=list[ProductOut])
async def list_products(access: TenantAccess = Depends(get_tenant_access)) -> list[ProductOut]:
    products = await access.list_products()
    return [ProductOut.model_validate(p) for p in products]


@router.get("/orders", response_model=list[OrderOut])
async def list_orders(access: TenantAccess = Depends(get_tenant_access)) -> list[OrderOut]:
    orders = await access.list_orders()
    return [OrderOut.model_validate(o) for o in orders]
