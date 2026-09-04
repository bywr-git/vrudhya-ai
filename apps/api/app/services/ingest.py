"""Deterministic canonical synthetic storefront ingestion."""

from collections.abc import Iterable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, Product
from app.schemas.events import StorefrontEventIn
from app.services.context import MerchantContext


async def ingest_events(
    session: AsyncSession, ctx: MerchantContext, payloads: Iterable[StorefrontEventIn]
) -> tuple[int, int]:
    events = list(payloads)
    event_ids = [payload.event_id for payload in events]
    existing = set(
        (await session.execute(
            select(Event.client_event_id).where(
                Event.merchant_id == ctx.merchant_id,
                Event.client_event_id.in_(event_ids),
            )
        )).scalars().all()
    ) if event_ids else set()
    product_ids = {payload.product_id for payload in events if payload.product_id is not None}
    if product_ids:
        valid_products = set((await session.execute(
            select(Product.id).where(Product.merchant_id == ctx.merchant_id, Product.id.in_(product_ids))
        )).scalars().all())
        missing = product_ids - valid_products
        if missing:
            raise ValueError("All product_id values must belong to the current merchant")

    accepted = 0
    for payload in events:
        if payload.event_id in existing:
            continue
        session.add(Event(
            merchant_id=ctx.merchant_id,
            client_event_id=payload.event_id,
            event_type=payload.event_type.value,
            occurred_at=payload.occurred_at,
            product_id=payload.product_id,
            visitor_key=payload.visitor_key,
            order_id=payload.order_id,
            payment_id=payload.payment_id,
            event_metadata={
                "channel": payload.channel,
                "variant": payload.variant,
                "revenue_paise": payload.revenue_paise,
            },
        ))
        existing.add(payload.event_id)
        accepted += 1
    await session.flush()
    return accepted, len(events) - accepted