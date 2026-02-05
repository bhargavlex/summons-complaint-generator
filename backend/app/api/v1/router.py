"""
API v1 router. 
"""

from fastapi import APIRouter
from app.api.v1 import extraction, preview

api_router = APIRouter()

api_router.include_router(extraction.router)
api_router.include_router(preview.router, tags=["preview"])

