"""Datos del usuario logueado (auxiliar, lo usa el front)."""
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Devuelve el usuario dueño del token. No hay edición de perfil."""
    return current_user
