from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes.pages import router as pages_router
from app.api.routes.visualize import router as viz_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import SecurityHeadersMiddleware


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.app_name, docs_url="/docs" if settings.debug else None)
    # Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(o) for o in settings.cors_origins],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )
    # Static
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    # Routers
    app.include_router(pages_router)
    app.include_router(viz_router, prefix="/api")
    return app


app = create_app()
