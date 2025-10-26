from celery import Celery

from .config import get_settings

settings = get_settings()

celery = Celery(
    "anycast",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.task_routes = {
    "app.tasks.install_entry_point_task": {"queue": "provision"},
    "app.tasks.apply_routes_task": {"queue": "config"},
    "app.tasks.collect_stats_task": {"queue": "metrics"},
    "app.tasks.monitor_health_task": {"queue": "health"},
}
