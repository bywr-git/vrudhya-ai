from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import Experiment, ExperimentAssignment, ExperimentObservation, ExperimentResult, Merchant
from app.models.enums import ActionType, ExperimentStatus
from app.services.context import MerchantContext
from app.services.experiment_approval import approve_or_reject_experiment
from app.services.experiment_runner import run_experiment
from app.services.measurement import measure_experiment


def context(merchant: Merchant) -> MerchantContext:
    return MerchantContext(merchant_id=merchant.id, name=merchant.name, data_mode=merchant.data_mode,
                           autonomy_kill_switch=merchant.autonomy_kill_switch)


async def experiment_for(db_session, merchant: Merchant, status=ExperimentStatus.awaiting_approval.value,
                         action_type=ActionType.synthetic_pdp_copy.value) -> Experiment:
    experiment = Experiment(
        merchant_id=merchant.id, action_type=action_type, params={"variant": "new_copy"},
        primary_metric="conversion_rate", guardrail_metrics=["revenue"], window="all_time", min_sample=20,
        status=status, control_description="old", variant_description="new",
    )
    db_session.add(experiment)
    await db_session.flush()
    return experiment


@pytest.mark.asyncio
async def test_approval_and_rejection_transitions(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    approved = await experiment_for(db_session, merchant)
    await approve_or_reject_experiment(db_session, merchant_context, approved.id, True)
    assert approved.status == ExperimentStatus.approved.value
    assert approved.approval_id is not None
    rejected = await experiment_for(db_session, merchant)
    await approve_or_reject_experiment(db_session, merchant_context, rejected.id, False)
    assert rejected.status == ExperimentStatus.rejected_by_merchant.value


@pytest.mark.asyncio
async def test_cannot_run_unapproved_or_rejected_experiment(db_session, merchant_context):
    draft = await experiment_for(db_session, await db_session.get(Merchant, merchant_context.merchant_id), ExperimentStatus.draft.value)
    with pytest.raises(ValueError, match="Only approved"):
        await run_experiment(db_session, merchant_context, draft.id)
    rejected = await experiment_for(db_session, await db_session.get(Merchant, merchant_context.merchant_id), ExperimentStatus.rejected_by_merchant.value)
    with pytest.raises(ValueError, match="Only approved"):
        await run_experiment(db_session, merchant_context, rejected.id)


@pytest.mark.asyncio
async def test_approved_run_assignments_and_observations_are_reproducible(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment = await experiment_for(db_session, merchant, ExperimentStatus.approved.value)
    first, assignment_count, observation_count = await run_experiment(db_session, merchant_context, experiment.id)
    assignments = (await db_session.execute(select(ExperimentAssignment).where(ExperimentAssignment.experiment_id == experiment.id).order_by(ExperimentAssignment.visitor_key))).scalars().all()
    observations = (await db_session.execute(select(ExperimentObservation).where(ExperimentObservation.experiment_id == experiment.id).order_by(ExperimentObservation.variant, ExperimentObservation.metric))).scalars().all()
    _, second_assignment_count, second_observation_count = await run_experiment(db_session, merchant_context, experiment.id)
    repeat_assignments = (await db_session.execute(select(ExperimentAssignment).where(ExperimentAssignment.experiment_id == experiment.id).order_by(ExperimentAssignment.visitor_key))).scalars().all()
    repeat_observations = (await db_session.execute(select(ExperimentObservation).where(ExperimentObservation.experiment_id == experiment.id).order_by(ExperimentObservation.variant, ExperimentObservation.metric))).scalars().all()
    assert first.status == ExperimentStatus.running.value
    assert (assignment_count, observation_count) == (second_assignment_count, second_observation_count)
    assert [(row.visitor_key, row.variant) for row in assignments] == [(row.visitor_key, row.variant) for row in repeat_assignments]
    assert [(row.variant, row.metric, row.value) for row in observations] == [(row.variant, row.metric, row.value) for row in repeat_observations]


@pytest.mark.asyncio
async def test_measurement_calculates_differences_and_measured_result(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment = await experiment_for(db_session, merchant, ExperimentStatus.running.value)
    for variant, views, purchases, revenue in [("control", 100, 10, 1000), ("variant", 100, 15, 1500)]:
        for metric, value in [("views", views), ("purchases", purchases), ("revenue", revenue)]:
            db_session.add(ExperimentObservation(merchant_id=merchant.id, experiment_id=experiment.id,
                observed_on=__import__("datetime").date.today(), variant=variant, source="synthetic.storefront",
                metric=metric, value=Decimal(value), unit="count", sample_size=views, claim_type="observation"))
    await db_session.flush()
    result = await measure_experiment(db_session, merchant_context, experiment.id)
    primary = result.guardrail_breaches["primary"]
    assert primary["control_metric"] == "0.1"
    assert primary["variant_metric"] == "0.15"
    assert primary["absolute_difference"] == "0.05"
    assert primary["relative_difference"] == "0.5"
    assert result.claim_type == "measured"
    assert experiment.status == ExperimentStatus.measured.value
    assert (await db_session.execute(select(ExperimentResult))).scalar_one().id == result.id


@pytest.mark.asyncio
async def test_zero_denominator_and_isolation(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment = await experiment_for(db_session, merchant, ExperimentStatus.running.value)
    db_session.add(ExperimentObservation(merchant_id=merchant.id, experiment_id=experiment.id,
        observed_on=__import__("datetime").date.today(), variant="control", source="synthetic.storefront",
        metric="views", value=0, unit="count", sample_size=0, claim_type="observation"))
    db_session.add(ExperimentObservation(merchant_id=merchant.id, experiment_id=experiment.id,
        observed_on=__import__("datetime").date.today(), variant="variant", source="synthetic.storefront",
        metric="views", value=0, unit="count", sample_size=0, claim_type="observation"))
    await db_session.flush()
    other = MerchantContext(merchant_id=uuid4(), name="Other", data_mode="synthetic", autonomy_kill_switch=False)
    with pytest.raises(ValueError, match="Experiment not found"):
        await measure_experiment(db_session, other, experiment.id)
    result = await measure_experiment(db_session, merchant_context, experiment.id)
    assert result.guardrail_breaches["primary"]["relative_difference"] is None


@pytest.mark.asyncio
async def test_razorpay_actions_cannot_execute(db_session, merchant_context):
    merchant = await db_session.get(Merchant, merchant_context.merchant_id)
    experiment = await experiment_for(db_session, merchant, ExperimentStatus.approved.value,
                                      ActionType.razorpay_payment_link.value)
    with pytest.raises(ValueError, match="not executable in V1"):
        await run_experiment(db_session, merchant_context, experiment.id)