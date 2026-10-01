"""Estado en memoria del partido. (REQ 14)

Solo existe mientras el partido está en_curso y NO se persiste: el motor lo crea al
arrancar la simulación y lo descarta al finalizar (ver MatchEngine).
"""
from __future__ import annotations

from dataclasses import dataclass, field

Coordinate = tuple[float, float]

# cancha fija de n x m
FIELD_WIDTH = 100.0  # n
FIELD_HEIGHT = 60.0  # m

STARTERS_PER_CLUB = 3

# ancho del arco, centrado verticalmente en la cancha. 
GOAL_WIDTH = 20.0
GOAL_Y_MIN = (FIELD_HEIGHT - GOAL_WIDTH) / 2
GOAL_Y_MAX = (FIELD_HEIGHT + GOAL_WIDTH) / 2

# velocidad de la simulación: 1 tick = 1 segundo real
TICKS_PER_MINUTE = 60

# Catálogo de formaciones predeterminadas: nombre -> posición inicial de cada
# titular, para el club HOME (ataca hacia +x). El AWAY se espeja en x.
# El ORDEN importa: el 1er titular de la plantilla va a la 1ra posición, y así.
# Formaciones definidas por el grupo: "1-2" y "2-1" (las coordenadas son supuestas);
# la plantilla (PUT /clubs/me/squad) debería validar contra estas mismas claves.
FORMATIONS: dict[str, list[Coordinate]] = {
    "1-2": [(10.0, 30.0), (30.0, 15.0), (30.0, 45.0)],
    "2-1": [(10.0, 20.0), (10.0, 40.0), (30.0, 30.0)],
}


@dataclass
class Ball:
    x: float
    y: float
    # Velocidad actual (unidades/tick). Un pase/patada la fija;
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class MatchState:
    match_id: str
    # Duración configurada del partido.
    duration_minutes: int
    ball: Ball
    # Marcador y tick en memoria.
    home_score: int = 0
    away_score: int = 0
    current_tick: int = 0
    # id de jugador -> (x, y) absolutas, solo los 6 en cancha
    positions: dict[str, Coordinate] = field(default_factory=dict)

    @classmethod
    def initial(
        cls,
        match_id: str,
        duration_minutes: int,
        home_ids: list[str],
        away_ids: list[str],
        home_formation: str,
        away_formation: str,
    ) -> "MatchState":
        """Posiciones de arranque: pelota al centro y cada club según su formación."""
        if duration_minutes <= 0:
            raise ValueError("La duración debe ser un entero positivo de minutos")
        if len(home_ids) != STARTERS_PER_CLUB or len(away_ids) != STARTERS_PER_CLUB:
            raise ValueError("Se necesitan 3 titulares en cancha por club")
        if len(set(home_ids) | set(away_ids)) != 2 * STARTERS_PER_CLUB:
            raise ValueError("Hay jugadores repetidos")
        for name in (home_formation, away_formation):
            if name not in FORMATIONS:
                raise ValueError(f"Formación desconocida: {name}")
        positions: dict[str, Coordinate] = {}
        for player_id, (x, y) in zip(home_ids, FORMATIONS[home_formation]):
            positions[player_id] = (x, y)
        for player_id, (x, y) in zip(away_ids, FORMATIONS[away_formation]):
            positions[player_id] = (FIELD_WIDTH - x, y)  # espejado
        return cls(
            match_id=match_id,
            duration_minutes=duration_minutes,
            ball=Ball(FIELD_WIDTH / 2, FIELD_HEIGHT / 2),
            positions=positions,
        )

    def is_over(self) -> bool:
        """True cuando se alcanzó la duración configurada del partido."""
        return self.current_tick >= self.duration_minutes * TICKS_PER_MINUTE