import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import Experiment, ExperimentObservation, ExperimentResult, GrowthDna, Merchant, Opportunity
from app.models.enums import OpportunityStatus
from app.services.agent_loop import continue_agent_loop
from app.services.context import MerchantContext


async def measured_experiment(db_session, merchant, delta):
    opportunity = Opportunity(merchant_id=merchant.id, detector_id=f"agent-loop-source-{uuid4()}", entity_type="product",
                              entity_id=merchant.id, score=Decimal("0.7"), evidence_fact_ids=[], status=OpportunityStatus.open.value)
    db_session.add(opportunity)
    await db_session.flush()
    experiment = Experiment(merchant_id=merchant.id, opportunity_id=opportunity.id, action_type="synthetic_pdp_copy",
                            params={}, primary_metric="conversion_rate", guardrail_metrics=[], window="all_time", min_sample=10,
                            status="measured", control_description="old", variant_description="new")
    db_session.add(experiment)
    await db_session.flush()
    observation = ExperimentObservation(merchant_id=merchant.id, experiment_id=experiment.id,
        observed_on=datetime.now(timezone.utc).date(), variant="control", source="synthetic.storefront",
        metric="views", value=100, unit="count", sample_size=100, claim_type="observation")
    db_session.add(observation)
    await db_session.flush()
    db_session.add(ExperimentResult(merchant_id=merchant.id, experiment_id=experiment.id, claim_type="measured",
        primary_delta=Decimal(delta), guardrail_breaches={"primary": {"metric": "conversion_rate", "control_metric": "0.1",
        "variant_metric": "0.15", "absolute_difference": delta, "relative_difference": "0.5"}, "guardrails": {}},
        method="test", notes=json.dumps({"observation_ids": [str(observation.id)]})))
    await db_session.flush()
    return experiment


@pytest.mark.asyncio
async def test_supported_loop_updates_dna_and_creates_next_opportunity(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment = await measured_experiment(db_session, merchant, "0.05")
    decision, dna, next_opportunity = await continue_agent_loop(db_session, merchant_context, experiment.id)
    assert decision.outcome == "supported"
    assert dna.evidence_experiment_id == experiment.id
    assert next_opportunity.merchant_id == merchant.id
    assert next_opportunity.status == "open"
    assert next_opportunity.detector_id.startswith("phase6_supported_")
    again = await continue_agent_loop(db_session, merchant_context, experiment.id)
    assert again[2].id == next_opportunity.id


@pytest.mark.asyncio
async def test_rejected_creates_alternative_and_inconclusive_stops(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    rejected = await measured_experiment(db_session, merchant, "-0.05")
    decision, _, opportunity = await continue_agent_loop(db_session, merchant_context, rejected.id)
    assert decision.outcome == "rejected"
    assert opportunity is not None
    inconclusive = await measured_experiment(db_session, merchant, "0")
    result = await continue_agent_loop(db_session, merchant_context, inconclusive.id)
    assert result[0].outcome == "inconclusive"
    assert result[2] is None


@pytest.mark.asyncio
async def test_loop_never_approves_or_executes_and_isolates(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment = await measured_experiment(db_session, merchant, "0.05")
    other = MerchantContext(merchant_id=uuid4(), name="Other", data_mode="synthetic", autonomy_kill_switch=False)
    with pytest.raises(ValueError, match="Experiment not found"):
        await continue_agent_loop(db_session, other, experiment.id)
    assert experiment.status == "measured"
    assert (await db_session.execute(select(GrowthDna).where(GrowthDna.merchant_id == merchant.id))).scalars().all() == []