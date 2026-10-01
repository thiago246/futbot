"""REQ 16 - Estado del partido (versión REST)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.match import MatchOut
from app.services import match_service

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """REQ 16 - Ver estado actual del partido."""
    return match_service.get_match(db, match_id)
