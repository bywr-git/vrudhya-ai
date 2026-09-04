"""Phase 3 Diagnose -> Hypothesize -> Strategize API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant, get_db_session
from app.schemas.diagnosis import DiagnosisOut
from app.schemas.hypotheses import HypothesisOut
from app.schemas.strategies import StrategyOut
from app.services.context import MerchantContext
from app.services.diagnose import diagnose_opportunity
from app.services.hypothesize import hypothesize_diagnosis
from app.services.strategize import strategize_hypothesis


router = APIRouter(
    prefix="/v1/opportunities",
    tags=["diagnosis"],
)


@router.post(
    "/{opportunity_id}/diagnose",
)
async def diagnose(
    opportunity_id: UUID,
    ctx: MerchantContext = Depends(get_current_merchant),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        diagnosis = await diagnose_opportunity(
            session=session,
            ctx=ctx,
            opportunity_id=opportunity_id,
        )

        hypothesis = await hypothesize_diagnosis(
            session=session,
            ctx=ctx,
            diagnosis_id=diagnosis.id,
        )

        strategy = await strategize_hypothesis(
            session=session,
            ctx=ctx,
            hypothesis_id=hypothesis.id,
        )

        return {
            "diagnosis": DiagnosisOut.model_validate(diagnosis),
            "hypothesis": HypothesisOut.model_validate(hypothesis),
            "strategy": StrategyOut.model_validate(strategy),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc