from __future__ import annotations

from fastapi import APIRouter

from astro_content_agent.api.routes.health import router as health_router
from astro_content_agent.api.routes.astro import router as astro_router
from astro_content_agent.api.routes.strategy import router as strategy_router
from astro_content_agent.api.routes.drafts import router as drafts_router
from astro_content_agent.api.routes.publish import router as publish_router
from astro_content_agent.api.routes.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(astro_router, prefix="/astro", tags=["astro"])
api_router.include_router(strategy_router, prefix="/strategy", tags=["strategy"])
api_router.include_router(drafts_router, prefix="/drafts", tags=["drafts"])
api_router.include_router(publish_router, prefix="/publish", tags=["publish"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])

