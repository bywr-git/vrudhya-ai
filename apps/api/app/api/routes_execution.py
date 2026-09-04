"""Phase 5 execution and measurement routes."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.schemas.execution import ApprovalRequest, ExecutionOut, MeasurementOut, MetricComparison, RunOut
from app.services.context import MerchantContext
from app.services.experiment_approval import approve_or_reject_experiment
from app.services.experiment_runner import run_experiment
from app.services.measurement import measure_experiment

router = APIRouter(prefix="/v1/experiments", tags=["execution"])


@router.post("/{experiment_id}/approve", response_model=ExecutionOut)
async def approve(experiment_id: UUID, payload: ApprovalRequest, ctx: MerchantContext = Depends(get_current_merchant), session: AsyncSession = Depends(get_db_session)):
    try:
        experiment = await approve_or_reject_experiment(session, ctx, experiment_id, payload.approved)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExecutionOut(experiment_id=experiment.id, status=experiment.status, approval_id=experiment.approval_id,
                        detail="Experiment approved" if payload.approved else "Experiment rejected")


@router.post("/{experiment_id}/reject", response_model=ExecutionOut)
async def reject(experiment_id: UUID, ctx: MerchantContext = Depends(get_current_merchant), session: AsyncSession = Depends(get_db_session)):
    return await approve(experiment_id, ApprovalRequest(approved=False), ctx, session)


@router.post("/{experiment_id}/run", response_model=RunOut)
async def run(experiment_id: UUID, ctx: MerchantContext = Depends(get_current_merchant), session: AsyncSession = Depends(get_db_session)):
    try:
        experiment, assignments, observations = await run_experiment(session, ctx, experiment_id)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RunOut(experiment_id=experiment.id, status=experiment.status, assignments=assignments, observations=observations)


@router.post("/{experiment_id}/measure", response_model=MeasurementOut)
async def measure(experiment_id: UUID, ctx: MerchantContext = Depends(get_current_merchant), session: AsyncSession = Depends(get_db_session)):
    try:
        result = await measure_experiment(session, ctx, experiment_id)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    data = result.guardrail_breaches or {}
    primary = data["primary"]
    trace = json.loads(result.notes or "{}")
    return MeasurementOut(experiment_id=result.experiment_id, status="measured", claim_type=result.claim_type,
                          primary=MetricComparison(**primary),
                          guardrails=[MetricComparison(**comparison) for comparison in data.get("guardrails", {}).values()],
                          observation_ids=trace.get("observation_ids", []), result_id=result.id)