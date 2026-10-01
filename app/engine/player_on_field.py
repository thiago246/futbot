"""Adaptador entre un jugador en cancha y las primitivas de comportamiento. (REQ 15)

primitives.py (ya implementado) espera que `_jugador_actual` tenga estos tres
métodos, y los llama TAL CUAL:

    mover_hacia(destino), patear_hacia(destino), intentar_robar(rival_id)

Esos tres nombres están en español porque son un contrato ya fijado por ese
archivo (primitives._set_jugador_actual), no una decisión mía; el resto de esta
clase sigue la convención en inglés del motor.

Esta clase no decide nada (eso lo hace el código de comportamiento del usuario,
vía decidir(contexto)): solo aplica el efecto de cada primitiva sobre el
MatchState compartido, usando los atributos PACSS del jugador para la física.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.engine.match_state import FIELD_HEIGHT, FIELD_WIDTH, Coordinate, MatchState


ATTRIBUTE_FIELDS = ("strength", "control", "precision", "agility", "speed")


def read_attributes(player) -> dict[str, int]:
    """Lee las 5 PACSS directamente del jugador"""
    return {field: getattr(player, field) for field in ATTRIBUTE_FIELDS}

# constantes de física. 
BASE_SPEED = 0.5  # unidades/tick incluso con SPEED mínimo
SPEED_FACTOR = 0.03  # unidades/tick adicionales por punto de SPEED

KICK_BASE_RANGE = 2.0  # distancia máx. a la pelota para patear, con CONTROL mínimo
KICK_RANGE_FACTOR = 0.03  # unidades adicionales por punto de CONTROL


def control_range(attributes: dict[str, int]) -> float:
    """Distancia máxima a la pelota dentro de la cual un jugador la controla"""
    return KICK_BASE_RANGE + attributes["control"] * KICK_RANGE_FACTOR

KICK_BASE_SPEED = 2.0  # velocidad mínima que toma la pelota al ser pateada
KICK_SPEED_FACTOR = 0.05  # velocidad adicional por punto de (AGILITY+CONTROL+PRECISION)/3


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class PlayerOnField:
    """Un jugador en cancha durante la simulación"""

    player_id: str
    attributes_by_player: dict[str, dict[str, int]]
    state: MatchState

    @property
    def attributes(self) -> dict[str, int]:
        return self.attributes_by_player[self.player_id]

    @property
    def position(self) -> Coordinate:
        return self.state.positions[self.player_id]

    @position.setter
    def position(self, value: Coordinate) -> None:
        self.state.positions[self.player_id] = value

    # ---------------------------------------------------- primitivas (español)
    def mover_hacia(self, destino: Coordinate) -> None:
        """Se mueve hacia `destino` una distancia por tick según SPEED"""
        x, y = self.position
        dx, dy = destino[0] - x, destino[1] - y
        distancia = math.hypot(dx, dy)
        if distancia == 0:
            return
        paso = min(BASE_SPEED + self.attributes["speed"] * SPEED_FACTOR, distancia)
        nx = _clamp(x + dx / distancia * paso, 0.0, FIELD_WIDTH)
        ny = _clamp(y + dy / distancia * paso, 0.0, FIELD_HEIGHT)
        self.position = (nx, ny)

    def patear_hacia(self, destino: Coordinate) -> None:
        """Patea la pelota hacia `destino` si está dentro del alcance que permite
        CONTROL; si no, la primitiva no tiene efecto (no puede patear)."""
        ball = self.state.ball
        px, py = self.position
        distancia_pelota = math.hypot(ball.x - px, ball.y - py)
        if distancia_pelota > control_range(self.attributes):
            return
        dx, dy = destino[0] - ball.x, destino[1] - ball.y
        distancia = math.hypot(dx, dy)
        if distancia == 0:
            return
        potencia = (
            self.attributes["agility"] + self.attributes["control"] + self.attributes["precision"]
        ) / 3
        velocidad = KICK_BASE_SPEED + potencia * KICK_SPEED_FACTOR
        ball.vx, ball.vy = dx / distancia * velocidad, dy / distancia * velocidad

    def intentar_robar(self, rival_id: str) -> None:
        """Disputa determinística por STRENGTH + CONTROL contra el rival. Si el
        jugador gana, la pelota pasa a su posición y queda detenida."""
        if rival_id not in self.attributes_by_player:
            return
        propio = self.attributes
        rival = self.attributes_by_player[rival_id]
        # gana quien tenga más STRENGTH+CONTROL; en caso de empate,
        # se queda con la pelota quien la tenía.
        if propio["strength"] + propio["control"] > rival["strength"] + rival["control"]:
            self.state.ball.x, self.state.ball.y = self.position
            self.state.ball.vx = self.state.ball.vy = 0.0