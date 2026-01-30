"""
LLM Engine for field extraction from legal documents using Azure OpenAI.
"""

import io
import json
import logging
import time
import base64
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from openai import AsyncAzureOpenAI
from pdf2image import convert_from_path
from app.core.config import settings
from app.services.extraction_tools import (
    generate_extraction_tool,
    generate_phase1_extraction_tool,
    generate_phase2_extraction_tool,
    get_all_fields,
    get_phase1_fields,
    get_phase1_system_prompt,
    get_phase2_fields,
    get_phase2_system_prompt,
    ExtractionState,
    FieldStatus,
)

logger = logging.getLogger(__name__)


class LLMEngine:
    """Simple LLM Engine for extracting fields from legal documents."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.model = settings.AZURE_OPENAI_DEPLOYMENT
        logger.info(f"LLM Engine initialized - Deployment: {self.model}")
    
    async def extract_images_from_pdf(self, pdf_path: str, pages: Optional[List[int]] = None) -> Tuple[List[bytes], int]:
        """Convert PDF pages to images."""
        logger.info("extract_images_from_pdf: path=%s, pages=%s", pdf_path, pages)
        poppler_path = settings.POPPLER_PATH if settings.POPPLER_PATH else None
        
        if pages:
            first_page = min(pages)
            last_page = max(pages)
            all_images = convert_from_path(pdf_path, first_page=first_page, last_page=last_page, poppler_path=poppler_path,dpi=150)
            sorted_pages = sorted(set(pages))
            images = [all_images[p - first_page] for p in sorted_pages if p - first_page < len(all_images)]
        else:
            images = convert_from_path(pdf_path, poppler_path=poppler_path,dpi=150)
        
        image_bytes_list = []
        for img in images:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_bytes = io.BytesIO()
            
            img.save(img_bytes, format='JPEG', quality=70) #here quality is the compression level of the image, 70 is a good compromise between quality and size
            image_bytes_list.append(img_bytes.getvalue())
        
        logger.info(f"Converted PDF to {len(images)} images")
        return image_bytes_list, len(images)
    
    async def extract_fields_from_document(
        self,
        image_bytes_list: List[bytes],
        fields: List[str],
        document_name: str = "",
        context_summary: Optional[str] = None,
        system_prompt: Optional[str] = None,
        use_phase1_tool: bool = False,
        use_phase2_tool: bool = False,
    ) -> Dict[str, Dict[str, any]]:
        """
        Extract fields from document images using LLM vision.
        Returns nested schema: {field_name: {value, confidence, reasoning}}
        If system_prompt is provided (e.g. phase-1/phase-2), that prompt is used; otherwise default.
        If use_phase1_tool is True, uses phase-1 tool (Case Screen UI). If use_phase2_tool is True, uses phase-2 tool (gap fill).
        """
        if not fields or not image_bytes_list:
            logger.warning(
                "extract_fields_from_document: empty fields or images, skipping (fields=%d, images=%d)",
                len(fields) if fields else 0,
                len(image_bytes_list) if image_bytes_list else 0,
            )
            return {}
        
        logger.info(
            "extract_fields_from_document: document=%s, fields=%d, use_phase1_tool=%s, use_phase2_tool=%s",
            document_name, len(fields), use_phase1_tool, use_phase2_tool,
        )
        if use_phase1_tool:
            tool = generate_phase1_extraction_tool(fields)
        elif use_phase2_tool:
            tool = generate_phase2_extraction_tool(fields)
        else:
            tool = generate_extraction_tool(fields)
        
        if system_prompt is None:
            system_prompt = """
        You are a legal document field extraction engine.

        Extract structured fields from OCR text or document images.

        For each field return:
        - value
        - confidence (0.0–1.0, real valued)
        - reasoning (where found + how extracted + why confidence)

        Rules:
        - Do not hallucinate.
        - Return empty value with confidence 0.0 if truly missing or ambiguous.
        - Follow each field's description strictly.
        - Use inference ONLY when explicitly allowed in the field description.
        - Be precise and auditable.
        - Output JSON only.
        """


        
        
        user_content = [{"type": "text", "text": f"Document: {document_name}\n\nExtract the requested fields from these document pages."}]

        if context_summary:
            user_content.insert(0, {"type":"text","text":context_summary})
        
        # Convert images to base64 because the LLM only accepts base64 images
        for img_bytes in image_bytes_list:
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}})
        
        logger.debug("extract_fields_from_document: calling LLM with %d images", len(image_bytes_list))
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": "extract_fields"}},
            temperature=0.1
        )
        
        
        message = response.choices[0].message
        if message.tool_calls and len(message.tool_calls) > 0:
            function_call = message.tool_calls[0].function
            if function_call.name == "extract_fields":
                try:
                    arguments = json.loads(function_call.arguments)
                    logger.info("extract_fields_from_document: extracted %d fields from %s", len(arguments), document_name)
                    return arguments
                except json.JSONDecodeError as e:
                    logger.error("extract_fields_from_document: failed to parse tool arguments: %s", e)
                    return {}
            logger.warning("extract_fields_from_document: unexpected tool name %s", getattr(function_call, "name", None))
        else:
            logger.warning("extract_fields_from_document: no tool_calls in response")
        return {}
    
    async def process_document(self, pdf_path: str, all_fields: Optional[List[str]] = None) -> Dict[str, str]:
        """Process PDF document and extract fields."""
        if all_fields is None:
            all_fields = get_all_fields()
        logger.info("process_document: path=%s, fields=%d", pdf_path, len(all_fields))
        
        image_bytes_list, _ = await self.extract_images_from_pdf(pdf_path)
        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            fields=all_fields,
            document_name=Path(pdf_path).name
        )
        
        logger.info("process_document: extracted %d/%d fields", len(extracted), len(all_fields))
        return extracted
    
    async def execute_phase1(
        self,
        case_screen_pdf_path: str,
        pages: Optional[List[int]] = None,
    ) -> ExtractionState:
        """
        Phase-1: Case Screen extraction only.
        Extracts phase-1 fields (plaintiff, defendant, incident) from the Case Screen PDF
        using the phase-1 prompt and tool. Does not touch phase-2 fields.
        
        Args:
            case_screen_pdf_path: Path to Case Screen PDF (CloudLex / Matter Manager UI).
            pages: Optional list of page numbers to process (default: all pages).
        
        Returns:
            ExtractionState with phase-1 fields populated; non–phase-1 fields left EMPTY.
        """
        phase1_start = time.perf_counter()
        logger.info("execute_phase1: starting Case Screen extraction, path=%s", case_screen_pdf_path)
        phase1_fields = get_phase1_fields()
        logger.debug("execute_phase1: phase1_fields=%s", phase1_fields)
        state = ExtractionState(iteration=1)
        
        image_bytes_list, page_count = await self.extract_images_from_pdf(
            case_screen_pdf_path, pages=pages
        )
        logger.info("execute_phase1: converted %d pages to images", page_count)
        
        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            fields=phase1_fields,
            document_name=Path(case_screen_pdf_path).name,
            system_prompt=get_phase1_system_prompt(),
            use_phase1_tool=True,
        )
        
        # Update state with extracted fields
        for field_name, field_data in extracted.items():
            if isinstance(field_data, dict):
                value = field_data.get("value", "")
                confidence = field_data.get("confidence", 0.0)
                reasoning = field_data.get("reasoning", "")
                
                state.update_field(
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                    reasoning=reasoning,
                    source_doc=Path(case_screen_pdf_path).name
                )
                if confidence == 0.0 or not value:
                    state.fields[field_name].status = FieldStatus.EMPTY
        updated_count = sum(1 for fn in phase1_fields if state.fields.get(fn) and state.fields[fn].value)
        logger.debug("execute_phase1: updated %d phase-1 fields with values", updated_count)
        
        for field_name in state.fields:
            if field_name not in phase1_fields:
                state.fields[field_name].value = ""
                state.fields[field_name].confidence = 0.0
                state.fields[field_name].status = FieldStatus.EMPTY
        
        pending = len([f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW])
        empty = len(state.get_empty_fields())
        phase1_elapsed = time.perf_counter() - phase1_start
        logger.info("execute_phase1: complete — pending_review=%d, empty=%d, elapsed_sec=%.2f", pending, empty, phase1_elapsed)
        return state

    async def execute_phase2(
        self,
        supporting_doc_pdf_path: str,
        state: ExtractionState,
        pages: Optional[List[int]] = None,
    ) -> ExtractionState:
        """
        Phase-2: Targeted refinement (gap filling) from a supporting document.
        Only extracts fields that are currently EMPTY. Uses approved/phase-1 context.
        
        Args:
            supporting_doc_pdf_path: Path to supporting document (e.g., police report, pleadings).
            state: ExtractionState from Phase-1 (or previous run).
            pages: Optional list of page numbers to process.
        
        Returns:
            Updated ExtractionState.
        """
        phase2_start = time.perf_counter()
        logger.info("execute_phase2: starting targeted refinement, path=%s, pages=%s", supporting_doc_pdf_path, pages)
        state.iteration += 1

        phase2_fields = get_phase2_fields()
        all_empty = state.get_empty_fields()
        empty_fields = [f for f in all_empty if f in phase2_fields]
        if not empty_fields:
            phase2_elapsed = time.perf_counter() - phase2_start
            logger.info("execute_phase2: no empty Phase-2 fields to extract (all_empty=%d, phase2_intersection=0), skipping, elapsed_sec=%.2f", len(all_empty), phase2_elapsed)
            return state

        # Claim Letter / supporting doc: only page 1 has needed fields (Claimant, D/A, Place, defendant address); pages 2–3 are boilerplate
        phase2_pages = pages if pages is not None else [1]
        logger.info("execute_phase2: targeting %d empty Phase-2 fields: %s (using pages=%s)", len(empty_fields), empty_fields, phase2_pages)

        image_bytes_list, page_count = await self.extract_images_from_pdf(
            supporting_doc_pdf_path, pages=phase2_pages
        )
        logger.info("execute_phase2: converted %d page(s) to images", page_count)

        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            fields=empty_fields,
            document_name=Path(supporting_doc_pdf_path).name,
            context_summary=None,
            system_prompt=get_phase2_system_prompt(),
            use_phase2_tool=True,
        )
        
        # Update state with new extractions
        for field_name, field_data in extracted.items():
            if isinstance(field_data, dict):
                value = field_data.get("value", "")
                confidence = field_data.get("confidence", 0.0)
                reasoning = field_data.get("reasoning", "")
                
                if field_name.startswith("Venue") or field_name.startswith("LOA"):
                    if "accident" not in reasoning.lower() and "venue" not in reasoning.lower() and "location" not in reasoning.lower():
                        logger.debug("execute_phase2: guard stripped Venue/LOA for %s (reasoning missing accident/venue/location)", field_name)
                        value = ""
                        confidence = 0.0
                
                if confidence > 0.0 and value:
                    state.update_field(
                        field_name=field_name,
                        value=value,
                        confidence=confidence,
                        reasoning=reasoning,
                        source_doc=Path(supporting_doc_pdf_path).name
                    )
                    state.fields[field_name].status = FieldStatus.PENDING_REVIEW
        
        pending = len([f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW])
        empty = len(state.get_empty_fields())
        phase2_elapsed = time.perf_counter() - phase2_start
        logger.info("execute_phase2: complete — pending_review=%d, still_empty=%d, elapsed_sec=%.2f", pending, empty, phase2_elapsed)
        return state

    async def execute_extraction_pipeline(
        self,
        case_screen_pdf_path: str,
        supporting_doc_pdf_path: Optional[str] = None,
        case_screen_pages: Optional[List[int]] = None,
        supporting_doc_pages: Optional[List[int]] = None,
    ) -> ExtractionState:
        """
        Run the full extraction pipeline: Phase-1 first, then Phase-2.
        
        1. Phase-1: Extracts from the Case Screen PDF (phase-1 fields only).
        2. Phase-2: If a supporting document path is provided, fills empty fields
           from that document; otherwise returns state after Phase-1 only.
        
        Args:
            case_screen_pdf_path: Path to Case Screen PDF (required).
            supporting_doc_pdf_path: Optional path to supporting document for Phase-2.
            case_screen_pages: Optional page numbers for Case Screen (default: all).
            supporting_doc_pages: Optional page numbers for supporting doc (default: all).
        
        Returns:
            ExtractionState after Phase-1 and (if provided) Phase-2.
        """
        pipeline_start = time.perf_counter()
        logger.info("execute_extraction_pipeline: starting — case_screen=%s, supporting_doc=%s", case_screen_pdf_path, supporting_doc_pdf_path)

        state = await self.execute_phase1(
            case_screen_pdf_path=case_screen_pdf_path,
            pages=case_screen_pages,
        )
        phase1_elapsed = time.perf_counter() - pipeline_start

        phase2_elapsed = 0.0
        if supporting_doc_pdf_path:
            logger.info("execute_extraction_pipeline: running Phase-2 with %s", supporting_doc_pdf_path)
            phase2_start = time.perf_counter()
            state = await self.execute_phase2(
                supporting_doc_pdf_path=supporting_doc_pdf_path,
                state=state,
                pages=supporting_doc_pages,
            )
            phase2_elapsed = time.perf_counter() - phase2_start

        total_elapsed = time.perf_counter() - pipeline_start
        if not supporting_doc_pdf_path:
            logger.info("execute_extraction_pipeline: no supporting doc provided, skipping Phase-2")
        logger.info(
            "execute_extraction_pipeline: finished — phase1_elapsed_sec=%.2f, phase2_elapsed_sec=%.2f, total_elapsed_sec=%.2f",
            phase1_elapsed, phase2_elapsed, total_elapsed,
        )
        return state

    # Backward-compatible aliases
    async def execute_initial_extraction(
        self, pdf_path: str, pages: Optional[List[int]] = None
    ) -> ExtractionState:
        """Alias for execute_phase1. Prefer execute_phase1 or execute_extraction_pipeline."""
        return await self.execute_phase1(case_screen_pdf_path=pdf_path, pages=pages)

    async def execute_targeted_refinement(
        self,
        pdf_path: str,
        state: ExtractionState,
        pages: Optional[List[int]] = None,
    ) -> ExtractionState:
        """Alias for execute_phase2. Prefer execute_phase2 or execute_extraction_pipeline."""
        return await self.execute_phase2(
            supporting_doc_pdf_path=pdf_path, state=state, pages=pages
        )