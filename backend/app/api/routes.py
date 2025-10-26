from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Route
from ..schemas import RouteCreate, RouteOut
from ..security import get_current_user
from ..tasks import apply_routes_task

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Route).filter(Route.user_id == user.id).all()


@router.post("", response_model=RouteOut, status_code=status.HTTP_202_ACCEPTED)
def create_route(payload: RouteCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
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
    apply_routes_task.delay(route.id)
    return route


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    return route


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
    apply_routes_task.delay(route.id)
    return route


@router.delete("/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id, Route.user_id == user.id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    db.delete(route)
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
    db.commit()
    apply_routes_task.delay(route.id)
    return {"detail": "Route resumed"}


@router.get("/{route_id}/check-dns")
def check_dns(route_id: int, user=Depends(get_current_user)):
    # In reality would run dig via Celery task and return propagation status
    return {"detail": "DNS propagated", "records": [{"type": "SRV", "value": "_game._tcp 0 5 25565 entry.anycast.net"}]}
