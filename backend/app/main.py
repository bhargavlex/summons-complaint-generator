import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1 import config as config_api

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed data on startup so you don't need to run setup_db manually."""
    import asyncio
    from app.db.init_db import create_tables, seed_data
    from app.db.base import SessionLocal

    for attempt in range(5):
        try:
            create_tables()
            db = SessionLocal()
            try:
                seed_data(db)
            finally:
                db.close()
            logger.info("Database initialized (tables + seed data)")
            break
        except Exception as e:
            if attempt < 4:
                logger.warning("Database init attempt %s failed: %s. Retrying in 3s...", attempt + 1, e)
                await asyncio.sleep(3)
            else:
                logger.warning("Database init on startup failed after 5 attempts: %s. Run setup_db.py if needed.", e)
    yield
    # shutdown: nothing to do


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include config routes (firms, case-types) at /api/v1 so GET /api/v1/firms and /api/v1/case-types work
app.include_router(config_api.router, prefix="/api/v1", tags=["config"])

# Include API v1 router (sessions, documents, preview)
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to Summons & Complaint Generator API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
