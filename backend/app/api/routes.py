import ipaddress
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EntryPoint, Route, RouteAssignment
from ..schemas import RouteCreate, RouteOut
from ..security import get_current_user

router = APIRouter(prefix="/routes", tags=["routes"])

_SUBDOMAIN_REGEX = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[A-Za-z]{2,63}$")


def _validate_subdomain(value: str) -> None:
    if not _SUBDOMAIN_REGEX.match(value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subdomain format")


def _validate_ip(value: str) -> None:
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:  # pragma: no cover - validation branch
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client IP") from exc


def _route_to_schema(route: Route, db: Session) -> RouteOut:
    assignment_ids = [assignment.entry_point_id for assignment in route.assignments]
    return RouteOut(
        id=route.id,
        subdomain=route.subdomain,
        client_ip=route.client_ip,
        client_port=route.client_port,
        protocol=route.protocol,
        use_haproxy=route.use_haproxy,
        created_at=route.created_at,
        entry_points=assignment_ids,
    )


@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[RouteOut]:
    routes = (
        db.query(Route)
        .filter(Route.user_id == user.id)
        .order_by(Route.created_at.desc())
        .all()
    )
    return [_route_to_schema(route, db) for route in routes]


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(
    payload: RouteCreate, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> RouteOut:
    _validate_subdomain(payload.subdomain)
    _validate_ip(payload.client_ip)

    if payload.protocol not in {"tcp", "udp", "tcp+udp"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported protocol")

    available_entry_points = (
        db.query(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .all()
    )
    available_ids = {entry_point.id for entry_point in available_entry_points}

    invalid_ids = [entry_id for entry_id in payload.entry_points if entry_id not in available_ids]
    if invalid_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown entry point selection")

    route = Route(
        user_id=user.id,
        subdomain=payload.subdomain,
        client_ip=payload.client_ip,
        client_port=payload.client_port,
        protocol=payload.protocol,
        use_haproxy=payload.use_haproxy,
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    assignments = [
        RouteAssignment(route_id=route.id, entry_point_id=entry_id) for entry_id in payload.entry_points
    ]
    db.add_all(assignments)
    db.commit()
    db.refresh(route)

    return _route_to_schema(route, db)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)) -> None:
    route = (
        db.query(Route)
        .filter(Route.id == route_id, Route.user_id == user.id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    db.delete(route)
    db.commit()


@router.put("/{route_id}", response_model=RouteOut)
def update_route(
    route_id: int,
    payload: RouteCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> RouteOut:
    route = (
        db.query(Route)
        .filter(Route.id == route_id, Route.user_id == user.id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    _validate_subdomain(payload.subdomain)
    _validate_ip(payload.client_ip)

    if payload.protocol not in {"tcp", "udp", "tcp+udp"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported protocol")

    available_entry_points = (
        db.query(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .all()
    )
    available_ids = {entry_point.id for entry_point in available_entry_points}
    invalid_ids = [entry_id for entry_id in payload.entry_points if entry_id not in available_ids]
    if invalid_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown entry point selection")

    route.subdomain = payload.subdomain
    route.client_ip = payload.client_ip
    route.client_port = payload.client_port
    route.protocol = payload.protocol
    route.use_haproxy = payload.use_haproxy

    db.query(RouteAssignment).filter(RouteAssignment.route_id == route.id).delete()
    db.add_all(
        [RouteAssignment(route_id=route.id, entry_point_id=entry_id) for entry_id in payload.entry_points]
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    return _route_to_schema(route, db)
