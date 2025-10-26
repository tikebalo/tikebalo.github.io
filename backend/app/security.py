from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User
from .schemas import TokenPayload

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(subject: int, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def create_tokens(user_id: int) -> dict[str, str]:
    access = create_token(user_id, timedelta(minutes=settings.access_token_expire_minutes))
    refresh = create_token(user_id, timedelta(minutes=settings.refresh_token_expire_minutes))
    return {"access_token": access, "refresh_token": refresh}


def verify_password(plain: str, hashed: str) -> bool:
    return password_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        token_data = TokenPayload(**payload)
    except JWTError as exc:  # pragma: no cover - runtime validation
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*roles: str):
    def wrapper(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return wrapper
