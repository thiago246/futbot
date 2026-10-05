"""match_service.match_is_watchable: cuándo se puede abrir el canal en vivo."""
from app.models.friendly import Friendly
from app.models.match import Match
from app.services.match_service import match_is_watchable


def _friendly(db, status="cuenta_regresiva") -> str:
    f = Friendly(home_club_id="c1", away_club_id="c2", duration=1, status=status)
    db.add(f)
    db.commit()
    return f.id


def test_partido_inexistente_no_se_puede_mirar(db):
    assert match_is_watchable(db, "no-existe") is False


def test_amistoso_en_cuenta_regresiva_sin_match_se_puede_mirar(db):
    assert match_is_watchable(db, _friendly(db)) is True


def test_amistoso_finalizado_sin_match_no_se_puede_mirar(db):
    assert match_is_watchable(db, _friendly(db, status="finalizado")) is False


def test_match_en_curso_se_puede_mirar(db):
    mid = _friendly(db, status="en_curso")
    db.add(Match(id=mid, friendly_id=mid, status="in_progress"))
    db.commit()
    assert match_is_watchable(db, mid) is True


def test_match_finished_no_se_puede_mirar(db):
    mid = _friendly(db, status="en_curso")
    db.add(Match(id=mid, friendly_id=mid, status="finished"))
    db.commit()
    assert match_is_watchable(db, mid) is False
