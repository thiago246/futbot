from pydantic import BaseModel, ConfigDict, Field

VALID_FORMATIONS = {"1-2", "2-1"} 


class SquadMemberInput(BaseModel):
    club_player_id: str
    behavior_id: int


class SquadInput(BaseModel):
    formation: str
    starters: list[SquadMemberInput] = Field(min_length=3, max_length=3)
    substitutes: list[SquadMemberInput] = Field(min_length=3, max_length=3)


class SquadMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    club_player_id: str
    behavior_id: int
    is_starter: bool


class SquadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    formation: str
    members: list[SquadMemberOut]