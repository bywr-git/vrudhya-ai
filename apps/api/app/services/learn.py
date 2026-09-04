"""Deterministic learning from measured experiment results only."""

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Experiment, ExperimentObservation, ExperimentResult
from app.models.enums import ClaimType, ExperimentStatus
from app.services.context import MerchantContext


@dataclass(frozen=True)
class LearningDecision:
    experiment: Experiment
    result: ExperimentResult
    outcome: str
    claim_type: str
    explanation: str
    evidence: dict[str, Any]


async def learn_from_experiment(
    session: AsyncSession,
    ctx: MerchantContext,
    experiment_id: UUID,
) -> LearningDecision:
    experiment = (await session.execute(select(Experiment).where(
        Experiment.id == experiment_id,
        Experiment.merchant_id == ctx.merchant_id,
    ))).scalar_one_or_none()
    if experiment is None:
        raise ValueError("Experiment not found")
    if experiment.status != ExperimentStatus.measured.value:
        raise ValueError("Only measured experiments can produce learning")

    result = (await session.execute(select(ExperimentResult).where(
        ExperimentResult.id == ExperimentResult.id,
        ExperimentResult.experiment_id == experiment.id,
        ExperimentResult.merchant_id == ctx.merchant_id,
    ))).scalar_one_or_none()
    if result is None:
        raise ValueError("Measured experiment result not found")
    if result.claim_type != "measured":
        raise ValueError("Experiment result is not measured")

    evidence = dict(result.guardrail_breaches or {})
    observation_ids = _observation_ids(result.notes)
    evidence["observation_ids"] = [str(observation_id) for observation_id in observation_ids]
    primary = evidence.get("primary")
    guardrails = evidence.get("guardrails", {})
    outcome, explanation = _classify(primary, guardrails)
    evidence["experiment_id"] = str(experiment.id)
    evidence["experiment_result_id"] = str(result.id)
    evidence["primary_metric"] = experiment.primary_metric
    if observation_ids:
        observations = (await session.execute(select(ExperimentObservation.id).where(
            ExperimentObservation.id.in_(observation_ids),
            ExperimentObservation.experiment_id == experiment.id,
            ExperimentObservation.merchant_id == ctx.merchant_id,
        ))).scalars().all()
        if len(observations) != len(observation_ids):
            raise ValueError("Measured result references invalid observations")
    return LearningDecision(
        experiment=experiment,
        result=result,
        outcome=outcome,
        claim_type=getattr(ClaimType, outcome).value,
        explanation=explanation,
        evidence=evidence,
    )


def _observation_ids(notes: str | None) -> list[UUID]:
    if not notes:
        return []
    try:
        values = json.loads(notes).get("observation_ids", [])
        return [UUID(value) for value in values]
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Measured result has invalid observation trace") from exc


def _classify(primary: dict[str, Any] | None, guardrails: dict[str, Any]) -> tuple[str, str]:
    """Classify without significance claims: positive/no breach=supported, negative/breach=rejected."""
    if not primary or primary.get("absolute_difference") is None:
        return "inconclusive", "The measured primary metric is unavailable."
    try:
        primary_delta = float(primary["absolute_difference"])
    except (TypeError, ValueError):
        return "inconclusive", "The measured primary metric is not numerically evaluable."
    if primary.get("relative_difference") is None:
        return "inconclusive", "Relative comparison is unavailable because the control metric is zero."
    try:
        guardrail_breach = any(
            comparison.get("absolute_difference") is not None
            and float(comparison["absolute_difference"]) < 0
            for comparison in guardrails.values()
        )
    except (TypeError, ValueError):
        return "inconclusive", "A guardrail metric is not numerically evaluable."
    if primary_delta < 0 or guardrail_breach:
        return "rejected", "The variant decreased the primary metric or breached a guardrail."
    if primary_delta > 0:
        return "supported", "The variant improved the primary metric without a blocking guardrail breach."
    return "inconclusive", "The measured primary metric was unchanged."