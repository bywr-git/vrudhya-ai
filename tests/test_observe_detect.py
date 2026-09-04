"""Observe -> Detect phase tests."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, FactSnapshot, Opportunity, Product, Merchant
from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.main import app
from app.models.enums import EventType
from app.schemas.events import StorefrontEventIn
from app.services.bi import build_snapshots
from app.services.context import MerchantContext
from app.services.detect import DETECTOR_ID, detect_opportunities
from app.services.ingest import ingest_events


async def make_product(session: AsyncSession, context: MerchantContext, sku: str = "SKU") -> Product:
    product = Product(merchant_id=context.merchant_id, sku=sku, name="Gift", price_paise=1000,
                      category="gifting", status="active")
    session.add(product)
    await session.flush()
    return product


def event(event_type: EventType, product_id=None, revenue: int = 0) -> StorefrontEventIn:
    return StorefrontEventIn(event_id=uuid4(), event_type=event_type, occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                             product_id=product_id, revenue_paise=revenue)


@pytest.mark.asyncio
async def test_event_validation_rejects_unknown_fields():
    with pytest.raises(ValueError):
        StorefrontEventIn(event_id=uuid4(), event_type=EventType.session,
                          occurred_at=datetime.now(timezone.utc), unknown="bad")


@pytest.mark.asyncio
async def test_ingestion_is_idempotent_and_ignores_client_merchant_id(db_session, merchant_context):
    product = await make_product(db_session, merchant_context)
    payload = event(EventType.product_view, product.id)
    accepted, duplicates = await ingest_events(db_session, merchant_context, [payload, payload])
    assert (accepted, duplicates) == (1, 1)
    assert len((await db_session.execute(select(Event))).scalars().all()) == 1
    assert "merchant_id" not in payload.model_dump()


@pytest.mark.asyncio
async def test_bi_rates_revenue_and_provenance(db_session, merchant_context):
    product = await make_product(db_session, merchant_context)
    payloads = [event(EventType.product_view, product.id) for _ in range(500)]
    payloads.extend(event(EventType.add_to_cart, product.id) for _ in range(100))
    payloads.extend(event(EventType.checkout_started, product.id) for _ in range(50))
    payloads.extend(event(EventType.purchase, product.id, 1000) for _ in range(5))
    await ingest_events(db_session, merchant_context, payloads)
    snapshots = await build_snapshots(db_session, merchant_context)
    by_metric = {snapshot.metric: snapshot for snapshot in snapshots if snapshot.product_id == product.id}
    assert by_metric["product_views"].value == 500
    assert by_metric["add_to_cart_rate"].value == Decimal("0.2")
    assert by_metric["checkout_rate"].value == Decimal("0.1")
    assert by_metric["product_view_to_purchase_conversion_rate"].value == Decimal("0.01")
    assert by_metric["revenue"].value == 5000
    assert by_metric["revenue"].source == "bi.storefront"
    assert by_metric["revenue"].sample_size == 5


@pytest.mark.asyncio
async def test_fact_snapshots_are_immutable(db_session, merchant_context):
    snapshot = FactSnapshot(merchant_id=merchant_context.merchant_id, metric="sessions", value=1,
                            unit="count", window="all_time", method="test", source="bi.storefront",
                            sample_size=1, computed_at=datetime.now(timezone.utc))
    db_session.add(snapshot)
    await db_session.commit()
    snapshot.value = 2
    with pytest.raises(Exception, match="fact_snapshots is immutable"):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_detector_threshold_score_evidence_and_rerun_idempotency(db_session, merchant_context):
    product = await make_product(db_session, merchant_context)
    await ingest_events(db_session, merchant_context,
                         [event(EventType.product_view, product.id) for _ in range(500)] +
                         [event(EventType.purchase, product.id, 1000) for _ in range(5)])
    await build_snapshots(db_session, merchant_context)
    first = await detect_opportunities(db_session, merchant_context)
    second = await detect_opportunities(db_session, merchant_context)
    assert len(first) == len(second) == 1
    assert first[0].score == Decimal("0.5")
    assert len(first[0].evidence_fact_ids) == 2
    opportunities = (await db_session.execute(select(Opportunity).where(
        Opportunity.merchant_id == merchant_context.merchant_id, Opportunity.detector_id == DETECTOR_ID
    ))).scalars().all()
    assert len(opportunities) == 1


@pytest.mark.asyncio
async def test_detector_excludes_insufficient_and_healthy_products(db_session, merchant_context):
    low_sample = await make_product(db_session, merchant_context, "LOW")
    healthy = await make_product(db_session, merchant_context, "HEALTHY")
    await ingest_events(db_session, merchant_context,
                         [event(EventType.product_view, low_sample.id) for _ in range(499)] +
                         [event(EventType.product_view, healthy.id) for _ in range(500)] +
                         [event(EventType.purchase, healthy.id, 1000) for _ in range(10)])
    await build_snapshots(db_session, merchant_context)
    assert await detect_opportunities(db_session, merchant_context) == []


@pytest.mark.asyncio
async def test_two_merchants_are_isolated(db_session, merchant_context):
    other = Merchant(name="Other Merchant", data_mode="synthetic")
    db_session.add(other)
    await db_session.flush()
    other_context = MerchantContext(merchant_id=other.id, name=other.name, data_mode=other.data_mode,
                                    autonomy_kill_switch=False)
    first_product = await make_product(db_session, merchant_context, "FIRST")
    other_product = await make_product(db_session, other_context, "OTHER")
    await ingest_events(db_session, merchant_context,
                         [event(EventType.product_view, first_product.id) for _ in range(500)])
    await ingest_events(db_session, other_context,
                         [event(EventType.product_view, other_product.id) for _ in range(500)])
    await build_snapshots(db_session, merchant_context)
    await build_snapshots(db_session, other_context)
    first_opportunities = await detect_opportunities(db_session, merchant_context)
    assert all(opportunity.merchant_id == merchant_context.merchant_id for opportunity in first_opportunities)
    assert all(opportunity.entity_id == first_product.id for opportunity in first_opportunities)


@pytest.mark.asyncio
async def test_radar_api_returns_persisted_evidence_without_llm(db_session, merchant_context):
    product = await make_product(db_session, merchant_context, "RADAR")
    await ingest_events(db_session, merchant_context,
                         [event(EventType.product_view, product.id) for _ in range(500)] +
                         [event(EventType.purchase, product.id, 1000) for _ in range(5)])
    await build_snapshots(db_session, merchant_context)
    await detect_opportunities(db_session, merchant_context)
    await db_session.commit()

    async def override_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_merchant] = lambda: merchant_context
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/v1/opportunities")
            assert response.status_code == 200
            opportunity = response.json()[0]
            detail = await client.get(f"/v1/opportunities/{opportunity['id']}")
            assert detail.status_code == 200
            body = detail.json()
            assert body["evidence"]
            assert {fact["claim_type"] for fact in body["evidence"]} == {"observation"}
    finally:
        app.dependency_overrides.clear()