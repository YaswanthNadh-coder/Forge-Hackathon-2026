"""
Ayushman-Shield Backend — FastAPI Application Entry Point.
Autonomous PM-JAY Hospital Bill Auditor & CGRMS Grievance Agent.
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api import audit, grievance, websocket

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ayushman_shield")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle manager."""
    logger.info(f"Initializing {settings.app_name} v{settings.app_version}...")

    # Ensure runtime directories exist
    for directory in [settings.upload_dir, settings.reports_dir, settings.voice_dir]:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Initialize Vector Store & seed official HBP 2022 dataset if Qdrant is accessible
    try:
        from app.rag.qdrant_store import qdrant_manager
        await qdrant_manager.initialize()

        # Seed official HBP 2022 packages if master JSON exists
        master_json = Path(__file__).parent.parent / "data" / "hbp_2022_master.json"
        if master_json.exists():
            from app.rag.ingest import ingest_hbp_data
            info = qdrant_manager.get_collection_info()
            if info.get("status") == "connected" and info.get("points_count", 0) == 0:
                logger.info(f"Seeding Qdrant vector store from official NHA HBP 2022 master: {master_json}")
                await ingest_hbp_data(str(master_json))
    except Exception as e:
        logger.warning(f"Vector DB auto-initialization note: {e}")

    yield

    logger.info("Ayushman-Shield Backend service stopped.")


app = FastAPI(
    title=settings.app_name,
    description="Autonomous PM-JAY Hospital Bill Auditor & CGRMS Grievance Agent (Forge Gen AI Buildathon 2026)",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset routes
Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
Path(settings.voice_dir).mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=settings.reports_dir), name="reports")
app.mount("/voice", StaticFiles(directory=settings.voice_dir), name="voice")

# Register routers
app.include_router(audit.router)
app.include_router(grievance.router)
app.include_router(websocket.router)


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "hbp_reference": "NHA HBP 2022 Master v2.2",
        "cgrms_portal": settings.cgrms_url,
    }

