from pydantic import BaseModel, Field, ConfigDict


class ClubOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    nombre: str
    puntos_ranking: int = Field(alias="puntosRanking")