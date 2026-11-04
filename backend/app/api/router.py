from fastapi import APIRouter
from backend.app.api.endpoints import (
    system, scanner, photos, calendar, timeline, home, memories, highlights, collections, backup, tags
)

api_router = APIRouter(prefix="/api")
api_router.include_router(system.router)
api_router.include_router(scanner.router)
api_router.include_router(photos.router)
api_router.include_router(calendar.router)
api_router.include_router(timeline.router)
api_router.include_router(home.router)
api_router.include_router(memories.router)
api_router.include_router(highlights.router)
api_router.include_router(collections.router)
api_router.include_router(backup.router)
api_router.include_router(tags.router)
