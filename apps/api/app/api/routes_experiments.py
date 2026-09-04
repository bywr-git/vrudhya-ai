"""Phase 4 simulation, permission, and experiment-draft routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db_session
from app.schemas.experiments import ExperimentDraftOut
from app.schemas.permissions import PermissionOut
from app.schemas.simulations import SimulationOut
from app.services.context import MerchantContext
from app.services.experiment_draft import create_experiment_draft

router = APIRouter(prefix="/v1/experiments", tags=["experiments"])


@router.post("/draft/{strategy_id}", response_model=ExperimentDraftOut)
async def draft_experiment(
    strategy_id: UUID,
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentDraftOut:
    try:
        simulation, permission, experiment = await create_experiment_draft(session, ctx, strategy_id)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExperimentDraftOut(
        simulation=SimulationOut.model_validate(simulation, from_attributes=True),
        permission=PermissionOut(
            merchant_id=permission.merchant_id,
            strategy_id=permission.strategy_id,
            action_type=permission.action_type,
            outcome=permission.outcome,
            reason=permission.reason,
        ),
        experiment=experiment,
    )