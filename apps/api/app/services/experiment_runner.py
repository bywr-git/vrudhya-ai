"""Deterministic synthetic experiment execution."""

import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment, ExperimentAssignment, ExperimentObservation
from app.models.enums import ActionType, ExperimentStatus, ExperimentVariant
from app.services.context import MerchantContext

RUN_NAMESPACE = UUID("6e6e8c42-65d4-45c6-a1a6-6dcd6e3d4a12")
SUPPORTED_ACTIONS = {ActionType.synthetic_pdp_copy.value, ActionType.synthetic_price_test.value}
BLOCKED_ACTIONS = {
    ActionType.razorpay_payment_link.value,
    ActionType.razorpay_payment_link_with_offer.value,
    ActionType.razorpay_cancel_payment_link.value,
}


async def run_experiment(
    session: AsyncSession,
    ctx: MerchantContext,
    experiment_id: UUID,
) -> tuple[Experiment, int, int]:
    experiment = (await session.execute(select(Experiment).where(
        Experiment.id == experiment_id, Experiment.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    if experiment is None:
        raise ValueError("Experiment not found")
    if experiment.action_type in BLOCKED_ACTIONS:
        raise ValueError("Razorpay actions are not executable in V1")
    if experiment.action_type not in SUPPORTED_ACTIONS:
        raise ValueError("Action type is not executable by the synthetic runner")
    if experiment.status == ExperimentStatus.running.value:
        assignments = (await session.execute(select(ExperimentAssignment).where(
            ExperimentAssignment.merchant_id == ctx.merchant_id,
            ExperimentAssignment.experiment_id == experiment.id,
        ))).scalars().all()
        observations = (await session.execute(select(ExperimentObservation).where(
            ExperimentObservation.merchant_id == ctx.merchant_id,
            ExperimentObservation.experiment_id == experiment.id,
        ))).scalars().all()
        return experiment, len(assignments), len(observations)
    if experiment.status != ExperimentStatus.approved.value:
        raise ValueError("Only approved experiments can run")

    experiment.status = ExperimentStatus.running.value
    assignment_count = 0
    for index in range(max(experiment.min_sample, 100)):
        visitor_key = f"experiment-{experiment.id}-visitor-{index:05d}"
        digest = hashlib.sha256(f"{experiment.id}:{visitor_key}:{experiment.params}".encode()).digest()
        variant = ExperimentVariant.variant.value if digest[0] % 2 else ExperimentVariant.control.value
        session.add(ExperimentAssignment(
            merchant_id=ctx.merchant_id, experiment_id=experiment.id, visitor_key=visitor_key,
            variant=variant, assigned_at=datetime.now(timezone.utc),
        ))
        assignment_count += 1
    await session.flush()
    await _create_observations(session, ctx, experiment)
    observations = (await session.execute(select(ExperimentObservation).where(
        ExperimentObservation.merchant_id == ctx.merchant_id,
        ExperimentObservation.experiment_id == experiment.id,
    ))).scalars().all()
    return experiment, assignment_count, len(observations)


async def _create_observations(session: AsyncSession, ctx: MerchantContext, experiment: Experiment) -> None:
    assignments = (await session.execute(select(ExperimentAssignment).where(
        ExperimentAssignment.merchant_id == ctx.merchant_id,
        ExperimentAssignment.experiment_id == experiment.id,
    ))).scalars().all()
    counts: dict[str, dict[str, int]] = {
        ExperimentVariant.control.value: {"views": 0, "add_to_cart": 0, "checkout": 0, "purchases": 0, "revenue": 0},
        ExperimentVariant.variant.value: {"views": 0, "add_to_cart": 0, "checkout": 0, "purchases": 0, "revenue": 0},
    }
    for assignment in assignments:
        values = counts[assignment.variant]
        values["views"] += 1
        digest = hashlib.sha256(f"{experiment.id}:{assignment.visitor_key}:{experiment.params}".encode()).digest()
        threshold = 18 if assignment.variant == ExperimentVariant.control.value else 22
        if digest[1] % 100 < threshold:
            values["add_to_cart"] += 1
        if digest[2] % 100 < threshold - 5:
            values["checkout"] += 1
        if digest[3] % 100 < (threshold - 10):
            values["purchases"] += 1
            values["revenue"] += 10000
    today = date.today()
    for variant, values in counts.items():
        metrics = [
            ("views", values["views"], "count", values["views"]),
            ("add_to_cart", values["add_to_cart"], "count", values["views"]),
            ("checkout", values["checkout"], "count", values["views"]),
            ("purchases", values["purchases"], "count", values["views"]),
            ("revenue", values["revenue"], "paise", values["purchases"]),
        ]
        for metric, value, unit, sample_size in metrics:
            session.add(ExperimentObservation(
                merchant_id=ctx.merchant_id, experiment_id=experiment.id, observed_on=today,
                variant=variant, source="synthetic.storefront", metric=metric,
                value=Decimal(value), unit=unit, sample_size=sample_size, claim_type="observation",
            ))
    await session.flush()