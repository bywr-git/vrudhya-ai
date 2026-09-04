"""Tenant-scoped data access. Always binds queries to MerchantContext.merchant_id."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Customer, Event, Merchant, Order, Product
from app.services.context import MerchantContext


class TenantAccess:
    """Reusable data-access boundary: every query includes merchant_id from auth context."""

    def __init__(self, session: AsyncSession, ctx: MerchantContext) -> None:
        self._session = session
        self._merchant_id = ctx.merchant_id

    @property
    def merchant_id(self) -> UUID:
        return self._merchant_id

    async def get_merchant(self) -> Merchant | None:
        stmt = select(Merchant).where(Merchant.id == self._merchant_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_products(self) -> Sequence[Product]:
        stmt = (
            select(Product)
            .where(Product.merchant_id == self._merchant_id)
            .order_by(Product.sku)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_product(self, product_id: UUID) -> Product | None:
        stmt = select(Product).where(
            Product.id == product_id,
            Product.merchant_id == self._merchant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_orders(self) -> Sequence[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.merchant_id == self._merchant_id)
            .order_by(Order.placed_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_product(
        self,
        *,
        sku: str,
        name: str,
        price_paise: int,
        category: str,
        status: str = "active",
        cost_paise: int | None = None,
        product_id: UUID | None = None,
    ) -> Product:
        product = Product(
            merchant_id=self._merchant_id,
            sku=sku,
            name=name,
            price_paise=price_paise,
            category=category,
            status=status,
            cost_paise=cost_paise,
        )
        if product_id is not None:
            product.id = product_id
        self._session.add(product)
        await self._session.flush()
        return product

    async def create_event(
        self,
        *,
        event_id: UUID,
        event_type: str,
        occurred_at,
        product_id: UUID | None = None,
        customer_id: UUID | None = None,
        visitor_key: str | None = None,
        order_id: UUID | None = None,
        payment_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> Event:
        event = Event(
            merchant_id=self._merchant_id,
            client_event_id=event_id,
            event_type=event_type,
            occurred_at=occurred_at,
            product_id=product_id,
            customer_id=customer_id,
            visitor_key=visitor_key,
            order_id=order_id,
            payment_id=payment_id,
            event_metadata=metadata,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_events(self) -> Sequence[Event]:
        stmt = (
            select(Event)
            .where(Event.merchant_id == self._merchant_id)
            .order_by(Event.occurred_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_customers(self) -> Sequence[Customer]:
        stmt = select(Customer).where(Customer.merchant_id == self._merchant_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()
