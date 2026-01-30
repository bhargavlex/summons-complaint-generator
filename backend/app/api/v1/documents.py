"""
Documents API - upload documents to a session and run extraction
"""
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.base import get_db
from app.db.models import Session as SessionModel, Document
from app.core.config import settings
from app.services.field_extraction import FieldExtractionService
from app.services.llm_extraction_service import run_llm_extraction_for_session

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}


class UploadDocumentResponse(BaseModel):
    document_id: int


@router.post("/{session_uuid}/documents", response_model=UploadDocumentResponse, tags=["documents"])
async def upload_document(
    session_uuid: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a document to a session. Saves the file, creates a Document record.
    For DOCX: runs template field extraction (merge-field names). For PDF: runs LLM extraction and fills field values.
    """
    session = db.query(SessionModel).filter(SessionModel.uuid == session_uuid).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_uuid}",
        )

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES and not file.filename.lower().endswith((".pdf", ".docx", ".doc", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed types: PDF, DOCX, DOC, TXT",
        )

    # Save under UPLOAD_DIR / session_uuid / filename
    upload_root = Path(settings.UPLOAD_DIR)
    session_dir = upload_root / session_uuid
    session_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    file_path = session_dir / safe_name

    try:
        content = file.file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File larger than {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB",
            )
        file_path.write_bytes(content)
    except Exception as e:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e}",
        ) from e

    # Store path relative to UPLOAD_DIR or absolute for service
    path_for_db = str(file_path)
    doc = Document(
        session_id=session.id,
        filename=file.filename,
        file_path=path_for_db,
        file_size_bytes=len(content),
        mime_type=content_type or None,
        is_processed=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # DOCX: create field_value rows from merge fields (no values yet)
    if path_for_db.lower().endswith(".docx"):
        try:
            extraction = FieldExtractionService(db)
            extraction.process_document(session, doc)
        except FileNotFoundError as e:
            logger.warning(f"Extraction skipped (file not found): {e}")
        except Exception as e:
            logger.warning(f"Extraction failed for document {doc.id}: {e}")
    # PDF: run LLM extraction and fill field values so GET /fields returns them
    elif path_for_db.lower().endswith(".pdf"):
        try:
            await run_llm_extraction_for_session(db, session)
        except Exception as e:
            logger.warning(f"LLM extraction failed for document {doc.id}: {e}")
            # Do not fail the upload; document is stored

    return UploadDocumentResponse(document_id=doc.id)
