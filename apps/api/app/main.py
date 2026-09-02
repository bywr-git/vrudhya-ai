"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_v1 import router as v1_router
from app.db.session import get_engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    engine = get_engine()
    await engine.dispose()


app = FastAPI(
    title="Vrudhya.ai API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(v1_router)
