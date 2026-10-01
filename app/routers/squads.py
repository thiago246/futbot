"""Club squad endpoints (REQ: Define club squad)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.squads import SquadInput, SquadOut
from app.services import squads_service

router = APIRouter(prefix="/clubs/me", tags=["Squad"])


@router.put("/squad", response_model=SquadOut)
def save_squad(
    data: SquadInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates or replaces the club's squad."""
    return squads_service.save_squad(db, current_user, data)


@router.get("/squad", response_model=SquadOut)
def get_squad(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the club's squad."""
    return squads_service.get_squad(db, current_user)