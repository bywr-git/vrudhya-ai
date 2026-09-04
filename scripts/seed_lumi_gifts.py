"""Idempotently seed the synthetic Lumi Gifts storefront."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models import Merchant, Product
from app.models.enums import EventType
from app.schemas.events import StorefrontEventIn
from app.services.bi import build_snapshots
from app.services.context import MerchantContext
from app.services.detect import detect_opportunities
from app.services.ingest import ingest_events

MERCHANT_ID = uuid5(NAMESPACE_URL, "vrudhya/lumi-gifts")
PRODUCT_ID = uuid5(NAMESPACE_URL, "vrudhya/lumi-gifts/traffic-gift")
HEALTHY_PRODUCT_ID = uuid5(NAMESPACE_URL, "vrudhya/lumi-gifts/healthy-gift")


def stable_id(label: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"vrudhya/lumi-gifts/{label}")


def make_events() -> list[StorefrontEventIn]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    events: list[StorefrontEventIn] = []
    for index in range(600):
        visitor = f"visitor-{index:04d}"
        timestamp = start + timedelta(minutes=index)
        events.extend([
            StorefrontEventIn(event_id=stable_id(f"session-{index}"), event_type=EventType.session,
                              occurred_at=timestamp, visitor_key=visitor),
            StorefrontEventIn(event_id=stable_id(f"view-{index}"), event_type=EventType.product_view,
                              occurred_at=timestamp, product_id=PRODUCT_ID, visitor_key=visitor),
        ])
    for index in range(120):
        events.append(StorefrontEventIn(event_id=stable_id(f"atc-{index}"), event_type=EventType.add_to_cart,
                                        occurred_at=start + timedelta(minutes=index), product_id=PRODUCT_ID,
                                        visitor_key=f"visitor-{index:04d}"))
    for index in range(40):
        events.append(StorefrontEventIn(event_id=stable_id(f"checkout-{index}"), event_type=EventType.checkout_started,
                                        occurred_at=start + timedelta(minutes=index), product_id=PRODUCT_ID,
                                        visitor_key=f"visitor-{index:04d}"))
    for index in range(8):
        events.append(StorefrontEventIn(event_id=stable_id(f"purchase-{index}"), event_type=EventType.purchase,
                                        occurred_at=start + timedelta(minutes=index), product_id=PRODUCT_ID,
                                        visitor_key=f"visitor-{index:04d}", revenue_paise=10000))
    for index in range(100):
        visitor = f"healthy-{index:04d}"
        timestamp = start + timedelta(days=1, minutes=index)
        events.append(StorefrontEventIn(event_id=stable_id(f"healthy-view-{index}"), event_type=EventType.product_view,
                                        occurred_at=timestamp, product_id=HEALTHY_PRODUCT_ID, visitor_key=visitor))
    for index in range(5):
        events.append(StorefrontEventIn(event_id=stable_id(f"healthy-purchase-{index}"), event_type=EventType.purchase,
                                        occurred_at=start + timedelta(days=1, minutes=index), product_id=HEALTHY_PRODUCT_ID,
                                        visitor_key=f"healthy-{index:04d}", revenue_paise=12000))
    return events


async def seed() -> None:
    async with get_session_factory()() as session:
        merchant = await session.get(Merchant, MERCHANT_ID)
        if merchant is None:
            merchant = Merchant(id=MERCHANT_ID, name="Lumi Gifts", data_mode="synthetic")
            session.add(merchant)
        for product_id, sku, name in [
            (PRODUCT_ID, "LUMI-TRAFFIC-GIFT", "Lumi Surprise Gift"),
            (HEALTHY_PRODUCT_ID, "LUMI-HEALTHY-GIFT", "Lumi Popular Gift"),
        ]:
            product = await session.get(Product, product_id)
            if product is None:
                session.add(Product(id=product_id, merchant_id=MERCHANT_ID, sku=sku, name=name,
                                    price_paise=10000, category="gifting", status="active"))
        await session.flush()
        ctx = MerchantContext(merchant_id=MERCHANT_ID, name=merchant.name, data_mode=merchant.data_mode,
                              autonomy_kill_switch=merchant.autonomy_kill_switch)
        accepted, duplicates = await ingest_events(session, ctx, make_events())
        snapshots = await build_snapshots(session, ctx)
        opportunities = await detect_opportunities(session, ctx)
        await session.commit()
        print(f"seeded merchant={MERCHANT_ID} accepted={accepted} duplicates={duplicates} "
              f"snapshots={len(snapshots)} opportunities={len(opportunities)}")


if __name__ == "__main__":
    asyncio.run(seed())