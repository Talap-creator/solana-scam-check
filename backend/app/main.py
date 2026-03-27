from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.admin import router as admin_router
from .api.routes.auth import router as auth_router
from .api.routes.billing import router as billing_router
from .api.routes.checks import router as checks_router
from .api.routes.feed import router as feed_router
from .api.routes.health import router as health_router
from .api.routes.oracle import router as oracle_router
from .api.routes.overview import router as overview_router
from .api.routes.v2_scan import router as v2_scan_router
from .api.routes.watchlist import router as watchlist_router
from .db import get_db, init_db
from .dependencies import get_repository, settings
from .services.oracle_agent import init_oracle_agent
from .services.solana_publisher import SolanaPublisher


app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def apply_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), browsing-topics=()",
    )
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if request.url.scheme == "https" or forwarded_proto == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/admin"):
        response.headers.setdefault("Cache-Control", "no-store")

    return response


@app.on_event("startup")
def startup_event() -> None:
    init_db()

    # Initialize Oracle Agent
    import os
    publisher = SolanaPublisher(
        program_id=os.getenv("ORACLE_PROGRAM_ID", "HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS"),
        publisher_keypair_path=os.getenv("ORACLE_PUBLISHER_KEYPAIR"),
        rpc_url=os.getenv("ORACLE_RPC_URL", "https://api.devnet.solana.com"),
    )
    init_oracle_agent(
        settings=settings,
        publisher=publisher,
        get_db=get_db,
        get_repository=get_repository,
    )


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(overview_router)
app.include_router(checks_router)
app.include_router(feed_router)
app.include_router(watchlist_router)
app.include_router(admin_router)
app.include_router(v2_scan_router)
app.include_router(oracle_router)
