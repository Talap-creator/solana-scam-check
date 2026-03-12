from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.admin import router as admin_router
from .api.routes.auth import router as auth_router
from .api.routes.checks import router as checks_router
from .api.routes.feed import router as feed_router
from .api.routes.health import router as health_router
from .api.routes.overview import router as overview_router
from .api.routes.v2_scan import router as v2_scan_router
from .api.routes.watchlist import router as watchlist_router
from .db import init_db
from .dependencies import settings


app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(overview_router)
app.include_router(checks_router)
app.include_router(feed_router)
app.include_router(watchlist_router)
app.include_router(admin_router)
app.include_router(v2_scan_router)
