from datetime import datetime, timedelta
from random import randint
from time import sleep
from typing import Iterable

from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from .celery_app import celery
from .database import SessionLocal
from .models import Alert, EntryPoint, EntryPointInstallEvent, Route, Stat

INSTALL_MESSAGES = {
    "connect_ssh": "Connected to server over SSH",
    "update_system": "System packages updated",
    "install_wireguard": "WireGuard installed and configured",
    "install_haproxy": "HAProxy installed",
    "install_nftables": "nftables rules prepared",
    "generate_keys": "WireGuard keys generated",
    "configure_mesh": "Mesh configuration rendered",
    "add_peers": "Existing peers updated",
    "apply_routes": "Routing rules synced",
    "start_services": "Services started successfully",
}

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
        events = (
            db.query(EntryPointInstallEvent)
            .filter(EntryPointInstallEvent.entry_point_id == entry_point_id)
            .order_by(EntryPointInstallEvent.created_at.asc())
            .all()
        )
        for event in events:
            event.status = "running"
            event.message = INSTALL_MESSAGES.get(event.stage, "Running")
            db.add(event)
            db.commit()
            sleep(0.1)
            event.status = "completed"
            db.add(event)
            db.commit()
        entry_point.status = "online"
        entry_point.wg_ip = payload.get("wg_ip") or f"10.0.0.{randint(2, 254)}"
        entry_point.last_seen = datetime.utcnow()
        db.add(entry_point)
        seed_stats(entry_point.id, db)
        db.add(
            Alert(
                user_id=entry_point.user_id,
                type="success",
                message=f"Entry point {entry_point.name} is now online",
            )
        )
        db.commit()
        logger.info("Entry point %s is online", entry_point_id)
    finally:
        db.close()


@celery.task(name="app.tasks.apply_routes_task")
def apply_routes_task(route_id: int):
    logger.info("Applying configuration for route %s", route_id)
    db: Session = SessionLocal()
    try:
        route = db.query(Route).get(route_id)
        if not route:
            logger.warning("Route %s not found", route_id)
            return
        if route.status == "paused":
            logger.info("Route %s paused, skipping deployment", route_id)
            return
        db.add(
            Alert(
                user_id=route.user_id,
                type="info",
                message=f"Route {route.subdomain} configuration synced to entry points",
            )
        )
        db.commit()
    finally:
        db.close()


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
            entry_point.last_seen = datetime.utcnow()
            if stat.cpu > 85:
                db.add(
                    Alert(
                        user_id=entry_point.user_id,
                        type="warning",
                        message=f"Entry point {entry_point.name} CPU at {stat.cpu}%",
                    )
                )
        db.commit()
    finally:
        db.close()


@celery.task(name="app.tasks.monitor_health_task")
def monitor_health_task():
    db: Session = SessionLocal()
    try:
        entry_points = db.query(EntryPoint).all()
        for entry_point in entry_points:
            if entry_point.status != "online" or (entry_point.last_seen and datetime.utcnow() - entry_point.last_seen > timedelta(minutes=2)):
                entry_point.status = "degraded"
                alert = Alert(
                    user_id=entry_point.user_id,
                    type="error",
                    message=f"Entry point {entry_point.name} offline",
                    read=False,
                    timestamp=datetime.utcnow(),
                )
                db.add(alert)
            else:
                entry_point.status = "online"
            db.add(entry_point)
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


@celery.task(name="app.tasks.dispatch_password_reset_email")
def dispatch_password_reset_email(email: str, token: str) -> None:
    logger.info("Password reset requested for %s token=%s", email, token)


@celery.task(name="app.tasks.restart_entry_point_services")
def restart_entry_point_services(entry_point_id: int) -> None:
    logger.info("Restarting services for entry point %s", entry_point_id)
    db: Session = SessionLocal()
    try:
        entry_point = db.query(EntryPoint).get(entry_point_id)
        if not entry_point:
            logger.error("Entry point %s not found", entry_point_id)
            return
        event = EntryPointInstallEvent(
            entry_point_id=entry_point.id,
            stage="restart_services",
            status="completed",
            message="Services restarted via control panel",
        )
        entry_point.last_seen = datetime.utcnow()
        db.add(event)
        db.add(
            Alert(
                user_id=entry_point.user_id,
                type="info",
                message=f"Restart command executed on {entry_point.name}",
            )
        )
        db.commit()
    finally:
        db.close()


def seed_stats(entry_point_id: int, db: Session, samples: int = 12) -> None:
    now = datetime.utcnow()
    for i in range(samples):
        db.add(
            Stat(
                entry_point_id=entry_point_id,
                cpu=randint(20, 60),
                ram=randint(30, 70),
                traffic_in=randint(50_000, 150_000),
                traffic_out=randint(50_000, 150_000),
                connections=randint(500, 5_000),
                timestamp=now - timedelta(minutes=5 * i),
            )
        )
