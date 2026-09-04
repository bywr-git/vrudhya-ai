"""Merchant-scoped Opportunity Radar endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.schemas.facts import FactSnapshotOut
from app.schemas.opportunities import OpportunityDetailOut, OpportunityOut
from app.services.context import MerchantContext
from app.services.radar import get_opportunity_with_evidence, list_opportunities

router = APIRouter(prefix="/v1/opportunities", tags=["radar"])


def _fact_out(fact) -> FactSnapshotOut:
    return FactSnapshotOut(
        fact_id=fact.id, merchant_id=fact.merchant_id, metric=fact.metric, value=fact.value,
        unit=fact.unit, window=fact.window, method=fact.method, source=fact.source,
        sample_size=fact.sample_size, computed_at=fact.computed_at, product_id=fact.product_id,
        experiment_id=fact.experiment_id,
    )


@router.get("", response_model=list[OpportunityOut])
async def get_opportunities(
    session: AsyncSession = Depends(get_db_session),
    ctx: MerchantContext = Depends(get_current_merchant),
) -> list[OpportunityOut]:
    opportunities = await list_opportunities(session, ctx)
    return [OpportunityOut.model_validate(opportunity, from_attributes=True) for opportunity in opportunities]


@router.get("/{opportunity_id}", response_model=OpportunityDetailOut)
async def get_opportunity(
    opportunity_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    ctx: MerchantContext = Depends(get_current_merchant),
) -> OpportunityDetailOut:
    opportunity, evidence = await get_opportunity_with_evidence(session, ctx, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return OpportunityDetailOut(
        **OpportunityOut.model_validate(opportunity, from_attributes=True).model_dump(),
        evidence=[_fact_out(fact) for fact in evidence],
    )