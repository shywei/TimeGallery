import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.exceptions import AppException
from backend.app.db.database import init_db
from backend.app.api.router import api_router

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Growing Up backend...")
    init_db()
    logger.info("Database schema initialized.")
    yield
    logger.info("Growing Up backend shutting down.")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS Middleware (especially useful during frontend Vite dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Custom Exception Handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"AppException: {exc.code} - {exc.message} (details: {exc.details})")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

# Mount API Router
app.include_router(api_router)

# Mount Frontend Dist & SPA Fallback
frontend_dist = settings.base_dir / "frontend" / "dist"

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If static file directly exists in dist
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Fallback to index.html for client-side routing
        index_file = frontend_dist / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"message": "Frontend not built yet."})
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.app_name,
            "status": "ready",
            "message": "Backend API is running. Build frontend for production UI."
        }
