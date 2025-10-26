from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DDoSLog, EntryPoint, Stat
from ..security import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.utcnow()
    traffic = (
        db.query(func.sum(Stat.traffic_in + Stat.traffic_out))
        .join(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .filter(Stat.timestamp >= now - timedelta(hours=1))
        .scalar()
        or 0
    )
    connections = (
        db.query(func.sum(Stat.connections))
        .join(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .filter(Stat.timestamp >= now - timedelta(hours=1))
        .scalar()
        or 0
    )
    entry_points_total = db.query(EntryPoint).filter(EntryPoint.user_id == user.id).count()
    entry_points_online = (
        db.query(EntryPoint)
        .filter(EntryPoint.user_id == user.id, EntryPoint.status == "online")
        .count()
    )
    ddos_blocked = (
        db.query(func.sum(DDoSLog.packets_blocked))
        .join(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .scalar()
        or 0
    )
    return {
        "traffic_gbps": round(traffic / 1_000_000_000, 2),
        "connections": int(connections),
        "entry_points": {"online": entry_points_online, "total": entry_points_total},
        "ddos_blocked": int(ddos_blocked),
        "timestamp": now,
    }


@router.get("/traffic")
def traffic(range: str = "1h", db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.utcnow()
    if range == "1h":
        interval = 5
        total_points = 12
    elif range == "24h":
        interval = 60
        total_points = 24
    else:
        interval = 6 * 60
        total_points = 28

    since = now - timedelta(minutes=interval * total_points)
    stats = (
        db.query(
            func.date_trunc('minute', Stat.timestamp).label('bucket'),
            func.sum(Stat.traffic_in + Stat.traffic_out).label('traffic'),
        )
        .join(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .filter(Stat.timestamp >= since)
        .group_by('bucket')
        .order_by('bucket')
        .all()
    )

    traffic_map = {row.bucket.replace(second=0, microsecond=0): row.traffic for row in stats}
    points = []
    current = since.replace(second=0, microsecond=0)
    while current <= now:
        points.append({
            "timestamp": current,
            "value": traffic_map.get(current, 0),
        })
        current += timedelta(minutes=interval)

    return {"range": range, "points": points[-total_points:]}


@router.get("/geo")
def geo(db: Session = Depends(get_db), user=Depends(get_current_user)):
    entry_points = db.query(EntryPoint.location, func.count(EntryPoint.id)).filter(EntryPoint.user_id == user.id).group_by(EntryPoint.location).all()
    counter = Counter()
    for location, count in entry_points:
        country = location.split(",")[-1].strip() if location else "Unknown"
        counter[country] += count
    return {
        "countries": [
            {"code": country.upper()[:2], "traffic": value}
            for country, value in counter.items()
        ]
    }


@router.get("/ddos")
def ddos(db: Session = Depends(get_db), user=Depends(get_current_user)):
    logs = (
        db.query(DDoSLog)
        .join(EntryPoint)
        .filter(EntryPoint.user_id == user.id)
        .order_by(DDoSLog.timestamp.desc())
        .limit(50)
        .all()
    )
    return {
        "attacks": [
            {
                "type": log.attack_type,
                "source": log.source_ip,
                "packets": log.packets_blocked,
                "timestamp": log.timestamp,
            }
            for log in logs
        ]
    }
