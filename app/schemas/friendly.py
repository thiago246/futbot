"""Formatos de amistosos. (REQ 11 a 14)

Los campos están en inglés, pero el JSON de entrada/salida conserva los nombres
del contrato (schema Match) mediante alias.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
# Valores del schema Match del query param `estado` de GET /matches.
FriendlyStatus = Literal[
    "esperando_rival", "programado", "cuenta_regresiva", "en_curso", "pausado", "finalizado"
]
FriendlyKind = Literal["amistoso", "liga"]

class FriendlyCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    # Usamos int (y no Literal[1, 3, 5]): el service valida y responde
    # 422 INVALID_DURATION con el formato de error del contrato.
    duration: int = Field(alias="duracion")

class FriendlyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    kind: str = Field(alias="tipo")
    status: str = Field(alias="estado")
    home_club_id: str = Field(alias="clubLocalId")
    away_club_id: str | None = Field(default=None, alias="clubVisitanteId")
    home_score: int = Field(alias="resultadoLocal")
    away_score: int = Field(alias="resultadoVisitante")
    duration: int = Field(alias="duracion")
    remaining_substitutions: int = Field(alias="sustitucionesRestantes")

class PaginatedFriendlies(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[FriendlyOut]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int