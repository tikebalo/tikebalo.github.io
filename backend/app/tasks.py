from datetime import datetime, timedelta
from random import randint

from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from .celery_app import celery
from .database import SessionLocal
from .models import Alert, EntryPoint, Route, Stat

logger = get_task_logger(__name__)


@celery.task(name="app.tasks.install_entry_point_task")
def install_entry_point_task(entry_point_id: int, payload: dict):
    logger.info("Installing entry point %s", entry_point_id)
    db: Session = SessionLocal()
    try:
        entry_point = db.query(EntryPoint).get(entry_point_id)
        if not entry_point:
            logger.error("Entry point %s not found", entry_point_id)
            return
        entry_point.status = "online"
        entry_point.wg_ip = payload.get("wg_ip") or f"10.0.0.{randint(2, 254)}"
        db.add(entry_point)
        db.commit()
        logger.info("Entry point %s is online", entry_point_id)
    finally:
        db.close()


@celery.task(name="app.tasks.apply_routes_task")
def apply_routes_task(route_id: int):
    logger.info("Applying configuration for route %s", route_id)


@celery.task(name="app.tasks.collect_stats_task")
def collect_stats_task():
    db: Session = SessionLocal()
    try:
        entry_points = db.query(EntryPoint).all()
        for entry_point in entry_points:
            stat = Stat(
                entry_point_id=entry_point.id,
                cpu=randint(10, 90),
                ram=randint(10, 90),
                traffic_in=randint(10_000, 100_000),
                traffic_out=randint(10_000, 100_000),
                connections=randint(100, 10_000),
            )
            db.add(stat)
        db.commit()
    finally:
        db.close()


@celery.task(name="app.tasks.monitor_health_task")
def monitor_health_task():
    db: Session = SessionLocal()
    try:
        entry_points = db.query(EntryPoint).all()
        for entry_point in entry_points:
            if entry_point.status != "online":
                alert = Alert(
                    user_id=entry_point.user_id,
                    type="error",
                    message=f"Entry point {entry_point.name} offline",
                    read=False,
                    timestamp=datetime.utcnow(),
                )
                db.add(alert)
        db.commit()
    finally:
        db.close()


@celery.task(name="app.tasks.cleanup_old_stats")
def cleanup_old_stats():
    cutoff = datetime.utcnow() - timedelta(days=30)
    db: Session = SessionLocal()
    try:
        deleted = db.query(Stat).filter(Stat.timestamp < cutoff).delete()
        logger.info("Removed %s old stat rows", deleted)
        db.commit()
    finally:
        db.close()
