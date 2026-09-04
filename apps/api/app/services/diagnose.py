"""Deterministic diagnosis service.

This phase does not call an LLM. It creates an evidence-grounded
diagnosis from persisted opportunity evidence.
"""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRun, Diagnosis, FactSnapshot, Opportunity
from app.models.enums import AgentRunState, OpportunityStatus
from app.services.context import MerchantContext


async def diagnose_opportunity(
    session: AsyncSession,
    ctx: MerchantContext,
    opportunity_id: UUID,
) -> Diagnosis:
    """Create an evidence-grounded diagnosis for an opportunity."""

    opportunity = (
        await session.execute(
            select(Opportunity).where(
                Opportunity.id == opportunity_id,
                Opportunity.merchant_id == ctx.merchant_id,
            )
        )
    ).scalar_one_or_none()

    if opportunity is None:
        raise ValueError("Opportunity not found")

    fact_ids = list(opportunity.evidence_fact_ids or [])

    if not fact_ids:
        raise ValueError("Opportunity has no evidence facts")

    facts = (
        await session.execute(
            select(FactSnapshot).where(
                FactSnapshot.merchant_id == ctx.merchant_id,
                FactSnapshot.id.in_(fact_ids),
            )
        )
    ).scalars().all()

    facts_by_id = {fact.id: fact for fact in facts}

    # Every evidence ID must belong to this merchant and exist.
    if len(facts_by_id) != len(fact_ids):
        raise ValueError("Opportunity contains invalid evidence fact IDs")

    # Pin the exact evidence used by this reasoning run.
    agent_run = AgentRun(
        id=uuid4(),
        merchant_id=ctx.merchant_id,
        opportunity_id=opportunity.id,
        pinned_fact_ids=fact_ids,
        state=AgentRunState.running.value,
    )

    session.add(agent_run)
    await session.flush()

    views = _get_metric(facts_by_id, "product_views")
    conversion = _get_metric(
        facts_by_id,
        "product_view_to_purchase_conversion_rate",
    )

    if views is not None and conversion is not None:
        statement = (
            f"The product receives substantial traffic ({views.value} views) "
            f"but converts poorly ({float(conversion.value) * 100:.2f}%). "
            "The observed evidence indicates a conversion opportunity "
            "rather than a traffic shortage."
        )
        uncertainty = (
            "The observed data identifies a conversion gap but does not "
            "establish its causal mechanism. Further experimentation is "
            "required to determine which storefront change improves conversion."
        )
        confidence = 0.90
    else:
        statement = (
            "The detected opportunity has persisted evidence, but the "
            "available facts are insufficient to establish a specific cause."
        )
        uncertainty = (
            "Additional product-level evidence is required before making "
            "a strong causal diagnosis."
        )
        confidence = 0.60

    diagnosis = Diagnosis(
        merchant_id=ctx.merchant_id,
        opportunity_id=opportunity.id,
        agent_run_id=agent_run.id,
        statement=statement,
        supporting_fact_ids=fact_ids,
        confidence=confidence,
        uncertainty=uncertainty,
        model_version="deterministic_v1",
    )

    session.add(diagnosis)

    opportunity.status = OpportunityStatus.investigating.value
    agent_run.state = AgentRunState.completed.value

    await session.flush()

    return diagnosis


def _get_metric(
    facts: dict[UUID, FactSnapshot],
    metric: str,
) -> FactSnapshot | None:
    for fact in facts.values():
        if fact.metric == metric:
            return fact

    return None