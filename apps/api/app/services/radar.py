"""Merchant-scoped Opportunity Radar reads."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FactSnapshot, Opportunity
from app.services.context import MerchantContext


async def list_opportunities(session: AsyncSession, ctx: MerchantContext) -> list[Opportunity]:
    return list((await session.execute(select(Opportunity).where(
        Opportunity.merchant_id == ctx.merchant_id
    ).order_by(Opportunity.score.desc(), Opportunity.created_at))).scalars().all())


async def get_opportunity_with_evidence(
    session: AsyncSession, ctx: MerchantContext, opportunity_id: UUID
) -> tuple[Opportunity | None, list[FactSnapshot]]:
    opportunity = (await session.execute(select(Opportunity).where(
        Opportunity.id == opportunity_id, Opportunity.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    if opportunity is None:
        return None, []
    facts = list((await session.execute(select(FactSnapshot).where(
        FactSnapshot.merchant_id == ctx.merchant_id, FactSnapshot.id.in_(opportunity.evidence_fact_ids)
    ))).scalars().all())
    facts_by_id = {fact.id: fact for fact in facts}
    return opportunity, [facts_by_id[fact_id] for fact_id in opportunity.evidence_fact_ids if fact_id in facts_by_id]