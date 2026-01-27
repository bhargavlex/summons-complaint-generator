"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import preview

api_router = APIRouter()

# Register all routers
api_router.include_router(preview.router, tags=["preview"])
