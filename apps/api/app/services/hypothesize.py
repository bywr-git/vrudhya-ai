"""Deterministic hypothesis generation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Diagnosis, Hypothesis
from app.models.enums import HypothesisStatus
from app.services.context import MerchantContext


async def hypothesize_diagnosis(
    session: AsyncSession,
    ctx: MerchantContext,
    diagnosis_id: UUID,
) -> Hypothesis:
    """Generate a testable hypothesis from a persisted diagnosis."""

    diagnosis = (
        await session.execute(
            select(Diagnosis).where(
                Diagnosis.id == diagnosis_id,
                Diagnosis.merchant_id == ctx.merchant_id,
            )
        )
    ).scalar_one_or_none()

    if diagnosis is None:
        raise ValueError("Diagnosis not found")

    statement = (
        "A targeted product-detail-page change can improve "
        "product-view-to-purchase conversion without requiring "
        "additional traffic."
    )

    hypothesis = Hypothesis(
        merchant_id=ctx.merchant_id,
        agent_run_id=diagnosis.agent_run_id,
        statement=statement,
        supporting_fact_ids=list(diagnosis.supporting_fact_ids),
        contradicting_fact_ids=[],
        confidence=min(float(diagnosis.confidence), 0.85),
        uncertainty=(
            "The diagnosis establishes an observed conversion gap, "
            "but the effect of a specific PDP change has not yet been measured."
        ),
        status=HypothesisStatus.proposed.value,
    )

    session.add(hypothesis)
    await session.flush()

    return hypothesis