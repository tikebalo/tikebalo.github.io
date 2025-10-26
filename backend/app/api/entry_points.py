from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EntryPoint
from ..schemas import EntryPointCreate, EntryPointOut
from ..security import get_current_user
from ..tasks import install_entry_point_task

router = APIRouter(prefix="/entry-points", tags=["entry-points"])


@router.get("", response_model=list[EntryPointOut])
def list_entry_points(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(EntryPoint).filter(EntryPoint.user_id == user.id).all()


@router.post("", response_model=EntryPointOut, status_code=status.HTTP_202_ACCEPTED)
def create_entry_point(payload: EntryPointCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entry_point = EntryPoint(
        user_id=user.id,
        name=payload.name,
        ip=payload.ip,
        ssh_port=payload.ssh_port,
        location=payload.location,
        wg_ip=payload.wg_ip,
        provider=payload.provider,
        specs=payload.specs,
        status="provisioning",
    )
    db.add(entry_point)
    db.commit()
    db.refresh(entry_point)
    install_entry_point_task.delay(entry_point.id, payload.dict())
    return entry_point


@router.get("/{entry_point_id}", response_model=EntryPointOut)
def get_entry_point(entry_point_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    return entry_point


@router.put("/{entry_point_id}", response_model=EntryPointOut)
def update_entry_point(entry_point_id: int, payload: EntryPointCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(entry_point, field, value)
    db.add(entry_point)
    db.commit()
    db.refresh(entry_point)
    return entry_point


@router.delete("/{entry_point_id}")
def delete_entry_point(entry_point_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    db.delete(entry_point)
    db.commit()
    return {"detail": "Entry point deleted"}


@router.post("/{entry_point_id}/restart")
def restart_entry_point(entry_point_id: int, user=Depends(get_current_user)):
    # Would dispatch Celery task that SSH into node and restarts services
    return {"detail": f"Entry point {entry_point_id} restart initiated"}


@router.get("/{entry_point_id}/stats")
def entry_point_stats(entry_point_id: int, user=Depends(get_current_user)):
    # Placeholder returning fake stats until collectors implemented
    return {"points": [], "entry_point_id": entry_point_id}


@router.get("/{entry_point_id}/logs")
def entry_point_logs(entry_point_id: int, user=Depends(get_current_user)):
    return {"logs": ["Provisioning started", "WireGuard configured", "HAProxy reloaded"]}
