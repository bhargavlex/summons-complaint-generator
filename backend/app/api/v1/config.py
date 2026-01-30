"""
Config API - law firms, case types (for frontend dropdowns)
"""
from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.base import get_db
from app.db.models import LawFirm, CaseType

router = APIRouter()


class FirmResponse(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class CaseTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None

    class Config:
        from_attributes = True


@router.get("/firms", response_model=list[FirmResponse], tags=["config"])
def list_firms(db: Session = Depends(get_db)):
    """List law firms for dropdown selection (active or is_active not set)."""
    firms = db.query(LawFirm).filter(
        or_(LawFirm.is_active == True, LawFirm.is_active.is_(None))
    ).order_by(LawFirm.name).all()
    return [FirmResponse.model_validate(f) for f in firms]


@router.get("/case-types", response_model=list[CaseTypeResponse], tags=["config"])
def list_case_types(db: Session = Depends(get_db)):
    """List case types for dropdown selection (active or is_active not set)."""
    types = db.query(CaseType).filter(
        or_(CaseType.is_active == True, CaseType.is_active.is_(None))
    ).order_by(CaseType.name).all()
    return [CaseTypeResponse.model_validate(t) for t in types]
