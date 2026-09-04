"""Create experiment drafts after simulation and permission evaluation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRun, Experiment, Strategy
from app.models.enums import ExperimentStatus, PermissionOutcome
from app.services.context import MerchantContext
from app.services.permissions import PermissionDecision, check_strategy_permission
from app.services.simulate import simulate_strategy


async def create_experiment_draft(
    session: AsyncSession,
    ctx: MerchantContext,
    strategy_id: UUID,
):
    simulation = await simulate_strategy(session, ctx, strategy_id)
    permission = await check_strategy_permission(session, ctx, strategy_id)
    if permission.outcome == PermissionOutcome.denied.value:
        raise ValueError(permission.reason)

    strategy = (await session.execute(select(Strategy).where(
        Strategy.id == strategy_id, Strategy.merchant_id == ctx.merchant_id
    ))).scalar_one()
    run = (await session.execute(select(AgentRun).where(
        AgentRun.id == strategy.agent_run_id, AgentRun.merchant_id == ctx.merchant_id
    ))).scalar_one()
    experiment = Experiment(
        merchant_id=ctx.merchant_id,
        opportunity_id=run.opportunity_id,
        hypothesis_id=strategy.hypothesis_id,
        action_type=strategy.action_type,
        params={"proposed_change": strategy.proposed_change, "simulation_id": str(simulation.id)},
        primary_metric=strategy.primary_metric,
        guardrail_metrics=list(strategy.guardrail_metrics),
        window="all_time",
        min_sample=500,
        status=(ExperimentStatus.awaiting_approval.value
                if permission.outcome == PermissionOutcome.approval_required.value
                else ExperimentStatus.draft.value),
        control_description=str(strategy.proposed_change.get("control", "existing experience")),
        variant_description=str(strategy.proposed_change.get("variant", "proposed experience")),
    )
    session.add(experiment)
    await session.flush()
    return simulation, permission, experiment