"""Development-only synchronous observe endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.schemas.events import EventIngestResult, StorefrontEventIn
from app.schemas.facts import FactSnapshotOut
from app.services.bi import build_snapshots
from app.services.context import MerchantContext
from app.services.detect import detect_opportunities
from app.services.ingest import ingest_events

router = APIRouter(prefix="/v1", tags=["observe-detect"])


@router.post("/events", response_model=EventIngestResult)
async def post_events(
    payloads: list[StorefrontEventIn],
    session: AsyncSession = Depends(get_db_session),
    ctx: MerchantContext = Depends(get_current_merchant),
) -> EventIngestResult:
    try:
        accepted, duplicates = await ingest_events(session, ctx, payloads)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EventIngestResult(accepted=accepted, duplicates=duplicates)


@router.post("/bi/snapshots", response_model=list[FactSnapshotOut])
async def post_snapshots(
    session: AsyncSession = Depends(get_db_session),
    ctx: MerchantContext = Depends(get_current_merchant),
) -> list[FactSnapshotOut]:
    snapshots = await build_snapshots(session, ctx)
    await session.commit()
    return [FactSnapshotOut(
        fact_id=snapshot.id, merchant_id=snapshot.merchant_id, metric=snapshot.metric,
        value=snapshot.value, unit=snapshot.unit, window=snapshot.window, method=snapshot.method,
        source=snapshot.source, sample_size=snapshot.sample_size, computed_at=snapshot.computed_at,
        product_id=snapshot.product_id, experiment_id=snapshot.experiment_id,
    ) for snapshot in snapshots]


@router.post("/detection/run", response_model=int)
async def run_detection(
    session: AsyncSession = Depends(get_db_session),
    ctx: MerchantContext = Depends(get_current_merchant),
) -> int:
    opportunities = await detect_opportunities(session, ctx)
    await session.commit()
    return len(opportunities)