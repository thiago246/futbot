"""Tests unitarios de services/behavior_service.py (REQ 4, 5)

Cada test está marcado como pendiente (skip). Al implementar el requerimiento,
sacar el @pytest.mark.skip y escribir el test.
"""
import pytest
from sqlalchemy import select

from app.core.exceptions import BehaviorNotFoundError
from app.models.behavior import Behavior, UserBehavior
from app.services import behavior_service

def test_seed_creates_default_behaviors(db):
    """After the seed there are at least 3 behaviors"""
    behavior_service.seed_default_behaviors(db)

    stmt = select(Behavior)
    behaviors = db.scalars(stmt).all()

    assert len(behaviors) >= 3
    names = [b.name for b in behaviors]
    assert "Ofensivo" in names
    assert "Defensivo" in names
    assert "Equilibrado" in names

def test_seed_is_idempotent(db):
    behavior_service.seed_default_behaviors(db)
    behavior_service.seed_default_behaviors(db)

    stmt = select(Behavior)
    behaviors = db.scalars(stmt).all()

    names = [b.name for b in behaviors]
    assert names.count("Ofensivo") == 1
    assert names.count("Defensivo") == 1
    assert names.count("Equilibrado") == 1

def test_assign_defaults_to_user(db, user):
    """The user ends up with exactly the 3 default behaviors"""
    behavior_service.seed_default_behaviors(db)

    behavior_service.assign_defaults_to_user(db, user)

    result = behavior_service.list_behaviors(db, user)
    assert len(result) == 3
    assert {b.name for b in result} == {"Ofensivo", "Defensivo", "Equilibrado"}
    assert all(b.is_default for b in result)

def test_list_behaviors(db,user):
    """Lists the user's behaviors"""
    # Creo comportamientos
    behavior_default = Behavior(
        name="Ofensivo",
        code="def decidir(contexto):\n    pass",
    )
    behavior_custom = Behavior(
        name="MiComportamiento",
        code="def decidir(contexto):\n    pass",
        is_default=False,
    )
    db.add(behavior_default)
    db.add(behavior_custom)
    db.commit()

    # vinculo
    link_default = UserBehavior(user_id=user.id, behavior_id=behavior_default.id)
    link_custom = UserBehavior(user_id=user.id, behavior_id=behavior_custom.id)
    db.add(link_default)
    db.add(link_custom)
    db.commit()

    result = behavior_service.list_behaviors(db, user)

    assert len(result) == 2

    name = [b.name for b in result]
    assert "Ofensivo" in name
    assert "MiComportamiento" in name

    defaults = [b.is_default for b in result]
    assert True in defaults
    assert False in defaults



def test_get_behavior_existing(db, user):
    """Returns the behavior detail"""
    behavior = Behavior(
        name="Ofensivo",
        code="def decidir(contexto):\n    pass",
    )
    db.add(behavior)
    db.commit()

    db.add(UserBehavior(user_id=user.id, behavior_id=behavior.id))
    db.commit()

    result = behavior_service.get_behavior(db, user, behavior.id)

    assert result.name == "Ofensivo"
    assert result.code == "def decidir(contexto):\n    pass"
    assert result.is_default is True
    


def test_get_behavior_not_found(db, user):
    """A nonexistent id raises BehaviorNotFoundError (404)"""
    with pytest.raises(BehaviorNotFoundError):
        behavior_service.get_behavior(db, user, 9999)

def test_get_behavior_of_other_user_not_found(db, user):
    """A behavior that exists but is not linked to the user also gives 404"""
    behavior = Behavior(
        name="NotLinkedToUser",
        code="def decidir(contexto):\n    pass",
        is_default=False,
    )
    db.add(behavior)
    db.commit()  

    with pytest.raises(BehaviorNotFoundError):
        behavior_service.get_behavior(db, user, behavior.id)
