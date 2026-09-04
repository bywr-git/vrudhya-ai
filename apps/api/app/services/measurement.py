"""Deterministic experiment measurement from persisted observations."""

import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment, ExperimentObservation, ExperimentResult
from app.models.enums import ExperimentStatus
from app.services.context import MerchantContext


async def measure_experiment(session: AsyncSession, ctx: MerchantContext, experiment_id: UUID) -> ExperimentResult:
    experiment = (await session.execute(select(Experiment).where(
        Experiment.id == experiment_id, Experiment.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    if experiment is None:
        raise ValueError("Experiment not found")
    if experiment.status != ExperimentStatus.running.value:
        raise ValueError("Only running experiments can be measured")
    observations = list((await session.execute(select(ExperimentObservation).where(
        ExperimentObservation.experiment_id == experiment.id,
        ExperimentObservation.merchant_id == ctx.merchant_id,
    ).order_by(ExperimentObservation.id))).scalars().all())
    if not observations:
        raise ValueError("Experiment has no observations")
    result_values = {metric: _compare(observations, metric) for metric in [experiment.primary_metric, *experiment.guardrail_metrics]}
    primary = result_values[experiment.primary_metric]
    result = ExperimentResult(
        merchant_id=ctx.merchant_id, experiment_id=experiment.id, claim_type="measured",
        primary_delta=Decimal(primary["absolute_difference"]),
        guardrail_breaches={"primary": primary, "guardrails": {k: v for k, v in result_values.items() if k != experiment.primary_metric}},
        method="deterministic_observation_comparison_v1",
        notes=json.dumps({"observation_ids": [str(observation.id) for observation in observations]}, sort_keys=True),
    )
    session.add(result)
    experiment.status = ExperimentStatus.measured.value
    await session.flush()
    return result


def _compare(observations: list[ExperimentObservation], metric: str) -> dict[str, str | None]:
    rows = [row for row in observations if row.metric == metric]
    values = {row.variant: Decimal(row.value) for row in rows}
    if metric in {"conversion_rate", "product_view_to_purchase_conversion_rate"}:
        views = {row.variant: Decimal(row.value) for row in observations if row.metric == "views"}
        purchases = {row.variant: Decimal(row.value) for row in observations if row.metric == "purchases"}
        values = {variant: (purchases.get(variant, Decimal(0)) / denominator if denominator else Decimal(0))
                  for variant, denominator in views.items()}
    control = values.get("control", Decimal(0))
    variant = values.get("variant", Decimal(0))
    absolute = variant - control
    relative = (absolute / control) if control else None
    return {"metric": metric, "control_metric": str(control), "variant_metric": str(variant),
            "absolute_difference": str(absolute), "relative_difference": str(relative) if relative is not None else None}