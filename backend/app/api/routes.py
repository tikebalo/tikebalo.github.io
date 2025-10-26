import socket
from contextlib import closing
from typing import Iterable

import dns.resolver
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, EntryPoint, Route, RouteAssignment
from ..schemas import RouteCreate, RouteOut
from ..security import get_current_user
from ..tasks import apply_routes_task

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    routes = db.query(Route).filter(Route.user_id == user.id).all()
    return [serialize_route(route) for route in routes]


@router.post("", response_model=RouteOut, status_code=status.HTTP_202_ACCEPTED)
def create_route(payload: RouteCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if db.query(Route).filter(Route.user_id == user.id, Route.subdomain == payload.subdomain).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Route with this subdomain already exists")

    if not is_valid_hostname(payload.subdomain):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subdomain")

    if payload.protocol.upper() in {"TCP", "TCP+UDP"}:
        if not probe_tcp(payload.client_ip, payload.client_port):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target server is unreachable over TCP")

    route = Route(
        user_id=user.id,
        subdomain=payload.subdomain,
        client_ip=payload.client_ip,
        client_port=payload.client_port,
        protocol=payload.protocol,
        use_haproxy=payload.use_haproxy,
        settings={"ddos_level": payload.ddos_level, "rate_limit": payload.rate_limit},
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    attach_entry_points(route, payload.entry_points, db)
    db.add(
        AuditLog(
            user_id=user.id,
            action="route:create",
            details={"route_id": route.id, "subdomain": route.subdomain},
        )
    )
    db.commit()
    db.refresh(route)
    apply_routes_task.delay(route.id)
    return serialize_route(route)


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    return serialize_route(route)


@router.put("/{route_id}", response_model=RouteOut)
def update_route(route_id: int, payload: RouteCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    for field, value in payload.dict(exclude_unset=True).items():
        if field in {"ddos_level", "rate_limit"}:
            route.settings = route.settings or {}
            route.settings[field] = value
        elif hasattr(route, field):
            setattr(route, field, value)
    db.add(route)
    db.commit()
    db.refresh(route)
    attach_entry_points(route, payload.entry_points, db, replace=True)
    db.add(
        AuditLog(
            user_id=user.id,
            action="route:update",
            details={"route_id": route.id},
        )
    )
    db.commit()
    db.refresh(route)
    apply_routes_task.delay(route.id)
    return serialize_route(route)


@router.delete("/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    db.delete(route)
    db.add(
        AuditLog(
            user_id=user.id,
            action="route:delete",
            details={"route_id": route_id},
        )
    )
    db.commit()
    apply_routes_task.delay(route_id)
    return {"detail": "Route removed"}


@router.post("/{route_id}/pause")
def pause_route(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    route.status = "paused"
    db.add(route)
    db.add(
        AuditLog(
            user_id=user.id,
            action="route:pause",
            details={"route_id": route.id},
        )
    )
    db.commit()
    apply_routes_task.delay(route.id)
    return {"detail": "Route paused"}


@router.post("/{route_id}/resume")
def resume_route(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    route.status = "active"
    db.add(route)
    db.add(
        AuditLog(
            user_id=user.id,
            action="route:resume",
            details={"route_id": route.id},
        )
    )
    db.commit()
    apply_routes_task.delay(route.id)
    return {"detail": "Route resumed"}


@router.get("/{route_id}/check-dns")
def check_dns(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    records = []
    try:
        answers = dns.resolver.resolve(route.subdomain, "A")
        records.extend({"type": "A", "value": answer.to_text()} for answer in answers)
    except Exception:  # pragma: no cover - depends on DNS availability
        records.append({"type": "A", "value": "pending"})

    try:
        srv_name = f"_{route.protocol.lower()}._tcp.{route.subdomain}".rstrip(".")
        answers = dns.resolver.resolve(srv_name, "SRV")
        records.extend({"type": "SRV", "value": answer.to_text()} for answer in answers)
    except Exception:  # pragma: no cover - depends on DNS availability
        records.append({"type": "SRV", "value": "pending"})

    return {"detail": "DNS lookup complete", "records": records, "instructions": dns_instructions(route)}


def attach_entry_points(route: Route, entry_points: Iterable[int] | None, db: Session, replace: bool = False) -> None:
    if entry_points is None:
        return
    valid_ids = {ep.id for ep in db.query(EntryPoint).filter(EntryPoint.user_id == route.user_id, EntryPoint.status == "online").all()}
    missing = [ep_id for ep_id in entry_points if ep_id not in valid_ids]
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Entry points {missing} are not online or do not belong to you")

    if replace:
        db.query(RouteAssignment).filter(RouteAssignment.route_id == route.id).delete()

    existing = {
        assignment.entry_point_id
        for assignment in db.query(RouteAssignment).filter(RouteAssignment.route_id == route.id).all()
    }
    for entry_point_id in entry_points:
        if entry_point_id in existing:
            continue
        db.add(RouteAssignment(route_id=route.id, entry_point_id=entry_point_id))


def serialize_route(route: Route) -> RouteOut:
    return RouteOut(
        id=route.id,
        subdomain=route.subdomain,
        client_ip=route.client_ip,
        client_port=route.client_port,
        protocol=route.protocol,
        use_haproxy=route.use_haproxy,
        status=route.status,
        created_at=route.created_at,
        settings=route.settings,
        entry_points=[assignment.entry_point_id for assignment in route.assignments],
    )


def is_valid_hostname(hostname: str) -> bool:
    if len(hostname) > 253:
        return False
    labels = hostname.rstrip(".").split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > 63:
            return False
        if label.startswith("-") or label.endswith("-"):
            return False
        if not label.replace("-", "").isalnum():
            return False
    return True


def probe_tcp(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except OSError:
        return False


def dns_instructions(route: Route) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    records.append({
        "type": "A",
        "name": route.subdomain,
        "value": "<ENTRY_POINT_PUBLIC_IP>",
        "ttl": "120",
    })
    if route.protocol.upper() in {"TCP", "TCP+UDP"}:
        records.append(
            {
                "type": "SRV",
                "name": f"_{route.protocol.lower()}._tcp.{route.subdomain}",
                "value": f"1 1 {route.client_port} {route.subdomain}",
                "ttl": "120",
            }
        )
    return records
