from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from astro_content_agent.api.router import api_router
from astro_content_agent.core.config import get_settings
from astro_content_agent.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    scheduler_svc = None

    if settings.scheduler_enabled:
        from astro_content_agent.db.session import SessionLocal
        from astro_content_agent.services.jobs.scheduler import build_scheduler

        scheduler_svc = build_scheduler(settings=settings, db_factory=SessionLocal)
        scheduler_svc.start()

    yield

    if scheduler_svc is not None:
        scheduler_svc.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="astro-content-agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(api_router)
    app.include_router(api_router, prefix="/api/v1")

    # Serve local assets at /media/<key> for development.
    # In production, replace with a CDN or cloud storage public URL.
    if settings.storage_mode == "local":
        assets_path = Path(settings.assets_dir)
        assets_path.mkdir(parents=True, exist_ok=True)
        app.mount("/media", StaticFiles(directory=str(assets_path)), name="media")

    # Minimal operator UI: static review console (uses existing admin + drafts APIs).
    _console_dir = Path(__file__).resolve().parent / "static" / "operator_review"

    @app.get("/operator/review", include_in_schema=False)
    def operator_review_console() -> FileResponse:
        return FileResponse(_console_dir / "index.html", media_type="text/html")

    app.mount(
        "/operator/review/static",
        StaticFiles(directory=str(_console_dir)),
        name="operator_review_static",
    )

    return app


app = create_app()
