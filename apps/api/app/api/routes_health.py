"""Liveness and database connectivity."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import get_engine
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health():
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return HealthOut(status="ok", database="ok")
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "error"},
        )
