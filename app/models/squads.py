from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Squad(Base):
    """A club's squad. A club has exactly one, fully replaced on every
    PUT /clubs/me/squad."""
    __tablename__ = "squads"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[str] = mapped_column(ForeignKey("clubs.id"), unique=True)
    formation: Mapped[str] = mapped_column(String(20))

    members: Mapped[list["SquadMember"]] = relationship("SquadMember", cascade="all, delete-orphan")


class SquadMember(Base):
    """A player within the squad, with the behavior assigned to them
    and whether they are a starter or a substitute."""
    __tablename__ = "squad_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id"))
    club_player_id: Mapped[str] = mapped_column(ForeignKey("club_players.id"))
    behavior_id: Mapped[int] = mapped_column(ForeignKey("behaviors.id"))
    is_starter: Mapped[bool] = mapped_column()


class FriendlySquadMember(Base):
    """Snapshot de la plantilla de un club, congelada cuando un amistoso se
    inicia (al unirse el rival). Una fila por jugador.

    No se puede reutilizar Squad/SquadMember: Squad.club_id es único (un club,
    una plantilla) y la plantilla del club se sigue pudiendo editar mientras el
    partido está en curso; el partido tiene que seguir usando la del momento
    en que arrancó.

    Se ancla al Friendly y no al Match porque durante la cuenta regresiva el
    Match (la simulación) todavía no existe.

    Para armar `participants` del motor: filtrar por club_id (local =
    Friendly.home_club_id, visitante = away_club_id); titulares = is_starter,
    ordenados por id (el orden de inserción es el orden de la plantilla y define
    la posición dentro de la formación).
    """
    __tablename__ = "friendly_squad_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    friendly_id: Mapped[str] = mapped_column(ForeignKey("friendlies.id"), index=True)
    club_id: Mapped[str] = mapped_column(ForeignKey("clubs.id"))
    # Se repite en cada fila del club: es un snapshot, no hace falta normalizar.
    formation: Mapped[str] = mapped_column(String(20))
    club_player_id: Mapped[str] = mapped_column(ForeignKey("club_players.id"))
    behavior_id: Mapped[int] = mapped_column(ForeignKey("behaviors.id"))
    is_starter: Mapped[bool] = mapped_column()