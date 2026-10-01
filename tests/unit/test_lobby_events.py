from app.schemas.league import LeagueLobbyOut
from app.services import lobby_events as ev


def _lobby(current, min_teams=3, max_teams=4):
    return LeagueLobbyOut(
        id="L1", nombre="Liga", estado="esperando_equipos",
        minEquipos=min_teams, maxEquipos=max_teams,
        equiposActuales=current, cuposRestantes=max_teams - current,
        listaParaIniciar=current >= min_teams, equipos=[],
    )


def test_lobby_room_name():
    assert ev.lobby_room("abc") == "league:abc"


def test_team_joined_carries_updated_capacity():
    e = ev.team_joined_event(_lobby(2), "c1", "Los Thiagos")
    assert e == {"tipo": "equipo_unido", "clubId": "c1", "clubNombre": "Los Thiagos",
                 "equiposActuales": 2, "maxEquipos": 4, "cuposRestantes": 2}


def test_join_below_min_emits_only_equipo_unido():
    assert [e["tipo"] for e in ev.events_on_join(_lobby(2), "c", "C")] == ["equipo_unido"]


def test_join_reaching_min_emits_ready_once():
    types = [e["tipo"] for e in ev.events_on_join(_lobby(3), "c", "C")]
    assert types == ["equipo_unido", "liga_lista_para_iniciar"]


def test_join_when_min_already_reached_does_not_repeat_ready():
    assert [e["tipo"] for e in ev.events_on_join(_lobby(4), "c", "C")] == ["equipo_unido"]


def test_ready_event_payload():
    assert ev.ready_to_start_event(_lobby(3)) == {
        "tipo": "liga_lista_para_iniciar", "equiposActuales": 3, "minEquipos": 3}


def test_leave_emits_equipo_abandono_with_capacity():
    (e,) = ev.events_on_leave(_lobby(2), "c1", "C")
    assert e["tipo"] == "equipo_abandono" and e["equiposActuales"] == 2 and e["cuposRestantes"] == 2


def test_cancelled_event():
    assert ev.league_cancelled_event("L1") == {"tipo": "liga_cancelada", "ligaId": "L1"}
