from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.core.logging import app_logger
from app.database.session import init_db
from app.services.scheduler import start_scheduler, stop_scheduler
from app.api.routes import jobs, items


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app_logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    app_logger.info("Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-grade web scraper dashboard API. "
        "Scrape jobs, products, and news. Filter, export, schedule."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
static_dir = os.path.join(frontend_dir, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str = ""):
    index = os.path.join(frontend_dir, "templates", "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "Frontend not found. Run with frontend/templates/index.html present."}
