"""Merchant-scoped read APIs for persisted intelligence and experiments."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.models import Diagnosis, Experiment, ExperimentResult, Hypothesis, Opportunity, Strategy
from app.schemas.diagnosis import DiagnosisOut
from app.schemas.hypotheses import HypothesisOut
from app.schemas.intelligence import (
    ExperimentOut,
    ExperimentResultOut,
    OpportunityHypothesesOut,
    OpportunityStrategiesOut,
)
from app.schemas.strategies import StrategyOut
from app.services.context import MerchantContext

router = APIRouter(tags=["intelligence"])


async def _opportunity(
    session: AsyncSession, ctx: MerchantContext, opportunity_id: UUID
) -> Opportunity:
    opportunity = (await session.execute(select(Opportunity).where(
        Opportunity.id == opportunity_id,
        Opportunity.merchant_id == ctx.merchant_id,
    ))).scalar_one_or_none()
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opportunity


@router.get("/v1/opportunities/{opportunity_id}/diagnosis", response_model=DiagnosisOut)
async def get_diagnosis(
    opportunity_id: UUID,
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosisOut:
    await _opportunity(session, ctx, opportunity_id)
    diagnosis = (await session.execute(select(Diagnosis).where(
        Diagnosis.opportunity_id == opportunity_id,
        Diagnosis.merchant_id == ctx.merchant_id,
    ).order_by(Diagnosis.created_at.desc()))).scalars().first()
    if diagnosis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis not found")
    return DiagnosisOut.model_validate(diagnosis)


@router.get("/v1/opportunities/{opportunity_id}/hypotheses", response_model=OpportunityHypothesesOut)
async def get_hypotheses(
    opportunity_id: UUID,
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> OpportunityHypothesesOut:
    await _opportunity(session, ctx, opportunity_id)
    run_ids = select(Diagnosis.agent_run_id).where(
        Diagnosis.opportunity_id == opportunity_id,
        Diagnosis.merchant_id == ctx.merchant_id,
    )
    hypotheses = (await session.execute(select(Hypothesis).where(
        Hypothesis.merchant_id == ctx.merchant_id,
        Hypothesis.agent_run_id.in_(run_ids),
    ).order_by(Hypothesis.created_at))).scalars().all()
    if not hypotheses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hypotheses not found")
    return OpportunityHypothesesOut(
        opportunity_id=opportunity_id,
        hypotheses=[HypothesisOut.model_validate(item) for item in hypotheses],
    )


@router.get("/v1/opportunities/{opportunity_id}/strategies", response_model=OpportunityStrategiesOut)
async def get_strategies(
    opportunity_id: UUID,
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> OpportunityStrategiesOut:
    await _opportunity(session, ctx, opportunity_id)
    run_ids = select(Diagnosis.agent_run_id).where(
        Diagnosis.opportunity_id == opportunity_id,
        Diagnosis.merchant_id == ctx.merchant_id,
    )
    hypothesis_ids = select(Hypothesis.id).where(
        Hypothesis.merchant_id == ctx.merchant_id,
        Hypothesis.agent_run_id.in_(run_ids),
    )
    strategies = (await session.execute(select(Strategy).where(
        Strategy.merchant_id == ctx.merchant_id,
        Strategy.hypothesis_id.in_(hypothesis_ids),
    ).order_by(Strategy.created_at))).scalars().all()
    if not strategies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategies not found")
    return OpportunityStrategiesOut(
        opportunity_id=opportunity_id,
        strategies=[StrategyOut.model_validate(item) for item in strategies],
    )


@router.get("/v1/experiments/{experiment_id}", response_model=ExperimentOut)
async def get_experiment(
    experiment_id: UUID,
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentOut:
    experiment = (await session.execute(select(Experiment).where(
        Experiment.id == experiment_id,
        Experiment.merchant_id == ctx.merchant_id,
    ))).scalar_one_or_none()
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return ExperimentOut.model_validate(experiment)


@router.get("/v1/experiments/{experiment_id}/result", response_model=ExperimentResultOut)
async def get_experiment_result(
    experiment_id: UUID,
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentResultOut:
    experiment = (await session.execute(select(Experiment).where(
        Experiment.id == experiment_id,
        Experiment.merchant_id == ctx.merchant_id,
    ))).scalar_one_or_none()
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    result = (await session.execute(select(ExperimentResult).where(
        ExperimentResult.experiment_id == experiment.id,
        ExperimentResult.merchant_id == ctx.merchant_id,
    ))).scalar_one_or_none()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment result not available")
    return ExperimentResultOut.model_validate(result)