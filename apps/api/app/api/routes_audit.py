"""Merchant-scoped read access to the existing append-only audit log."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.models import AuditLog
from app.schemas.audit import AuditLogOut
from app.services.context import MerchantContext

router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> list[AuditLogOut]:
    logs = (await session.execute(select(AuditLog).where(
        AuditLog.merchant_id == ctx.merchant_id,
    ).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()))).scalars().all()
    return [AuditLogOut.model_validate(log) for log in logs]
