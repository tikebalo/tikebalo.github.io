from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from ..security import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def overview(user=Depends(get_current_user)):
    now = datetime.utcnow()
    return {
        "traffic_gbps": 182.4,
        "connections": 12482,
        "entry_points": {"online": 14, "total": 15},
        "ddos_blocked": 328,
        "timestamp": now,
    }


@router.get("/traffic")
def traffic(range: str = "1h", user=Depends(get_current_user)):
    points = 60 if range == "1h" else 24 if range == "24h" else 7
    return {
        "range": range,
        "points": [
            {
                "timestamp": datetime.utcnow() - timedelta(minutes=i * (60 // max(points, 1))),
                "value": 150 + i,
            }
            for i in range(points)
        ][::-1],
    }


@router.get("/geo")
def geo(user=Depends(get_current_user)):
    return {"countries": [{"code": "RU", "traffic": 24}, {"code": "DE", "traffic": 18}, {"code": "US", "traffic": 16}]}


@router.get("/ddos")
def ddos(user=Depends(get_current_user)):
    return {
        "attacks": [
            {"type": "SYN flood", "source": "45.134.22.1", "packets": 2300000},
            {"type": "UDP amp", "source": "103.23.5.21", "packets": 1100000},
        ]
    }
