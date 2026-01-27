"""
Extraction API: initiate, refine, get case.
 
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.llm_engine import LLMEngine
from app.services.extraction_tools import ExtractionState
from app.schemas.extraction import CaseResponse, FieldData, RefineResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["extraction"])

# In-memory store for ExtractionState by case_id (dummy persistence for testing)
_case_store: Dict[str, ExtractionState] = {}

@router.get("/debug/cases")
async def debug_cases():
    return {
        "total": len(_case_store),
        "case_ids": list(_case_store.keys())
    }

def _state_to_response(state: ExtractionState) -> CaseResponse:
    """Convert ExtractionState to CaseResponse schema."""
    fields_data = {
        name: FieldData(
            value=f.value,
            confidence=f.confidence,
            reasoning=f.reasoning,
            status=f.status.value,
            source_doc=f.source_doc,
        )
        for name, f in state.fields.items()
    }
    return CaseResponse(case_id=state.case_id, iteration=state.iteration, fields=fields_data)


@router.post("/initiate", response_model=CaseResponse, summary="Phase 1: run initial extraction on Case Screen docx")
async def initiate_extraction(case_screen: UploadFile = File(..., description="Case Screen pdf (all pages)")):
    """
    Phase 1: Accept Case Screen pdf, run initial extraction, return state for review.
    Frontend will display fields and collect approved_field_ids for refine.
    Uploaded PDF is temporarily saved, then deleted after processing.
    Upload → Temp file created → LLM reads → Deleted.
    """
    if not case_screen.filename or not case_screen.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Case screen must be a pdf file")

    suffix = Path(case_screen.filename).suffix
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await case_screen.read()
            tmp.write(content)
            tmp_path = tmp.name
    except Exception as e:
        logger.exception("Failed to save uploaded PDF")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        engine = LLMEngine()
        state = await engine.execute_initial_extraction(tmp_path, pages=[1, 2, 3, 4, 5, 6])
        _case_store[state.case_id] = state
        return _state_to_response(state)
    except Exception as e:
        logger.exception("Initial extraction failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.get("/case/{case_id}", response_model=CaseResponse, summary="Get extraction state for frontend (initial load)")
async def get_case(case_id: str):
    """
    Initial load for frontend: return current extraction state by case_id.
    """
    if case_id not in _case_store:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return _state_to_response(_case_store[case_id])


# @router.post("/refine", response_model=RefineResponse, summary="Phase 3: apply approved fields + refine from new document")
# async def refine(
#     case_id: str = Form(...),
#     approved_fields: str = Form(..., description="JSON array of field names, e.g. [\"Plaintiff_name_\", \"Defendant_name\"]"),
#     new_file: UploadFile = File(..., description="Supporting document (e.g. Police Report)"),
# ):
#     """
#     Phase 2→3: Accept approved field IDs and new document.
#     Applies approved locks, then runs targeted refinement on EMPTY fields only.
#     """
#     import json
#     if case_id not in _case_store:
#         raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

#     try:
#         approved_list = json.loads(approved_fields)
#         if not isinstance(approved_list, list):
#             approved_list = [approved_list]
#     except json.JSONDecodeError:
#         approved_list = [s.strip() for s in approved_fields.strip("[]").replace('"', "").split(",")]

#     if not new_file.filename or not new_file.filename.lower().endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Supporting document must be a PDF file")

#     suffix = Path(new_file.filename).suffix
#     try:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#             content = await new_file.read()
#             tmp.write(content)
#             tmp_path = tmp.name
#     except Exception as e:
#         logger.exception("Failed to save uploaded PDF")
#         raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

#     try:
#         state = _case_store[case_id]
#         state.approve_fields(approved_list)
#         engine = LLMEngine()
#         state = await engine.execute_targeted_refinement(tmp_path, state, pages=None)
#         _case_store[case_id] = state
#         return RefineResponse(
#             case_id=state.case_id,
#             iteration=state.iteration,
#             fields={name: FieldData(value=f.value, confidence=f.confidence, reasoning=f.reasoning, status=f.status.value, source_doc=f.source_doc) for name, f in state.fields.items()},
#         )
#     except Exception as e:
#         logger.exception("Refinement failed")
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         try:
#             os.unlink(tmp_path)
#         except Exception:
#             pass
