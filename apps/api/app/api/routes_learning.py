"""Phase 6 learning and deterministic agent-loop routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.schemas.agent_loop import AgentLoopOut
from app.schemas.growth_dna import GrowthDnaOut
from app.schemas.learning import LearningOut, LearningRequest
from app.services.agent_loop import continue_agent_loop
from app.services.context import MerchantContext
from app.services.growth_dna import list_growth_dna, update_growth_dna
from app.services.learn import learn_from_experiment

router = APIRouter(prefix="/v1/learning", tags=["learning"])


def _learning_out(decision, dna=None, next_opportunity_id=None) -> LearningOut:
    return LearningOut(
        experiment_id=decision.experiment.id,
        experiment_result_id=decision.result.id,
        outcome=decision.outcome,
        claim_type=decision.claim_type,
        explanation=decision.explanation,
        evidence=decision.evidence,
        growth_dna_updated=dna is not None,
        growth_dna_id=dna.id if dna is not None else None,
    )


@router.post("/experiments/{experiment_id}/learn", response_model=LearningOut)
async def learn(experiment_id: UUID, ctx: MerchantContext = Depends(get_current_merchant), session: AsyncSession = Depends(get_db_session)):
    try:
        decision = await learn_from_experiment(session, ctx, experiment_id)
        dna = await update_growth_dna(session, ctx, decision)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _learning_out(decision, dna)


@router.post("/experiments/{experiment_id}/continue", response_model=AgentLoopOut)
async def continue_loop(experiment_id: UUID, payload: LearningRequest | None = None, ctx: MerchantContext = Depends(get_current_merchant), session: AsyncSession = Depends(get_db_session)):
    try:
        decision, dna, opportunity = await continue_agent_loop(
            session, ctx, experiment_id, payload.create_next_opportunity if payload else True
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AgentLoopOut(learning=_learning_out(decision, dna, opportunity.id if opportunity else None),
                        next_opportunity_id=opportunity.id if opportunity else None,
                        next_stage="diagnose" if opportunity else "stopped_before_execution")


@router.get("/growth-dna", response_model=list[GrowthDnaOut])
async def growth_dna(ctx: MerchantContext = Depends(get_current_merchant), session: AsyncSession = Depends(get_db_session)):
    return await list_growth_dna(session, ctx)