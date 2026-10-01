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
