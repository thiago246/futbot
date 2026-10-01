from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.user import UserOut
from app.schemas.club import ClubOut
from typing import Optional

class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: str
    email: EmailStr
    password: str = Field(min_length=8)
    avatar: str
    club_nombre: str = Field(alias="clubNombre")

class RegisterResponse(BaseModel):
    user: UserOut
    club: ClubOut
    token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    userId: str