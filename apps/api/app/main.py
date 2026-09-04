"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_diagnosis import router as diagnosis_router
from app.api.routes_experiments import router as experiments_router
from app.api.routes_execution import router as execution_router
from app.api.routes_health import router as health_router
from app.api.routes_intelligence import router as intelligence_router
from app.api.routes_learning import router as learning_router
from app.api.routes_events import router as events_router
from app.api.routes_radar import router as radar_router
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
app.include_router(diagnosis_router)
app.include_router(experiments_router)
app.include_router(execution_router)
app.include_router(health_router)
app.include_router(intelligence_router)
app.include_router(learning_router)
app.include_router(events_router)
app.include_router(radar_router)
app.include_router(v1_router)
