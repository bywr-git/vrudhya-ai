from uuid import UUID

from pydantic import BaseModel

from app.schemas.learning import LearningOut


class AgentLoopOut(BaseModel):
    learning: LearningOut
    next_opportunity_id: UUID | None
    next_stage: str