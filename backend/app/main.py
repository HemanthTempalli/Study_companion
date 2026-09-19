"""FastAPI main application — AI Study Companion backend."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.workers.runner import run_worker

from app.core.config import settings, validate_settings
from app.routers import auth, spaces, projects, materials, tutor, quiz, mastery, recommendations, analytics, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    issues = validate_settings()
    for issue in issues:
        logger.warning(f"⚠️  {issue}")
    logger.info("🚀 AI Study Companion API started")

    # Create upload directory
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Start background worker on the same thread
    logger.info("Starting background worker attached to API...")
    worker_task = asyncio.create_task(run_worker())

    yield

    # Shutdown
    worker_task.cancel()
    logger.info("👋 API shutting down")


app = FastAPI(
    title="AI Study Companion",
    description="AI-Powered Learning & Growth Workspace",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(spaces.router)
app.include_router(projects.router)
app.include_router(materials.router)
app.include_router(tutor.router)
app.include_router(quiz.router)
app.include_router(mastery.router)
app.include_router(recommendations.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AI Study Companion"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )
