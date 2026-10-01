"""Primitivas creadas para generar comportamientos"""

from typing import Tuple

Coordenada = Tuple[float, float]

def correr_hacia(destino: Coordenada) -> None:
    """El jugador se mueve hacia `destino` (coordenadas absolutas) teniendo en
    cuenta las PACSS del jugador (principalmente Speed) y la distancia a la 
    que se encuentran las coordenadas"""
    ...


def patear(destino: Coordenada) -> None:
    """El jugador patea la pelota hacia `destino` (coordenadas absolutas) 
    tendiendo en cuenta las PACSS del jugador (principalmente Agility, Control y Power) y la distancia a la que
    se encuentra la pelota dado que depende del control del jugador desde que 
    tan lejos de la pelota puede patear. Por ende solo puede patear si el atributo control
    lo permite.
    """
    ...


def robar_pelota_jugador(rival_id: str) -> None:
    """
    El jugador intenta robarle la pelota al rival `rival_id`. El motor calcula el 
    resultado de la disputa de forma 100% determinística según los PACSS (Strength y Control) de ambos 
    jugadores. No existe aleatoriedad. El motor resuelve el cálculo internamente.
    """
    ...
