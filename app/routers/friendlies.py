"""REQ 11 a 14 - Amistosos.

Los amistosos viven bajo /matches 
(POST /matches, GET /matches, POST /matches/{id}/join).
Unirse inicia el partido automáticamente: no hay un POST /matches/{id}/start.
El router de matches.py solo se ocupa de GET /matches/{id}.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.friendly import (
    FriendlyCreate,
    FriendlyKind,
    FriendlyOut,
    FriendlyStatus,
    PaginatedFriendlies,
)
from app.services import friendly_service

router = APIRouter(prefix="/matches", tags=["Friendlies"])

@router.post("", response_model=FriendlyOut, status_code=status.HTTP_201_CREATED)
def create_friendly(
    data: FriendlyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear amistoso: publica un partido esperando rival, con el club propio como local."""
    return friendly_service.create_friendly(db, current_user, data)

@router.get("", response_model=PaginatedFriendlies)
def list_friendlies(
    # Se llaman *_filter para no pisar el `status` importado de fastapi.
    status_filter: FriendlyStatus | None = Query(default=None, alias="estado"),
    kind_filter: FriendlyKind | None = Query(default=None, alias="tipo"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar amistosos, filtrando por estado y tipo. Los más antiguos primero."""
    items, total = friendly_service.list_friendlies(
        db, status_filter, kind_filter, page, page_size
    )
    return PaginatedFriendlies(items=items, page=page, page_size=page_size, total=total)

@router.post("/{match_id}/join", response_model=FriendlyOut)
def join_friendly(
    match_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unirse a un amistoso esperando rival: el club propio queda como visitante,
    se congelan las plantillas de ambos clubes y el partido pasa a "cuenta_regresiva".
    A los 15 segundos pasa solo a "en_curso"."""
    friendly = friendly_service.join_friendly(db, current_user, match_id)
    background_tasks.add_task(friendly_service.run_countdown, friendly.id)
    return friendly