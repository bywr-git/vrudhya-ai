"""Continue the deterministic loop up to the next opportunity, never execution."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Opportunity
from app.services.context import MerchantContext
from app.services.growth_dna import update_growth_dna
from app.services.learn import LearningDecision, learn_from_experiment


async def continue_agent_loop(
    session: AsyncSession,
    ctx: MerchantContext,
    experiment_id: UUID,
    create_next_opportunity: bool = True,
) -> tuple[LearningDecision, object, Opportunity | None]:
    decision = await learn_from_experiment(session, ctx, experiment_id)
    dna = await update_growth_dna(session, ctx, decision)
    opportunity = None
    if create_next_opportunity and decision.outcome in {"supported", "rejected"}:
        source = decision.experiment.opportunity_id
        if source is not None:
            original = (await session.execute(select(Opportunity).where(
                Opportunity.id == source,
                Opportunity.merchant_id == ctx.merchant_id,
            ))).scalar_one_or_none()
            if original is not None:
                detector_id = f"phase6_{decision.outcome}_{decision.experiment.id}"
                opportunity = (await session.execute(select(Opportunity).where(
                    Opportunity.merchant_id == ctx.merchant_id,
                    Opportunity.detector_id == detector_id,
                    Opportunity.entity_id == original.entity_id,
                ))).scalar_one_or_none()
                if opportunity is None:
                    opportunity = Opportunity(
                        merchant_id=ctx.merchant_id,
                        detector_id=detector_id,
                        entity_type=original.entity_type,
                        entity_id=original.entity_id,
                        score=original.score,
                        evidence_fact_ids=list(original.evidence_fact_ids),
                        status="open",
                    )
                    session.add(opportunity)
                    await session.flush()
    return decision, dna, opportunity