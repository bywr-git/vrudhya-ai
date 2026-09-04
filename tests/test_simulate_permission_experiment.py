from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    AgentRun,
    FactSnapshot,
    Hypothesis,
    Opportunity,
    PermissionPolicy,
    SimulationResult,
    Strategy,
)
from app.models.enums import ActionType, AgentRunState, ExperimentStatus, OpportunityStatus
from app.services.context import MerchantContext
from app.services.experiment_draft import create_experiment_draft
from app.services.permissions import check_strategy_permission
from app.services.simulate import simulate_strategy


async def make_strategy(db_session, merchant_context, action_type=ActionType.synthetic_pdp_copy.value):
    product_id = None
    opportunity = Opportunity(
        merchant_id=merchant_context.merchant_id, detector_id="phase4", entity_type="product",
        entity_id=merchant_context.merchant_id, score=Decimal("0.8"), evidence_fact_ids=[],
        status=OpportunityStatus.open.value,
    )
    db_session.add(opportunity)
    await db_session.flush()
    run = AgentRun(merchant_id=merchant_context.merchant_id, opportunity_id=opportunity.id,
                   pinned_fact_ids=[], state=AgentRunState.completed.value)
    db_session.add(run)
    await db_session.flush()
    fact = FactSnapshot(merchant_id=merchant_context.merchant_id, metric="product_view_to_purchase_conversion_rate",
                        value=Decimal("0.01"), unit="ratio", window="all_time", method="test",
                        source="bi.storefront", sample_size=1500, computed_at=datetime.now(timezone.utc))
    db_session.add(fact)
    await db_session.flush()
    run.pinned_fact_ids = [fact.id]
    hypothesis = Hypothesis(merchant_id=merchant_context.merchant_id, agent_run_id=run.id,
                            statement="A copy change improves conversion", supporting_fact_ids=[fact.id],
                            contradicting_fact_ids=[], confidence=Decimal("0.8"), uncertainty="unproven")
    db_session.add(hypothesis)
    await db_session.flush()
    strategy = Strategy(merchant_id=merchant_context.merchant_id, agent_run_id=run.id, hypothesis_id=hypothesis.id,
                        action_type=action_type, rationale="Test the observed gap", impact_assumptions={"relative_lift": "0.10"},
                        expected_direction="increase", cost="low", risk="low", implementation_complexity="low",
                        primary_metric="product_view_to_purchase_conversion_rate", guardrail_metrics=["revenue"],
                        proposed_change={"control": "old", "variant": "new", "surface": "product_detail_page"})
    db_session.add(strategy)
    await db_session.flush()
    return strategy


@pytest.mark.asyncio
async def test_deterministic_simulation_stores_simulation_claim(db_session, merchant_context):
    strategy = await make_strategy(db_session, merchant_context)
    first = await simulate_strategy(db_session, merchant_context, strategy.id)
    second = await simulate_strategy(db_session, merchant_context, strategy.id)
    assert first.assumption_hash == second.assumption_hash
    assert first.outputs == second.outputs
    assert first.claim_type == "simulation"
    assert (await db_session.execute(select(SimulationResult))).scalars().all()


@pytest.mark.asyncio
async def test_simulation_merchant_isolation(db_session, merchant_context):
    strategy = await make_strategy(db_session, merchant_context)
    other = MerchantContext(merchant_id=__import__("uuid").uuid4(), name="Other", data_mode="synthetic", autonomy_kill_switch=False)
    with pytest.raises(ValueError, match="Strategy not found"):
        await simulate_strategy(db_session, other, strategy.id)


@pytest.mark.asyncio
async def test_permission_outcomes(db_session, merchant_context):
    strategy = await make_strategy(db_session, merchant_context)
    db_session.add(PermissionPolicy(merchant_id=merchant_context.merchant_id,
                                    policy={"autonomous_action_types": [ActionType.synthetic_pdp_copy.value]}))
    await db_session.flush()
    assert (await check_strategy_permission(db_session, merchant_context, strategy.id)).outcome == "allowed"

    strategy.action_type = ActionType.razorpay_payment_link.value
    assert (await check_strategy_permission(db_session, merchant_context, strategy.id)).outcome == "approval_required"
    strategy.action_type = "unknown_action"
    assert (await check_strategy_permission(db_session, merchant_context, strategy.id)).outcome == "denied"


@pytest.mark.asyncio
async def test_experiment_draft_copies_strategy_and_awaits_approval(db_session, merchant_context):
    strategy = await make_strategy(db_session, merchant_context)
    simulation, permission, experiment = await create_experiment_draft(db_session, merchant_context, strategy.id)
    assert permission.outcome == "approval_required"
    assert experiment.status == ExperimentStatus.awaiting_approval.value
    assert experiment.action_type == strategy.action_type
    assert experiment.primary_metric == strategy.primary_metric
    assert experiment.guardrail_metrics == strategy.guardrail_metrics
    assert experiment.params["proposed_change"] == strategy.proposed_change
    assert experiment.params["simulation_id"] == str(simulation.id)