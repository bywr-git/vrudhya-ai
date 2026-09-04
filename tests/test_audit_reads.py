from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import AuditLog, Merchant
from app.services.context import MerchantContext


@pytest.mark.asyncio
async def test_audit_read_is_merchant_scoped(db_session, merchant_context):
    other = Merchant(name="Other Merchant", data_mode="synthetic")
    db_session.add(other)
    await db_session.flush()
    db_session.add_all([
        AuditLog(
            merchant_id=merchant_context.merchant_id,
            actor="system",
            action="experiment.measured",
            target={"experiment_id": str(uuid4())},
            timestamp=datetime.now(timezone.utc),
            idempotency_key="audit-test-a",
            result="measured",
            permission_outcome="allowed",
            kill_switch_state=False,
        ),
        AuditLog(
            merchant_id=other.id,
            actor="system",
            action="other.merchant.event",
            target={},
            timestamp=datetime.now(timezone.utc),
            idempotency_key="audit-test-b",
            result="hidden",
            permission_outcome="denied",
            kill_switch_state=False,
        ),
    ])
    await db_session.flush()

    from app.api.deps import get_current_merchant
    from app.db.session import get_db_session
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    async def override_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_merchant] = lambda: merchant_context
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/v1/audit")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["action"] == "experiment.measured"
    finally:
        app.dependency_overrides.clear()