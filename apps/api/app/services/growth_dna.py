"""Persist measured learning as deterministic, merchant-scoped Growth DNA."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GrowthDna
from app.models.enums import Actor, DnaKind
from app.services.context import MerchantContext
from app.services.learn import LearningDecision


async def update_growth_dna(
    session: AsyncSession,
    ctx: MerchantContext,
    decision: LearningDecision,
) -> GrowthDna:
    existing = (await session.execute(select(GrowthDna).where(
        GrowthDna.merchant_id == ctx.merchant_id,
        GrowthDna.evidence_experiment_id == decision.experiment.id,
        GrowthDna.key == f"experiment:{decision.experiment.id}",
    ))).scalar_one_or_none()
    if existing is not None:
        return existing
    kind = {
        "supported": DnaKind.proven_play.value,
        "rejected": DnaKind.failed_play.value,
        "inconclusive": DnaKind.baseline.value,
    }[decision.outcome]
    dna = GrowthDna(
        merchant_id=ctx.merchant_id,
        kind=kind,
        key=f"experiment:{decision.experiment.id}",
        body={
            "outcome": decision.outcome,
            "claim_type": decision.claim_type,
            "explanation": decision.explanation,
            "evidence": decision.evidence,
        },
        evidence_experiment_id=decision.experiment.id,
        actor=Actor.system.value,
    )
    session.add(dna)
    await session.flush()
    return dna


async def list_growth_dna(session: AsyncSession, ctx: MerchantContext) -> list[GrowthDna]:
    return list((await session.execute(select(GrowthDna).where(
        GrowthDna.merchant_id == ctx.merchant_id,
        GrowthDna.active.is_(True),
    ).order_by(GrowthDna.created_at, GrowthDna.id))).scalars().all())