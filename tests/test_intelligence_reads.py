from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.main import app
from app.models import (
    AgentRun,
    Diagnosis,
    Experiment,
    ExperimentResult,
    FactSnapshot,
    Hypothesis,
    Opportunity,
    Strategy,
)
from app.models.enums import AgentRunState, ExperimentStatus, HypothesisStatus, OpportunityStatus


async def make_chain(db_session, merchant_context, *, measured: bool = True):
    product_id = uuid4()
    opportunity = Opportunity(
        merchant_id=merchant_context.merchant_id,
        detector_id=f"read-test-{uuid4()}",
        entity_type="product",
        entity_id=product_id,
        score=Decimal("0.8"),
        evidence_fact_ids=[],
        status=OpportunityStatus.investigating.value,
    )
    db_session.add(opportunity)
    await db_session.flush()
    run = AgentRun(
        merchant_id=merchant_context.merchant_id,
        opportunity_id=opportunity.id,
        pinned_fact_ids=[],
        state=AgentRunState.completed.value,
    )
    db_session.add(run)
    await db_session.flush()
    fact = FactSnapshot(
        merchant_id=merchant_context.merchant_id,
        metric="product_views",
        value=Decimal("1000"),
        unit="count",
        window="all_time",
        method="test",
        source="bi.storefront",
        sample_size=1000,
        computed_at=datetime.now(timezone.utc),
    )
    db_session.add(fact)
    await db_session.flush()
    run.pinned_fact_ids = [fact.id]
    diagnosis = Diagnosis(
        merchant_id=merchant_context.merchant_id,
        opportunity_id=opportunity.id,
        agent_run_id=run.id,
        statement="Observed conversion gap",
        supporting_fact_ids=[fact.id],
        confidence=Decimal("0.8"),
        uncertainty="Causal mechanism unproven",
        model_version="test",
    )
    db_session.add(diagnosis)
    await db_session.flush()
    hypothesis = Hypothesis(
        merchant_id=merchant_context.merchant_id,
        agent_run_id=run.id,
        statement="Copy may improve conversion",
        supporting_fact_ids=[fact.id],
        contradicting_fact_ids=[],
        confidence=Decimal("0.7"),
        uncertainty="Unmeasured",
        status=HypothesisStatus.proposed.value,
    )
    db_session.add(hypothesis)
    await db_session.flush()
    strategy = Strategy(
        merchant_id=merchant_context.merchant_id,
        agent_run_id=run.id,
        hypothesis_id=hypothesis.id,
        action_type="synthetic_pdp_copy",
        rationale="Test copy",
        impact_assumptions={"relative_lift": "0.1"},
        expected_direction="increase",
        cost="low",
        risk="low",
        implementation_complexity="low",
        primary_metric="conversion_rate",
        guardrail_metrics=["revenue"],
        proposed_change={"control": "old", "variant": "new"},
    )
    db_session.add(strategy)
    await db_session.flush()
    experiment = Experiment(
        merchant_id=merchant_context.merchant_id,
        opportunity_id=opportunity.id,
        hypothesis_id=hypothesis.id,
        action_type=strategy.action_type,
        params={"strategy_id": str(strategy.id)},
        primary_metric=strategy.primary_metric,
        guardrail_metrics=strategy.guardrail_metrics,
        window="all_time",
        min_sample=10,
        status=ExperimentStatus.measured.value if measured else ExperimentStatus.running.value,
        control_description="old",
        variant_description="new",
    )
    db_session.add(experiment)
    await db_session.flush()
    if measured:
        db_session.add(ExperimentResult(
            merchant_id=merchant_context.merchant_id,
            experiment_id=experiment.id,
            claim_type="measured",
            primary_delta=Decimal("0.01"),
            guardrail_breaches={"primary": {"absolute_difference": "0.01"}},
            method="test",
        ))
        await db_session.flush()
    return opportunity, diagnosis, hypothesis, strategy, experiment


@pytest.fixture
async def api_client(db_session, merchant_context):
    async def override_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_merchant] = lambda: merchant_context
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_intelligence_reads_return_persisted_resources(db_session, merchant_context, api_client):
    opportunity, diagnosis, hypothesis, strategy, experiment = await make_chain(db_session, merchant_context)
    assert (await api_client.get(f"/v1/opportunities/{opportunity.id}/diagnosis")).json()["id"] == str(diagnosis.id)
    hypotheses = await api_client.get(f"/v1/opportunities/{opportunity.id}/hypotheses")
    assert hypotheses.status_code == 200
    assert hypotheses.json()["hypotheses"][0]["id"] == str(hypothesis.id)
    strategies = await api_client.get(f"/v1/opportunities/{opportunity.id}/strategies")
    assert strategies.status_code == 200
    assert strategies.json()["strategies"][0]["id"] == str(strategy.id)
    experiment_response = await api_client.get(f"/v1/experiments/{experiment.id}")
    assert experiment_response.status_code == 200
    assert experiment_response.json()["status"] == "measured"
    result = await api_client.get(f"/v1/experiments/{experiment.id}/result")
    assert result.status_code == 200
    assert result.json()["claim_type"] == "measured"


@pytest.mark.asyncio
async def test_unmeasured_experiment_result_is_not_available(db_session, merchant_context, api_client):
    *_, experiment = await make_chain(db_session, merchant_context, measured=False)
    response = await api_client.get(f"/v1/experiments/{experiment.id}/result")
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment result not available"


@pytest.mark.asyncio
async def test_missing_resources_return_404(api_client):
    missing = uuid4()
    assert (await api_client.get(f"/v1/opportunities/{missing}/diagnosis")).status_code == 404
    assert (await api_client.get(f"/v1/experiments/{missing}")).status_code == 404
    assert (await api_client.get(f"/v1/experiments/{missing}/result")).status_code == 404


@pytest.mark.asyncio
async def test_intelligence_reads_are_merchant_scoped(db_session, merchant_context, api_client):
    opportunity, _, _, _, experiment = await make_chain(db_session, merchant_context)
    other_context = merchant_context.__class__(uuid4(), "Other", "synthetic", False)
    app.dependency_overrides[get_current_merchant] = lambda: other_context
    assert (await api_client.get(f"/v1/opportunities/{opportunity.id}/diagnosis")).status_code == 404
    assert (await api_client.get(f"/v1/experiments/{experiment.id}")).status_code == 404