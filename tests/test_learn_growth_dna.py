import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models import Experiment, ExperimentObservation, ExperimentResult, GrowthDna, Merchant, Opportunity
from app.models.enums import ExperimentStatus, OpportunityStatus
from app.services.context import MerchantContext
from app.services.learn import learn_from_experiment
from app.services.growth_dna import update_growth_dna


async def make_measured(db_session, merchant, delta="0.05", relative="0.5", claim_type="measured", status="measured"):
    opportunity = Opportunity(merchant_id=merchant.id, detector_id=f"learn-source-{uuid4()}", entity_type="product",
                              entity_id=merchant.id, score=Decimal("0.5"), evidence_fact_ids=[], status=OpportunityStatus.open.value)
    db_session.add(opportunity)
    await db_session.flush()
    experiment = Experiment(merchant_id=merchant.id, opportunity_id=opportunity.id, action_type="synthetic_pdp_copy",
                            params={}, primary_metric="conversion_rate", guardrail_metrics=["revenue"], window="all_time",
                            min_sample=10, status=status, control_description="old", variant_description="new")
    db_session.add(experiment)
    await db_session.flush()
    observation = ExperimentObservation(merchant_id=merchant.id, experiment_id=experiment.id,
        observed_on=datetime.now(timezone.utc).date(), variant="control", source="synthetic.storefront",
        metric="views", value=100, unit="count", sample_size=100, claim_type="observation")
    db_session.add(observation)
    await db_session.flush()
    result = ExperimentResult(merchant_id=merchant.id, experiment_id=experiment.id, claim_type=claim_type,
        primary_delta=Decimal(delta), guardrail_breaches={
            "primary": {"metric": "conversion_rate", "control_metric": "0.1", "variant_metric": "0.15",
                         "absolute_difference": delta, "relative_difference": relative},
            "guardrails": {"revenue": {"metric": "revenue", "control_metric": "100", "variant_metric": "100",
                                         "absolute_difference": "0", "relative_difference": "0"}},
        }, method="test", notes=json.dumps({"observation_ids": [str(observation.id)]}))
    db_session.add(result)
    await db_session.flush()
    return experiment, result


def ctx(merchant):
    return MerchantContext(merchant_id=merchant.id, name=merchant.name, data_mode=merchant.data_mode, autonomy_kill_switch=False)


@pytest.mark.asyncio
async def test_supported_rejected_and_inconclusive_learning(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    supported, _ = await make_measured(db_session, merchant)
    rejected, _ = await make_measured(db_session, merchant, delta="-0.05", relative="-0.5")
    inconclusive, _ = await make_measured(db_session, merchant, delta="0", relative=None)
    assert (await learn_from_experiment(db_session, ctx(merchant), supported.id)).outcome == "supported"
    assert (await learn_from_experiment(db_session, ctx(merchant), rejected.id)).outcome == "rejected"
    assert (await learn_from_experiment(db_session, ctx(merchant), inconclusive.id)).outcome == "inconclusive"


@pytest.mark.asyncio
async def test_only_measured_results_can_create_idempotent_dna(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment, _ = await make_measured(db_session, merchant)
    decision = await learn_from_experiment(db_session, ctx(merchant), experiment.id)
    first = await update_growth_dna(db_session, ctx(merchant), decision)
    second = await update_growth_dna(db_session, ctx(merchant), decision)
    assert first.id == second.id
    assert (await db_session.execute(__import__("sqlalchemy").select(GrowthDna))).scalars().all() == [first]
    simulation, _ = await make_measured(db_session, merchant, claim_type="simulation")
    with pytest.raises(ValueError, match="not measured"):
        await learn_from_experiment(db_session, ctx(merchant), simulation.id)
    unmeasured, _ = await make_measured(db_session, merchant, status=ExperimentStatus.running.value)
    with pytest.raises(ValueError, match="Only measured"):
        await learn_from_experiment(db_session, ctx(merchant), unmeasured.id)


@pytest.mark.asyncio
async def test_learning_is_merchant_scoped(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment, _ = await make_measured(db_session, merchant)
    other = MerchantContext(merchant_id=uuid4(), name="Other", data_mode="synthetic", autonomy_kill_switch=False)
    with pytest.raises(ValueError, match="Experiment not found"):
        await learn_from_experiment(db_session, other, experiment.id)