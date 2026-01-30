"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import preview, sessions, documents

api_router = APIRouter()

# Register all routers (config is included in main.py so /api/v1/firms and /api/v1/case-types are registered)
api_router.include_router(preview.router, tags=["preview"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(documents.router, prefix="/sessions", tags=["documents"])
