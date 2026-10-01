"""REQ 4 y 5 - Comportamientos."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.behavior import BehaviorDetailOut, BehaviorOut
from app.services import behavior_service

router = APIRouter(prefix="/behaviors", tags=["Behaviors"])


@router.get("", response_model=list[BehaviorOut])
def list_behaviors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """REQ 4 - Listar comportamientos existentes."""
    return behavior_service.list_behaviors(db, current_user)


@router.get("/{behavior_id}", response_model=BehaviorDetailOut)
def get_behavior(
    behavior_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """REQ 5 - Detalle de un comportamiento por default."""
    return behavior_service.get_behavior(db,current_user, behavior_id)
