"""Explicit merchant approval for experiment lifecycle transitions."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment
from app.models.enums import ExperimentStatus
from app.services.context import MerchantContext


async def approve_or_reject_experiment(
    session: AsyncSession,
    ctx: MerchantContext,
    experiment_id: UUID,
    approved: bool,
) -> Experiment:
    experiment = (await session.execute(select(Experiment).where(
        Experiment.id == experiment_id, Experiment.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    if experiment is None:
        raise ValueError("Experiment not found")
    if experiment.status != ExperimentStatus.awaiting_approval.value:
        raise ValueError("Only awaiting_approval experiments can be approved or rejected")
    if approved:
        experiment.status = ExperimentStatus.approved.value
        experiment.approval_id = uuid4()
    else:
        experiment.status = ExperimentStatus.rejected_by_merchant.value
        experiment.approval_id = None
    await session.flush()
    return experiment