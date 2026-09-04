"""Deterministic strategy simulation. This module never executes actions."""

import hashlib
import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRun, FactSnapshot, Hypothesis, SimulationResult, Strategy
from app.models.enums import ClaimType
from app.services.context import MerchantContext


async def simulate_strategy(
    session: AsyncSession,
    ctx: MerchantContext,
    strategy_id: UUID,
) -> SimulationResult:
    strategy = (await session.execute(select(Strategy).where(
        Strategy.id == strategy_id, Strategy.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    if strategy is None:
        raise ValueError("Strategy not found")

    hypothesis = (await session.execute(select(Hypothesis).where(
        Hypothesis.id == strategy.hypothesis_id, Hypothesis.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    run = (await session.execute(select(AgentRun).where(
        AgentRun.id == strategy.agent_run_id, AgentRun.merchant_id == ctx.merchant_id
    ))).scalar_one_or_none()
    if hypothesis is None or run is None:
        raise ValueError("Strategy references invalid hypothesis or agent run")

    fact_ids = list(run.pinned_fact_ids or [])
    if not fact_ids:
        raise ValueError("Strategy agent run has no pinned facts")
    facts = (await session.execute(select(FactSnapshot).where(
        FactSnapshot.merchant_id == ctx.merchant_id, FactSnapshot.id.in_(fact_ids)
    ))).scalars().all()
    facts_by_metric = {fact.metric: fact for fact in facts}
    if len(facts_by_metric) != len(facts):
        raise ValueError("Strategy facts are not uniquely identifiable")

    assumptions = strategy.impact_assumptions or {}
    baseline_fact = facts_by_metric.get(strategy.primary_metric)
    baseline = Decimal(baseline_fact.value) if baseline_fact is not None else Decimal("0")
    relative_lift = _bounded_lift(assumptions)
    simulated_value = baseline * (Decimal("1") + relative_lift)
    outputs: dict[str, Any] = {
        "claim_type": ClaimType.simulation.value,
        "primary_metric": strategy.primary_metric,
        "baseline_value": str(baseline),
        "simulated_value": str(simulated_value),
        "relative_lift": str(relative_lift),
        "unit": baseline_fact.unit if baseline_fact is not None else "unknown",
        "fact_ids": sorted(str(fact_id) for fact_id in fact_ids),
        "method": "deterministic_bounded_lift_v1",
    }
    assumption_payload = {
        "strategy_id": str(strategy.id),
        "primary_metric": strategy.primary_metric,
        "impact_assumptions": assumptions,
        "fact_ids": sorted(str(fact_id) for fact_id in fact_ids),
    }
    serialized = json.dumps(assumption_payload, sort_keys=True, separators=(",", ":"), default=str)
    result = SimulationResult(
        merchant_id=ctx.merchant_id,
        agent_run_id=run.id,
        strategy_id=strategy.id,
        assumption_hash=hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        outputs=outputs,
        claim_type=ClaimType.simulation.value,
    )
    session.add(result)
    await session.flush()
    return result


def _bounded_lift(assumptions: dict[str, Any]) -> Decimal:
    raw = assumptions.get("relative_lift", assumptions.get("lift", "0.10"))
    try:
        lift = Decimal(str(raw))
    except Exception as exc:
        raise ValueError("Simulation lift must be numeric") from exc
    if lift < Decimal("-0.50") or lift > Decimal("0.50"):
        raise ValueError("Simulation lift must be between -0.50 and 0.50")
    return lift