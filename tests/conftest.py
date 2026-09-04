"""PostgreSQL integration-test fixtures."""

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import Merchant
from app.services.context import MerchantContext

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is required")


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    if TEST_DATABASE_URL is None:
        pytest.skip("TEST_DATABASE_URL is required")
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        await connection.exec_driver_sql(
            """
            CREATE OR REPLACE FUNCTION fact_snapshots_immutable()
            RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'fact_snapshots is immutable'; END; $$ LANGUAGE plpgsql
            """
        )
        await connection.exec_driver_sql(
            """
            CREATE TRIGGER test_fact_snapshots_no_update
            BEFORE UPDATE ON fact_snapshots FOR EACH ROW EXECUTE FUNCTION fact_snapshots_immutable()
            """
        )
        await connection.exec_driver_sql(
            """
            CREATE TRIGGER test_fact_snapshots_no_delete
            BEFORE DELETE ON fact_snapshots FOR EACH ROW EXECUTE FUNCTION fact_snapshots_immutable()
            """
        )
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def merchant_context(db_session: AsyncSession) -> MerchantContext:
    merchant = Merchant(name="Lumi Gifts", data_mode="synthetic")
    db_session.add(merchant)
    await db_session.flush()
    return MerchantContext(merchant_id=merchant.id, name=merchant.name, data_mode=merchant.data_mode,
                           autonomy_kill_switch=merchant.autonomy_kill_switch)