"""
Sessions API - create and manage extraction sessions
"""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Session as SessionModel, Template, LawFirm, CaseType
from app.db.models.session import SessionStatus
from app.services.llm_extraction_service import (
    run_llm_extraction_for_session,
    ensure_session_field_values,
    seed_test_values_for_session,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateSessionRequest(BaseModel):
    law_firm_code: str
    case_type_code: str


class CreateSessionResponse(BaseModel):
    uuid: str


class SessionListItem(BaseModel):
    uuid: str
    status: str
    created_at: str
    template_name: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=list[SessionListItem], tags=["sessions"])
def list_sessions(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    List existing sessions (newest first). Use to load test data or resume a session.
    """
    sessions = (
        db.query(SessionModel)
        .order_by(SessionModel.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for s in sessions:
        template_name = s.template.name if s.template else None
        out.append(
            SessionListItem(
                uuid=s.uuid,
                status=s.status.value,
                created_at=s.created_at.isoformat() if s.created_at else "",
                template_name=template_name,
            )
        )
    return out


@router.post("", response_model=CreateSessionResponse, tags=["sessions"])
def create_session(
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new extraction session for the given law firm and case type.
    Returns session UUID for use in document upload and field endpoints.
    """
    firm_code = (body.law_firm_code or "").strip().upper()
    firm = db.query(LawFirm).filter(
        LawFirm.code == firm_code,
    ).filter(
        (LawFirm.is_active == True) | (LawFirm.is_active.is_(None)),
    ).first()
    if not firm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Law firm not found: {body.law_firm_code}",
        )

    code = (body.case_type_code or "").strip().upper().replace("-", "_").replace(" ", "_")
    case_type = db.query(CaseType).filter(
        CaseType.code == code,
    ).filter(
        (CaseType.is_active == True) | (CaseType.is_active.is_(None)),
    ).first()
    if not case_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case type not found: {body.case_type_code}",
        )

    template = db.query(Template).filter(
        Template.law_firm_id == firm.id,
        Template.case_type_id == case_type.id,
        Template.is_active == True,
    ).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No template for firm {body.law_firm_code} and case type {body.case_type_code}",
        )

    session_uuid = str(uuid.uuid4())
    session = SessionModel(
        uuid=session_uuid,
        template_id=template.id,
        status=SessionStatus.CREATED,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    # Ensure FieldValue rows exist for all template fields so extraction UI has fields to show
    ensure_session_field_values(db, session)
    # Seed test values for some fields (until LLM extraction is integrated)
    seed_test_values_for_session(db, session)
    logger.info(f"Created session {session_uuid} for template {template.id}")
    return CreateSessionResponse(uuid=session_uuid)


@router.post("/{session_uuid}/extract", tags=["sessions"])
async def run_extraction(
    session_uuid: str,
    db: Session = Depends(get_db),
):
    """
    Run LLM extraction on this session's PDF document(s).
    Extracted values are written to field_values; GET /sessions/{uuid}/fields will then return them.
    Requires at least one PDF in the session.
    """
    session = db.query(SessionModel).filter(SessionModel.uuid == session_uuid).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_uuid}",
        )
    try:
        summary = await run_llm_extraction_for_session(db, session)
        return summary
    except Exception as e:
        logger.exception("LLM extraction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
