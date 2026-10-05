from pydantic import BaseModel, field_validator
from typing import Optional
from app.core.exceptions import MatchDurationNotAllowed


class LeagueCreateSchema(BaseModel):
    nombre: str
    esPrivada: bool
    password: Optional[str] = None
    minEquipos: int
    maxEquipos: int
    duracionPartido: int

    @field_validator("duracionPartido")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v not in (1, 3, 5):
            raise MatchDurationNotAllowed
        return v


class LeagueResponseSchema(BaseModel):
    id: str
    nombre: str
    esPrivada: bool
    minEquipos: int
    maxEquipos: int
    duracionPartido: int
    estado: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_league(cls, league: object) -> "LeagueResponseSchema":
        return cls(
            id=league.id,
            nombre=league.nombre,
            esPrivada=league.is_private,
            minEquipos=league.min_teams,
            maxEquipos=league.max_teams,
            duracionPartido=league.match_duration,
            estado=league.status,
        )


class LeagueListItemSchema(LeagueResponseSchema):
    equiposActuales: int = 0

    @classmethod
    def from_league_count(cls, league: object, count: int) -> "LeagueListItemSchema":
        base = LeagueResponseSchema.from_league(league)
        return cls(**base.model_dump(), equiposActuales=count)


class LeagueJoinSchema(BaseModel):
    password: Optional[str] = None


class PaginatedLeaguesSchema(BaseModel):
    items: list[LeagueListItemSchema]
    page: int
    pageSize: int
    total: int


class LobbyClubSchema(BaseModel):
    clubId: str
    nombre: str


class LeagueLobbyOut(BaseModel):
    """'Imagen' del lobby de espera: la liga, los clubes inscriptos y los cupos que quedan."""
    id: str
    nombre: str
    estado: str
    minEquipos: int
    maxEquipos: int
    equiposActuales: int
    cuposRestantes: int
    listaParaIniciar: bool  # equiposActuales >= minEquipos
    equipos: list[LobbyClubSchema]