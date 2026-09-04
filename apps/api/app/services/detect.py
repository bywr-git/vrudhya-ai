"""Deterministic high-traffic/low-conversion detector."""

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FactSnapshot, Opportunity
from app.services.context import MerchantContext

DETECTOR_ID = "high_traffic_low_conversion_v1"


async def detect_opportunities(session: AsyncSession, ctx: MerchantContext) -> list[Opportunity]:
    facts = (await session.execute(
        select(FactSnapshot).where(FactSnapshot.merchant_id == ctx.merchant_id, FactSnapshot.product_id.is_not(None),
                                    FactSnapshot.window == "all_time").order_by(FactSnapshot.computed_at.desc())
    )).scalars().all()
    latest: dict[tuple[object, str], FactSnapshot] = {}
    for fact in facts:
        latest.setdefault((fact.product_id, fact.metric), fact)
    by_product: dict[object, dict[str, FactSnapshot]] = {}
    for (product_id, metric), fact in latest.items():
        by_product.setdefault(product_id, {})[metric] = fact

    results: list[Opportunity] = []
    for product_id, product_facts in by_product.items():
        views = product_facts.get("product_views")
        conversion = product_facts.get("product_view_to_purchase_conversion_rate")
        if not views or not conversion or views.value < 500 or conversion.value >= Decimal("0.02"):
            continue
        score = (Decimal(views.value) / Decimal("500")) * (Decimal("0.02") - conversion.value) / Decimal("0.02")
        evidence_ids = [views.id, conversion.id]
        opportunity = (await session.execute(select(Opportunity).where(
            Opportunity.merchant_id == ctx.merchant_id, Opportunity.detector_id == DETECTOR_ID,
            Opportunity.entity_id == product_id,
        ))).scalar_one_or_none()
        if opportunity is None:
            opportunity = Opportunity(merchant_id=ctx.merchant_id, detector_id=DETECTOR_ID,
                                      entity_type="product", entity_id=product_id, score=score,
                                      evidence_fact_ids=evidence_ids)
            session.add(opportunity)
        else:
            opportunity.score = score
            opportunity.evidence_fact_ids = evidence_ids
        results.append(opportunity)
    await session.flush()
    return results