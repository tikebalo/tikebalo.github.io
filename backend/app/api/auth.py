from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import Token, UserCreate, UserOut
from ..security import create_tokens, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    tokens = create_tokens(user.id)
    return Token(**tokens)


@router.post("/forgot-password")
def forgot_password(email: str) -> dict[str, str]:
    # Placeholder for emailing logic handled by Celery task.
    return {"detail": "If account exists a reset email was sent."}


@router.post("/reset-password")
def reset_password(token: str, new_password: str) -> dict[str, str]:
    # Placeholder for verifying token and updating password.
    if len(new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password too short")
    return {"detail": "Password updated"}


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"detail": "Token invalidated client-side."}


@router.get("/verify-email")
def verify_email(token: str) -> dict[str, str]:
    return {"detail": "Email verification is pending implementation"}
