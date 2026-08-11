from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)


def _user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _build_token_response(user: User) -> TokenResponse:
    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )


def register(db: Session, payload: RegisterRequest) -> TokenResponse:
    exists = db.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email)
        )
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_token_response(user)


def login(db: Session, payload: LoginRequest) -> TokenResponse:
    user = db.scalar(
        select(User).where(
            or_(User.username == payload.account, User.email == payload.account)
        )
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )
    return _build_token_response(user)


def get_me(db: Session, user_id: int) -> UserOut:
    user = _user_or_404(db, user_id)
    return UserOut.model_validate(user)


def update_me(db: Session, user_id: int, payload: dict) -> UserOut:
    user = _user_or_404(db, user_id)
    for key, value in payload.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


def change_password(db: Session, user_id: int, old: str, new: str) -> None:
    user = _user_or_404(db, user_id)
    if not verify_password(old, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password incorrect",
        )
    user.password_hash = hash_password(new)
    db.commit()
