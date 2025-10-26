from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, EntryPoint, EntryPointInstallEvent, Stat
from ..schemas import (
    EntryPointCreate,
    EntryPointDetail,
    EntryPointInstallEventOut,
    EntryPointOut,
    EntryPointUpdate,
    StatOut,
)
from ..security import get_current_user
from ..tasks import install_entry_point_task, restart_entry_point_services

router = APIRouter(prefix="/entry-points", tags=["entry-points"])


@router.get("", response_model=list[EntryPointOut])
def list_entry_points(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .order_by(EntryPoint.created_at.desc())
        .all()
    )


@router.post("", response_model=EntryPointOut, status_code=status.HTTP_202_ACCEPTED)
def create_entry_point(
    payload: EntryPointCreate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
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
    stages = [
        "connect_ssh",
        "update_system",
        "install_wireguard",
        "install_haproxy",
        "install_nftables",
        "generate_keys",
        "configure_mesh",
        "add_peers",
        "apply_routes",
        "start_services",
    ]
    for stage in stages:
        db.add(
            EntryPointInstallEvent(
                entry_point_id=entry_point.id,
                stage=stage,
                status="pending",
            )
        )
    db.add(
        AuditLog(
            user_id=user.id,
            action="entry_point:create",
            details={"entry_point_id": entry_point.id, "name": entry_point.name},
        )
    )
    db.commit()
    install_entry_point_task.delay(entry_point.id, payload.dict())
    return entry_point


@router.get("/{entry_point_id}", response_model=EntryPointDetail)
def get_entry_point(
    entry_point_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    stats = (
        db.query(Stat)
        .filter(Stat.entry_point_id == entry_point.id)
        .order_by(Stat.timestamp.desc())
        .limit(50)
        .all()
    )
    install_events = (
        db.query(EntryPointInstallEvent)
        .filter(EntryPointInstallEvent.entry_point_id == entry_point.id)
        .order_by(EntryPointInstallEvent.created_at.asc())
        .all()
    )
    route_ids = [assignment.route_id for assignment in entry_point.routes]
    return EntryPointDetail(
        **EntryPointOut.from_orm(entry_point).dict(),
        stats=[StatOut.from_orm(stat) for stat in stats],
        install_events=[EntryPointInstallEventOut.from_orm(event) for event in install_events],
        routes=route_ids,
    )


@router.put("/{entry_point_id}", response_model=EntryPointOut)
def update_entry_point(
    entry_point_id: int,
    payload: EntryPointUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(entry_point, field, value)
    entry_point.last_seen = datetime.utcnow()
    db.add(entry_point)
    db.commit()
    db.refresh(entry_point)
    return entry_point


@router.delete("/{entry_point_id}")
def delete_entry_point(
    entry_point_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    db.delete(entry_point)
    db.add(
        AuditLog(
            user_id=user.id,
            action="entry_point:delete",
            details={"entry_point_id": entry_point_id},
        )
    )
    db.commit()
    return {"detail": "Entry point deleted"}


@router.post("/{entry_point_id}/restart")
def restart_entry_point(
    entry_point_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    restart_entry_point_services.delay(entry_point_id)
    db.add(
        AuditLog(
            user_id=user.id,
            action="entry_point:restart",
            details={"entry_point_id": entry_point_id},
        )
    )
    db.commit()
    return {"detail": f"Entry point {entry_point_id} restart initiated"}


@router.get("/{entry_point_id}/stats")
def entry_point_stats(
    entry_point_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    stats = (
        db.query(Stat)
        .filter(Stat.entry_point_id == entry_point_id)
        .order_by(Stat.timestamp.desc())
        .limit(288)
        .all()
    )
    return {
        "entry_point_id": entry_point_id,
        "points": [StatOut.from_orm(point).dict() for point in reversed(stats)],
    }


@router.get("/{entry_point_id}/logs")
def entry_point_logs(
    entry_point_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    events = (
        db.query(EntryPointInstallEvent)
        .filter(EntryPointInstallEvent.entry_point_id == entry_point_id)
        .order_by(EntryPointInstallEvent.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "logs": [
            {
                "stage": event.stage,
                "status": event.status,
                "message": event.message,
                "timestamp": event.created_at,
            }
            for event in events
        ]
    }


@router.get("/{entry_point_id}/install-events", response_model=list[EntryPointInstallEventOut])
def install_events(
    entry_point_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entry_point = db.query(EntryPoint).filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id).first()
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")
    events = (
        db.query(EntryPointInstallEvent)
        .filter(EntryPointInstallEvent.entry_point_id == entry_point_id)
        .order_by(EntryPointInstallEvent.created_at.asc())
        .all()
    )
    return [EntryPointInstallEventOut.from_orm(event) for event in events]
