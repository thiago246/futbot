from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.security import hash_password, create_access_token, verify_password
from app.core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.models.club import Club
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from app.schemas.user import UserOut
from app.schemas.club import ClubOut
from app.services import behavior_service


def register(db: Session, data: RegisterRequest) -> RegisterResponse:
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise EmailAlreadyExistsError()
    
    try:
        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            avatar=data.avatar,
        )
        db.add(user)
        db.flush()

        club = Club(nombre=data.club_nombre, user_id=user.id)
        db.add(club)


        behavior_service.seed_default_behaviors(db)
        behavior_service.assign_defaults_to_user(db, user)
        
        db.commit()
        db.refresh(user)
        db.refresh(club)

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al crear la cuenta y el club")

    token = create_access_token(user.id)

    return RegisterResponse(
        user=UserOut.model_validate(user),
        club=ClubOut.model_validate(club),
        token=token,
    )

def login(db: Session, data: LoginRequest) -> LoginResponse:
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise InvalidCredentialsError()

    token = create_access_token(user.id)
    
    return LoginResponse(
        token=token,
        userId=user.id
    )