"""Deterministic BI aggregation and immutable observation snapshots."""

from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, EventDaily, FactSnapshot
from app.models.enums import EventType
from app.services.context import MerchantContext


def _rate(numerator: int, denominator: int) -> Decimal:
    return Decimal(numerator) / Decimal(denominator) if denominator else Decimal("0")


async def build_snapshots(session: AsyncSession, ctx: MerchantContext) -> list[FactSnapshot]:
    events = (await session.execute(
        select(Event).where(Event.merchant_id == ctx.merchant_id).order_by(Event.occurred_at, Event.id)
    )).scalars().all()
    grouped: dict[tuple[UUID | None, date, str, str], dict[str, int]] = defaultdict(
        lambda: {"sessions": 0, "pdp_views": 0, "atc": 0, "checkouts": 0, "orders": 0, "revenue_paise": 0}
    )
    for event in events:
        metadata = event.event_metadata or {}
        key = (
            event.product_id,
            event.occurred_at.date(),
            str(metadata.get("channel", "synthetic")),
            str(metadata.get("variant", "unassigned")),
        )
        counters = grouped[key]
        if event.event_type == EventType.session.value:
            counters["sessions"] += 1
        elif event.event_type == EventType.product_view.value:
            counters["pdp_views"] += 1
        elif event.event_type == EventType.add_to_cart.value:
            counters["atc"] += 1
        elif event.event_type == EventType.checkout_started.value:
            counters["checkouts"] += 1
        elif event.event_type == EventType.purchase.value:
            counters["orders"] += 1
            counters["revenue_paise"] += int(metadata.get("revenue_paise", 0))

    await session.execute(delete(EventDaily).where(EventDaily.merchant_id == ctx.merchant_id))
    for (product_id, day, channel, variant), counters in grouped.items():
        session.add(EventDaily(merchant_id=ctx.merchant_id, product_id=product_id, day=day,
                               channel=channel, variant=variant, **counters))
    await session.flush()

    computed_at = datetime.now(timezone.utc)
    window = "all_time"
    snapshots: list[FactSnapshot] = []
    product_ids = {product_id for product_id, *_ in grouped if product_id is not None}
    for product_id in sorted(product_ids, key=str):
        counters = {name: 0 for name in ("sessions", "pdp_views", "atc", "checkouts", "orders", "revenue_paise")}
        for (candidate, _day, _channel, _variant), values in grouped.items():
            if candidate == product_id:
                for name in counters:
                    counters[name] += values[name]
        metrics = [
            ("product_views", Decimal(counters["pdp_views"]), "count", counters["pdp_views"]),
            ("add_to_cart_rate", _rate(counters["atc"], counters["pdp_views"]), "ratio", counters["pdp_views"]),
            ("checkout_rate", _rate(counters["checkouts"], counters["pdp_views"]), "ratio", counters["pdp_views"]),
            ("product_view_to_purchase_conversion_rate", _rate(counters["orders"], counters["pdp_views"]), "ratio", counters["pdp_views"]),
            ("revenue", Decimal(counters["revenue_paise"]), "paise", counters["orders"]),
        ]
        for metric, value, unit, sample_size in metrics:
            snapshots.append(FactSnapshot(merchant_id=ctx.merchant_id, product_id=product_id, metric=metric,
                                          value=value, unit=unit, window=window, method="event_aggregation",
                                          source="bi.storefront", sample_size=sample_size, computed_at=computed_at))
    total = {name: sum(values[name] for values in grouped.values()) for name in ("sessions", "revenue_paise")}
    for metric, value, unit, sample_size in [
        ("sessions", Decimal(total["sessions"]), "count", total["sessions"]),
        ("revenue", Decimal(total["revenue_paise"]), "paise", total["sessions"]),
    ]:
        snapshots.append(FactSnapshot(merchant_id=ctx.merchant_id, metric=metric, value=value, unit=unit,
                                      window=window, method="event_aggregation", source="bi.storefront",
                                      sample_size=sample_size, computed_at=computed_at))
    session.add_all(snapshots)
    await session.flush()
    return snapshots