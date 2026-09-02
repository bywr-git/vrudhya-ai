"""Development-only merchant context. Not production authentication."""

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.models import Merchant
from app.services.access import TenantAccess
from app.services.context import MerchantContext

LUMI_GIFTS_NAME = "Lumi Gifts"


async def get_current_merchant(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> MerchantContext:
    """Resolve the demo merchant from application settings.

    When DATA_MODE=synthetic this is Lumi Gifts. This path must not run as
    production authentication.
    """
    if settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo authentication is disabled in production",
        )
    if settings.data_mode != "synthetic":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Non-synthetic merchant context is not implemented in this phase",
        )

    result = await session.execute(select(Merchant).where(Merchant.name == LUMI_GIFTS_NAME))
    merchant = result.scalar_one_or_none()
    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthetic merchant 'Lumi Gifts' is not seeded. Run scripts/seed_lumi_gifts.py",
        )
    return MerchantContext(
        merchant_id=merchant.id,
        name=merchant.name,
        data_mode=merchant.data_mode,
        autonomy_kill_switch=merchant.autonomy_kill_switch,
    )


async def get_tenant_access(
    session: AsyncSession = Depends(get_db_session),
    ctx: MerchantContext = Depends(get_current_merchant),
) -> TenantAccess:
    return TenantAccess(session, ctx)
