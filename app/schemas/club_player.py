from pydantic import BaseModel, model_validator
from typing import Self
from app.core.exceptions import AttributeSumInvalidError, AttributeOutOfRangeError

class StatsSchema(BaseModel):
    strength: int
    control: int
    precision: int
    agility: int
    speed: int

    @model_validator(mode="after")
    def validate_stats(self) -> Self:
        values = [self.strength, self.control, self.precision, self.agility, self.speed]
        if any(v < 20 or v > 100 for v in values):
            raise AttributeOutOfRangeError
        if sum(values) != 300:
            raise AttributeSumInvalidError
        return self


class PlayerCreateSchema(BaseModel):
    name: str
    stats: StatsSchema


class PlayerResponseSchema(BaseModel):
    id: str
    name: str
    stats: StatsSchema

    model_config = {"from_attributes": True}

    @classmethod
    def from_player(cls, player: object) -> "PlayerResponseSchema":
        return cls(
            id=player.id,
            name=player.name,
            stats=StatsSchema(
                strength=player.strength,
                control=player.control,
                precision=player.precision,
                agility=player.agility,
                speed=player.speed,
            )
        )