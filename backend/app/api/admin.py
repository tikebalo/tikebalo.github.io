from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EntryPoint, Route, User
from ..schemas import UserOut
from ..security import require_role

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("owner", "admin"))])


@router.get("/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db)):
    return [UserOut.from_orm(user) for user in db.query(User).all()]


@router.get("/system-stats")
def system_stats(db: Session = Depends(get_db)):
    return {
        "users": db.query(User).count(),
        "entry_points": db.query(EntryPoint).count(),
        "routes": db.query(Route).count(),
    }


@router.post("/maintenance-mode")
def maintenance_mode(enabled: bool):
    return {"detail": f"Maintenance mode {'enabled' if enabled else 'disabled'}"}
