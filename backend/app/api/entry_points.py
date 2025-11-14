import ipaddress

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EntryPoint, RouteAssignment
from ..schemas import EntryPointCreate, EntryPointOut, EntryPointUpdate
from ..security import get_current_user

router = APIRouter(prefix="/entry-points", tags=["entry-points"])


def _ensure_ip(value: str) -> None:
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:  # pragma: no cover - validation branch
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid IP address") from exc


@router.get("", response_model=list[EntryPointOut])
def list_entry_points(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[EntryPointOut]:
    return (
        db.query(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .order_by(EntryPoint.created_at.desc())
        .all()
    )


@router.post("", response_model=EntryPointOut, status_code=status.HTTP_201_CREATED)
def create_entry_point(
    payload: EntryPointCreate, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> EntryPointOut:
    _ensure_ip(payload.ip)

    entry_point = EntryPoint(
        user_id=user.id,
        name=payload.name,
        ip=payload.ip,
        ssh_port=payload.ssh_port,
        location=payload.location,
        status=payload.status,
    )
    db.add(entry_point)
    db.commit()
    db.refresh(entry_point)
    return entry_point


@router.put("/{entry_point_id}", response_model=EntryPointOut)
def update_entry_point(
    entry_point_id: int,
    payload: EntryPointUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> EntryPointOut:
    entry_point = (
        db.query(EntryPoint)
        .filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id)
        .first()
    )
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")

    data = payload.dict(exclude_unset=True)
    if "ip" in data:
        _ensure_ip(data["ip"])

    for field, value in data.items():
        setattr(entry_point, field, value)

    db.add(entry_point)
    db.commit()
    db.refresh(entry_point)
    return entry_point


@router.delete("/{entry_point_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry_point(
    entry_point_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> None:
    entry_point = (
        db.query(EntryPoint)
        .filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id)
        .first()
    )
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")

    # automatically remove assignments via cascade
    db.delete(entry_point)
    db.commit()


@router.get("/{entry_point_id}/routes", response_model=list[int])
def entry_point_routes(
    entry_point_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> list[int]:
    entry_point = (
        db.query(EntryPoint)
        .filter(EntryPoint.id == entry_point_id, EntryPoint.user_id == user.id)
        .first()
    )
    if not entry_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry point not found")

    assignments = (
        db.query(RouteAssignment)
        .filter(RouteAssignment.entry_point_id == entry_point.id)
        .all()
    )
    return [assignment.route_id for assignment in assignments]
