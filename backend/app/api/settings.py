from secrets import token_hex

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, Subscription, User
from ..schemas import AuditLogOut, NotificationSettings, ProfileUpdate, SubscriptionOut, UserOut
from ..security import get_current_user, hash_password

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/profile", response_model=UserOut)
def profile(user=Depends(get_current_user)):
    return UserOut.from_orm(user)


@router.put("/profile", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        db_user.full_name = payload.full_name
    if payload.timezone is not None:
        db_user.timezone = payload.timezone
    if payload.avatar_url is not None:
        db_user.avatar_url = payload.avatar_url
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserOut.from_orm(db_user)


@router.put("/password")
def update_password(new_password: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    return {"detail": "Password updated"}


@router.post("/2fa/enable")
def enable_2fa(code: str, user=Depends(get_current_user)):
    return {"detail": "2FA enabled"}


@router.post("/api-keys/generate")
def generate_api_key(db: Session = Depends(get_db), user=Depends(get_current_user)):
    api_key = f"anycast_{token_hex(16)}"
    user.api_key = api_key
    db.add(user)
    db.commit()
    return {"api_key": api_key}


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user.id)
        .order_by(AuditLog.timestamp.desc())
        .limit(50)
        .all()
    )
    return [AuditLogOut.from_orm(log) for log in logs]


@router.put("/notifications", response_model=NotificationSettings)
def update_notifications(
    settings: NotificationSettings,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    user.notification_settings = settings.dict()
    db.add(user)
    db.commit()
    return settings


@router.get("/subscription", response_model=SubscriptionOut)
def subscription(db: Session = Depends(get_db), user=Depends(get_current_user)):
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id, plan="free", limits={"entry_points": 3, "routes": 5})
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    return SubscriptionOut.from_orm(subscription)
