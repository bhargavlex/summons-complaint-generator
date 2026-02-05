"""
Pydantic schemas for extraction API (Phase 2 data contracts).
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FieldData(BaseModel):
    """Per-field data for frontend display."""
    value: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    status: str = "EMPTY"  # PENDING_REVIEW | APPROVED | EMPTY
    source_doc: Optional[str] = None


class CaseResponse(BaseModel):
    """Response for GET /case/{id} and POST /initiate. Matches ExtractionState.to_dict()."""
    case_id: str
    iteration: int = 1
    fields: Dict[str, FieldData] = Field(default_factory=dict)


class RefineRequest(BaseModel):
    """Body for POST /refine (approved fields). File is sent as multipart."""
    case_id: str
    approved_fields: List[str] = Field(default_factory=list, description="Field IDs user confirmed as correct")


class RefineResponse(BaseModel):
    """Response after refinement pass."""
    case_id: str
    iteration: int
    fields: Dict[str, FieldData]
