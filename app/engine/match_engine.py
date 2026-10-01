"""Motor del partido. (REQ 14 y 15)

Es lo que hace que un partido "se juegue solo": en cada tick le pregunta a los
comportamientos de los jugadores qué hacer (REQ 15), actualiza el estado, lo guarda en la
DB y lo emite por WebSocket (REQ 16). Sin pausas, sustituciones ni interacción del usuario.
"""
import asyncio
import math

from app.core.database import SessionLocal
from app.core.ws_manager import manager
from app.behaviors.registry import load_behavior
from app.engine.behavior_executor import execute_turn
from app.engine.match_state import FIELD_HEIGHT, FIELD_WIDTH, GOAL_Y_MAX, GOAL_Y_MIN, MatchState
from app.engine.player_on_field import PlayerOnField, control_range, read_attributes
from app.models.match import Match

# segundos reales entre tick y tick. Debe coincidir con TICKS_PER_MINUTE
# de match_state.py (60/min = 1 tick por segundo); si uno cambia, cambia el otro.
TICK_SECONDS = 1.0


class MatchEngine:
    def __init__(self, match_id: str, participants: dict, duration_minutes: int) -> None:
        """match_id: UUID del partido (str), igual que en el resto de la API.
        duration_minutes: la `duracion` con la que se creó el partido (1, 3 o 5).

        participants: un dict con una entrada por club, con esta forma:

            {
                "home": {"players": [j1, j2, j3], "formation": "1-2"},
                "away": {"players": [j4, j5, j6], "formation": "2-1"},
            }

        - "players": los 3 titulares del club EN ORDEN (el orden define su posición
          dentro de la formación). Cada uno debe tener:
            - `.id`
            - `.strength`, `.control`, `.precision`, `.agility`, `.speed`: las 5 PACSS,
              igual que las columnas de ClubPlayer. Es requisito para entrar a un
              partido, así que se asumen siempre presentes (sin valor por defecto).
            - `.decide` (la función `decidir` ya cargada con
              behaviors.registry.load_behavior) O `.behavior_code` (el código fuente,
              y el motor la carga una sola vez acá).
        - "formation": nombre elegido en la plantilla ("1-2" o "2-1").
        - "home" es el club creador del partido.
        """
        self.match_id = match_id
        self.participants = participants
        self.duration_minutes = duration_minutes
        self.room = f"match:{match_id}"
        # Estado en memoria: existe solo mientras el partido está en curso y NUNCA se
        # persiste. Lo crea build_initial_state() y lo descarta discard_state().
        self.state: MatchState | None = None
        # Datos fijos por jugador, armados una sola vez en build_initial_state():
        # de qué lado juega, sus atributos y su función decidir() ya cargada.
        self._player_ids: list[str] = []
        self._sides: dict[str, str] = {}
        self._attributes: dict[str, dict[str, int]] = {}
        self._decide_fns: dict[str, callable] = {}

    def build_initial_state(self) -> MatchState:
        """Estado de arranque: posiciones iniciales de los 6 jugadores, pelota al
        centro y marcador/tick en 0. Lo guarda en self.state.
        También arma una sola vez los datos fijos de cada jugador (REQ 15): lado,
        atributos y comportamiento ya cargado."""
        home = self.participants["home"]
        away = self.participants["away"]
        self.state = MatchState.initial(
            self.match_id,
            self.duration_minutes,
            [str(p.id) for p in home["players"]],
            [str(p.id) for p in away["players"]],
            home["formation"],
            away["formation"],
        )
        self._prepare_players()
        return self.state

    def discard_state(self) -> None:
        """Descarta por completo el estado en memoria."""
        self.state = None

    def _prepare_players(self) -> None:
        for side in ("home", "away"):
            for player in self.participants[side]["players"]:
                pid = str(player.id)
                self._player_ids.append(pid)
                self._sides[pid] = side
                self._attributes[pid] = read_attributes(player)
                self._decide_fns[pid] = self._resolve_decide(player)

    @staticmethod
    def _resolve_decide(player):
        decide = getattr(player, "decide", None)
        if callable(decide):
            return decide
        code = getattr(player, "behavior_code", None)
        if code:
            return load_behavior(code)
        raise ValueError(
            f"El jugador {getattr(player, 'id', '?')} no tiene comportamiento cargado "
            "(.decide callable o .behavior_code)"
        )

    async def run(self) -> None:
        """Bucle principal (se lanza con asyncio.create_task desde friendly_service.start_friendly)."""
        if self.state is None:
            self.build_initial_state()
        while not self.is_finished():
            self.tick()
            self._persist_state()
            await manager.broadcast(self.room, self._state_payload())
            await asyncio.sleep(TICK_SECONDS)
        self._persist_state(final=True)
        await manager.broadcast(self.room, {"type": "finished", "data": self._state_payload()})
        self.discard_state()

    def _state_payload(self) -> dict:
        """Payload mínimo para el WebSocket."""
        state = self.state
        return {
            "tick": state.current_tick,
            "ball": {"x": state.ball.x, "y": state.ball.y},
            "positions": dict(state.positions),
            "score": {"home": state.home_score, "away": state.away_score},
        }

    def _persist_state(self, final: bool = False) -> None:
        """Guarda en la tabla matches lo que NO es parte del estado en memoria
        (REQ 14): marcador, tick/minuto y status. NUNCA state.positions.
        """
        if self.state is None:
            return
        db = SessionLocal()
        try:
            match = db.get(Match, self.match_id)
            if match is None:
                return
            match.home_score = self.state.home_score
            match.away_score = self.state.away_score
            match.minute = self.state.current_tick  # [SUPUESTO] "minute" = tick actual
            match.status = "finished" if final else "in_progress"
            db.commit()
        finally:
            db.close()

    def tick(self) -> None:
        """Avanza un paso: para cada jugador, ejecutar su comportamiento (REQ 15)
        con execute_behavior() y después mover la pelota (rebotes/goles)."""
        if self.state is None:
            raise RuntimeError("build_initial_state() debe llamarse antes de tick()")
        for player_id in self._player_ids:
            self.execute_behavior(player_id)
        self._advance_ball()
        self.state.current_tick += 1

    def execute_behavior(self, player_id: str) -> None:
        """REQ 15 - Ejecuta el comportamiento de un jugador para este tick: arma su
        contexto y llama a execute_turn(), que corre decidir(contexto)."""
        context = self._build_context(player_id)
        player = PlayerOnField(player_id, self._attributes, self.state)
        execute_turn(player, self._decide_fns[player_id], context)

    def _build_context(self, player_id: str) -> dict:
        """Forma del `contexto` que recibe decidir(contexto):
        mi_id, jugador_con_pelota, posicion_pelota, arco_rival y
        jugadores_rivales."""
        state = self.state
        side = self._sides[player_id]

        def as_dict(pid: str) -> dict:
            return {"id": pid, "posicion": state.positions[pid]}

        return {
            "mi_id": player_id,
            "posicion_propia": state.positions[player_id],
            "posicion_pelota": (state.ball.x, state.ball.y),
            "jugador_con_pelota": self._player_with_ball(),
            "arco_rival": self._rival_goal(side),
            "jugadores_rivales": [
                as_dict(pid) for pid in self._player_ids if self._sides[pid] != side
            ],
            "jugadores_companeros": [
                as_dict(pid)
                for pid in self._player_ids
                if self._sides[pid] == side and pid != player_id
            ],
        }

    def _player_with_ball(self) -> str | None:
        """Quién tiene la pelota en este instante: el jugador más cercano que la
        tiene dentro de su alcance de control"""
        state = self.state
        candidatos = []
        for pid in self._player_ids:
            px, py = state.positions[pid]
            distancia = math.hypot(state.ball.x - px, state.ball.y - py)
            if distancia <= control_range(self._attributes[pid]):
                candidatos.append((distancia, pid))
        if not candidatos:
            return None
        candidatos.sort(key=lambda t: (t[0], t[1]))
        return candidatos[0][1]

    def _rival_goal(self, side: str) -> tuple[float, float]:
        """Centro del arco rival"""
        x = FIELD_WIDTH if side == "home" else 0.0
        return (x, FIELD_HEIGHT / 2)

    def apply_action(self, player, action: dict) -> None:
        """No se usa en este diseño: ver la nota en execute_behavior(). Se deja
        definida (sin efecto) para no romper si algo todavía la llama."""
        return None

    # -------------------------------------------------------------- física de la pelota
    def _advance_ball(self) -> None:
        """Mueve la pelota según su velocidad y resuelve rebotes/goles en los bordes."""
        ball = self.state.ball
        ball.x += ball.vx
        ball.y += ball.vy

        # Arriba/abajo: siempre rebota, no hay arcos en esos bordes.
        if ball.y < 0:
            ball.y, ball.vy = -ball.y, -ball.vy
        elif ball.y > FIELD_HEIGHT:
            ball.y, ball.vy = 2 * FIELD_HEIGHT - ball.y, -ball.vy

        # Izquierda/derecha: gol si cruza dentro del arco, si no, rebota.
        if ball.x < 0:
            if GOAL_Y_MIN <= ball.y <= GOAL_Y_MAX:
                self._score_goal("away")
            else:
                ball.x, ball.vx = -ball.x, -ball.vx
        elif ball.x > FIELD_WIDTH:
            if GOAL_Y_MIN <= ball.y <= GOAL_Y_MAX:
                self._score_goal("home")
            else:
                ball.x, ball.vx = 2 * FIELD_WIDTH - ball.x, -ball.vx

    def _score_goal(self, scorer: str) -> None:
        """scorer: el club que convirtió (arco de enfrente al que defiende)."""
        if scorer == "home":
            self.state.home_score += 1
        else:
            self.state.away_score += 1
        # [SUPUESTO] saque del medio tras el gol: la pelota vuelve al centro, quieta.
        self.state.ball.x, self.state.ball.y = FIELD_WIDTH / 2, FIELD_HEIGHT / 2
        self.state.ball.vx = self.state.ball.vy = 0.0

    def is_finished(self) -> bool:
        """True cuando se cumple la condición de fin (llegó a la duración configurada)."""
        return self.state is not None and self.state.is_over()