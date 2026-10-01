"""Primitivas creadas para generar comportamientos.

Son la interfaz pública que usa el código de los comportamientos. No calculan
nada: delegan en el jugador que el motor dejó como "actual" antes de llamar
a decidir(contexto). La lógica de física y reglas vive en la clase Jugador
del motor.
"""

from typing import Tuple

Coordenada = Tuple[float, float]
_jugador_actual = None


def _set_jugador_actual(jugador) -> None:
    """Uso interno del motor (REQ 14/15). No forma parte de la API para usuarios.

    `jugador` debe tener:
      - atributos: id, posicion, pacss (dict)
      - métodos: mover_hacia(destino), patear_hacia(destino), intentar_robar(rival_id)
    """
    global _jugador_actual
    _jugador_actual = jugador


def _get_jugador_actual():
    """Devuelve el jugador actual o falla con un mensaje claro si el motor no lo seteó."""
    if _jugador_actual is None:
        raise RuntimeError(
            "No hay jugador actual: el motor debe llamar a _set_jugador_actual() "
            "antes de ejecutar decidir()."
        )
    return _jugador_actual


def correr_hacia(destino: Coordenada) -> None:
    """El jugador se mueve hacia `destino` (coordenadas absolutas) teniendo en
    cuenta las PACSS del jugador (principalmente Speed) y la distancia a la
    que se encuentran las coordenadas"""
    _get_jugador_actual().mover_hacia(destino)


def patear(destino: Coordenada) -> None:
    """El jugador patea la pelota hacia `destino` (coordenadas absolutas)
    teniendo en cuenta las PACSS del jugador (principalmente Agility, Control y
    Power) y la distancia a la que se encuentra la pelota, dado que depende del
    control del jugador desde qué tan lejos de la pelota puede patear. Por ende
    solo puede patear si el atributo control lo permite.
    """
    _get_jugador_actual().patear_hacia(destino)


def robar_pelota_jugador(rival_id: str) -> None:
    """El jugador intenta robarle la pelota al rival `rival_id`. El motor calcula
    el resultado de la disputa de forma 100% determinística según los PACSS
    (Strength y Control) de ambos jugadores. No existe aleatoriedad. El motor
    resuelve el cálculo internamente.
    """
    _get_jugador_actual().intentar_robar(rival_id)