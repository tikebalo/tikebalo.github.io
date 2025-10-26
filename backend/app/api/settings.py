from fastapi import APIRouter, Depends

from ..schemas import SubscriptionOut
from ..security import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/profile")
def profile(user=Depends(get_current_user)):
    return {"email": user.email, "role": user.role, "timezone": "UTC+3"}


@router.put("/profile")
def update_profile(name: str | None = None, timezone: str | None = None, user=Depends(get_current_user)):
    return {"detail": "Profile updated", "name": name, "timezone": timezone}


@router.put("/password")
def update_password(new_password: str, user=Depends(get_current_user)):
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters")
    return {"detail": "Password updated"}


@router.post("/2fa/enable")
def enable_2fa(code: str, user=Depends(get_current_user)):
    return {"detail": "2FA enabled"}


@router.post("/api-keys/generate")
def generate_api_key(user=Depends(get_current_user)):
    return {"api_key": "anycast_" + str(user.id).zfill(6)}


@router.get("/audit-logs")
def audit_logs(user=Depends(get_current_user)):
    return {"logs": [{"action": "login", "timestamp": "2024-05-01T10:00:00Z"}]}


@router.put("/notifications")
def update_notifications(settings: dict, user=Depends(get_current_user)):
    return {"detail": "Notification preferences saved", "settings": settings}


@router.get("/subscription", response_model=SubscriptionOut)
def subscription(user=Depends(get_current_user)):
    return SubscriptionOut(plan="pro", limits={"entry_points": 20, "routes": 100}, expires_at=None)
