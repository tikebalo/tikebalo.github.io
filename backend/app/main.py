from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import admin, alerts, auth, entry_points, routes, settings, stats
from .config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(entry_points.router, prefix=settings.api_v1_prefix)
app.include_router(routes.router, prefix=settings.api_v1_prefix)
app.include_router(stats.router, prefix=settings.api_v1_prefix)
app.include_router(alerts.router, prefix=settings.api_v1_prefix)
app.include_router(settings.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}
