from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, PasswordResetToken, Subscription, User
from ..schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserOut,
)
from ..security import create_tokens, get_current_user, hash_password, verify_password
from ..tasks import dispatch_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> UserOut:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    subscription = Subscription(user_id=user.id, plan="free", limits={"entry_points": 3, "routes": 5})
    db.add(subscription)
    db.add(
        AuditLog(
            user_id=user.id,
            action="register",
            details={"email": user.email},
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    tokens = create_tokens(user.id)
    db.add(
        AuditLog(
            user_id=user.id,
            action="login",
            details={"success": True},
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()
    return Token(**tokens)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return {"detail": "If account exists a reset email was sent."}

    token_value = uuid4().hex
    token = PasswordResetToken(user_id=user.id, token=token_value, expires_at=datetime.utcnow() + timedelta(hours=1))
    db.add(token)
    db.commit()

    dispatch_password_reset_email.delay(user.email, token_value)
    return {"detail": "If account exists a reset email was sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == payload.token)
        .first()
    )
    if not token or token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    db.delete(token)
    db.add(
        AuditLog(
            user_id=user.id,
            action="reset_password",
            details={},
        )
    )
    db.commit()
    return {"detail": "Password updated"}


@router.post("/logout")
def logout(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    db.add(
        AuditLog(
            user_id=user.id,
            action="logout",
            details={},
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()
    return {"detail": "Token invalidated client-side."}


@router.get("/verify-email")
def verify_email(token: str) -> dict[str, str]:
    return {"detail": "Email verification is pending implementation"}
