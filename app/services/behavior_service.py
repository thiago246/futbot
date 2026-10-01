"""Lógica de comportamientos."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import BehaviorNotFoundError
from app.models.behavior import Behavior, UserBehavior
from app.models.user import User
from app.behaviors.defaults import DEFAULT_BEHAVIORS


def seed_default_behaviors(db: Session) -> None:
    """Se ejecuta al arrancar la app (main.py -> lifespan).

    Recorre behaviors.registry.DEFAULT_BEHAVIORS y crea en la DB los que no existan
    """
    for data in DEFAULT_BEHAVIORS:
        stmt = select(Behavior).where(Behavior.name == data["name"])
        exists = db.scalars(stmt).first()
        if not exists:
            behavior = Behavior(
                name=data["name"],
                description=data.get("description", ""),
                code=data["code"],
                is_default=True,
            )
            db.add(behavior)
    db.flush()


def assign_defaults_to_user(db: Session, user: User) -> None:
    """Vincula al usuario con todos los comportamientos is_default=True (tabla user_behaviors).
    Lo llama auth_service.register_user."""
    stmt = select(Behavior).where(Behavior.is_default == True)
    default_behaviors = db.scalars(stmt).all()

    for behavior in default_behaviors:
        user_behavior = UserBehavior(user_id=user.id, behavior_id=behavior.id)
        db.add(user_behavior)

    db.flush()



def list_behaviors(db: Session, user: User) -> list[Behavior]:
    """Comportamientos disponibles para el usuario."""
    stmt = (
        select(Behavior)
        .join(UserBehavior, UserBehavior.behavior_id == Behavior.id)
        .where(UserBehavior.user_id == user.id)
    )   
    return db.scalars(stmt).all()

def get_behavior(db: Session, user: User, behavior_id: int) -> Behavior:
    """Detalle de un comportamiento. Si no existe -> HTTPException 404."""
    stmt = (
        select(Behavior)
        .join(UserBehavior, UserBehavior.behavior_id == Behavior.id)
        .where(
            UserBehavior.user_id == user.id,
            Behavior.id == behavior_id,
        )
    )
    behavior = db.scalars(stmt).first()

    if behavior is None:
        raise BehaviorNotFoundError()

    return behavior
