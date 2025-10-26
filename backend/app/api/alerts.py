from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert
from ..schemas import AlertOut
from ..security import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Alert).filter(Alert.user_id == user.id).order_by(Alert.timestamp.desc()).all()


@router.post("/{alert_id}/read")
def mark_read(alert_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
    if alert:
        alert.read = True
        db.add(alert)
        db.commit()
    return {"detail": "Alert updated"}


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
    if alert:
        db.delete(alert)
        db.commit()
    return {"detail": "Alert removed"}
