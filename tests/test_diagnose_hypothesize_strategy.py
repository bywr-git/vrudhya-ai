from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import (
    AgentRun,
    Diagnosis,
    FactSnapshot,
    Merchant,
    Hypothesis,
    Opportunity,
    Product,
    Strategy,
)
from app.models.enums import AgentRunState, OpportunityStatus
from app.services.diagnose import diagnose_opportunity
from app.services.hypothesize import hypothesize_diagnosis
from app.services.strategize import strategize_hypothesis


@pytest.fixture
async def merchant(db_session, merchant_context):
    return await db_session.get(Merchant, merchant_context.merchant_id)


@pytest.fixture
async def product(db_session, merchant):
    product = Product(
        merchant_id=merchant.id,
        sku="PHASE3-TEST",
        name="Phase 3 Test Gift",
        price_paise=1000,
        category="gifting",
        status="active",
    )
    db_session.add(product)
    await db_session.flush()
    return product


@pytest.mark.asyncio
async def test_full_diagnose_hypothesize_strategize_chain(
    db_session,
    merchant,
    product,
    merchant_context,
):
    views_fact = FactSnapshot(
        merchant_id=merchant.id,
        product_id=product.id,
        metric="product_views",
        value=Decimal("1500"),
        unit="count",
        window="all_time",
        method="event_aggregation",
        source="bi.storefront",
        sample_size=1500,
        computed_at=datetime.now(timezone.utc),
    )

    conversion_fact = FactSnapshot(
        merchant_id=merchant.id,
        product_id=product.id,
        metric="product_view_to_purchase_conversion_rate",
        value=Decimal("0.010000"),
        unit="ratio",
        window="all_time",
        method="event_aggregation",
        source="bi.storefront",
        sample_size=1500,
        computed_at=datetime.now(timezone.utc),
    )

    db_session.add_all([views_fact, conversion_fact])
    await db_session.flush()

    opportunity = Opportunity(
        merchant_id=merchant.id,
        detector_id="high_traffic_low_conversion",
        entity_type="product",
        entity_id=product.id,
        score=Decimal("0.8500"),
        evidence_fact_ids=[
            views_fact.id,
            conversion_fact.id,
        ],
        status=OpportunityStatus.open.value,
    )

    db_session.add(opportunity)
    await db_session.flush()

    diagnosis = await diagnose_opportunity(
        db_session,
        merchant_context,
        opportunity.id,
    )

    assert diagnosis.merchant_id == merchant.id
    assert diagnosis.opportunity_id == opportunity.id
    assert diagnosis.supporting_fact_ids == [
        views_fact.id,
        conversion_fact.id,
    ]
    assert diagnosis.confidence == pytest.approx(0.90)
    assert diagnosis.model_version == "deterministic_v1"

    run = (
        await db_session.execute(
            select(AgentRun).where(
                AgentRun.id == diagnosis.agent_run_id
            )
        )
    ).scalar_one()

    assert run.merchant_id == merchant.id
    assert run.pinned_fact_ids == [
        views_fact.id,
        conversion_fact.id,
    ]
    assert run.state == AgentRunState.completed.value

    hypothesis = await hypothesize_diagnosis(
        db_session,
        merchant_context,
        diagnosis.id,
    )

    assert hypothesis.merchant_id == merchant.id
    assert hypothesis.agent_run_id == diagnosis.agent_run_id
    assert hypothesis.supporting_fact_ids == diagnosis.supporting_fact_ids
    assert hypothesis.contradicting_fact_ids == []

    strategy = await strategize_hypothesis(
        db_session,
        merchant_context,
        hypothesis.id,
    )

    assert strategy.merchant_id == merchant.id
    assert strategy.agent_run_id == diagnosis.agent_run_id
    assert strategy.hypothesis_id == hypothesis.id

    assert strategy.action_type == "synthetic_pdp_copy"
    assert strategy.primary_metric == (
        "product_view_to_purchase_conversion_rate"
    )

    assert "add_to_cart_rate" in strategy.guardrail_metrics
    assert "checkout_rate" in strategy.guardrail_metrics
    assert "revenue" in strategy.guardrail_metrics

    assert strategy.proposed_change["surface"] == "product_detail_page"
    assert strategy.proposed_change["change_type"] == "copy"


@pytest.mark.asyncio
async def test_diagnosis_rejects_invalid_evidence(
    db_session,
    merchant,
    product,
    merchant_context,
):
    missing_fact_id = uuid4()

    opportunity = Opportunity(
        merchant_id=merchant.id,
        detector_id="test_detector",
        entity_type="product",
        entity_id=product.id,
        score=Decimal("0.5000"),
        evidence_fact_ids=[missing_fact_id],
        status=OpportunityStatus.open.value,
    )

    db_session.add(opportunity)
    await db_session.flush()

    with pytest.raises(
        ValueError,
        match="invalid evidence fact IDs",
    ):
        await diagnose_opportunity(
            db_session,
            merchant_context,
            opportunity.id,
        )


@pytest.mark.asyncio
async def test_diagnosis_enforces_merchant_isolation(
    db_session,
    merchant,
    product,
    merchant_context,
):
    other_merchant = Merchant(name="Other Merchant", data_mode="synthetic")
    db_session.add(other_merchant)
    await db_session.flush()

    fact = FactSnapshot(
        merchant_id=other_merchant.id,
        product_id=product.id,
        metric="product_views",
        value=Decimal("1000"),
        unit="count",
        window="all_time",
        method="event_aggregation",
        source="bi.storefront",
        sample_size=1000,
        computed_at=datetime.now(timezone.utc),
    )

    db_session.add(fact)
    await db_session.flush()

    opportunity = Opportunity(
        merchant_id=merchant.id,
        detector_id="test_detector",
        entity_type="product",
        entity_id=product.id,
        score=Decimal("0.5000"),
        evidence_fact_ids=[fact.id],
        status=OpportunityStatus.open.value,
    )

    db_session.add(opportunity)
    await db_session.flush()

    with pytest.raises(
        ValueError,
        match="invalid evidence fact IDs",
    ):
        await diagnose_opportunity(
            db_session,
            merchant_context,
            opportunity.id,
        )