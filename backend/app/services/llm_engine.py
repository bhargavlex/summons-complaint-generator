"""
LLM Engine for field extraction from legal documents using Azure OpenAI.
"""

import json
import logging
import io
import base64
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from openai import AsyncAzureOpenAI
from pdf2image import convert_from_path
from app.core.config import settings
from app.services.extraction_tools import (
    generate_extraction_tool, 
    get_all_fields,
    get_phase1_fields,
    ExtractionState,
    FieldStatus
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
        poppler_path = settings.POPPLER_PATH if settings.POPPLER_PATH else None
        
        if pages:
            first_page = min(pages)
            last_page = max(pages)
            all_images = convert_from_path(pdf_path, first_page=first_page, last_page=last_page, poppler_path=poppler_path)
            sorted_pages = sorted(set(pages))
            images = [all_images[p - first_page] for p in sorted_pages if p - first_page < len(all_images)]
        else:
            images = convert_from_path(pdf_path, poppler_path=poppler_path)
        
        image_bytes_list = []
        for img in images:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_bytes = io.BytesIO()
            
            img.save(img_bytes, format='JPEG', quality=85) #here quality is the compression level of the image, 85 is a good compromise between quality and size
            image_bytes_list.append(img_bytes.getvalue())
        
        logger.info(f"Converted PDF to {len(images)} images")
        return image_bytes_list, len(images)
    
    async def extract_fields_from_document(
        self,
        image_bytes_list: List[bytes],
        fields: List[str],
        document_name: str = "",
        context_summary: Optional[str] = None
    ) -> Dict[str, Dict[str, any]]:
        """
        Extract fields from document images using LLM vision.
        Returns nested schema: {field_name: {value, confidence, reasoning}}
        """
        if not fields or not image_bytes_list:
            return {}
        
        tool = generate_extraction_tool(fields)
        
        system_prompt = """
You are a legal document field extraction engine for Summons & Complaint automation.

Your task is to extract structured field values from legal case documents.

For EACH field return:

- value: extracted text or empty string
- confidence: float between 0.00 and 1.00 (real-valued, not only 0 / 0.5 / 1)
- reasoning: concise explanation INCLUDING:
    • where it was found (caption / paragraph / address block)
    • how it was extracted (explicit match / pattern / inference)
    • why the confidence was assigned

Confidence Guidelines:

1.00 – Exact explicit match in document
0.90–0.99 – Explicit value with minor formatting normalization
0.75–0.89 – Strong contextual match (address blocks, narrative)
0.50–0.74 – Inferred from surrounding text or related fields
0.25–0.49 – Weak inference or partial data
0.01–0.24 – Very weak guess
0.00 – Not present

IMPORTANT RULES:

1. Do NOT default to 1.0 unless the value is explicitly written in the document.
2. Follow field-specific instructions: Some fields allow inference (see field descriptions). If a field description says you can infer, do so with appropriate confidence (0.75-0.85). Only return empty if truly not found or ambiguous.
3. Do not reuse Plaintiff address for LOA unless accident language explicitly confirms it.
4. Do not reuse Defendant mailing address for Venue unless venue language explicitly confirms it.

5. Dates:
   - Accident date must be narrative format: "<Month> <Day>, <Year>"
   - Current month must be: "<Month>_____, <Year>"

6. States must be FULL names.

7. Defendant_name:
   - If multiple defendants, join using " and ".

8. LOA must be full postal accident address. If only location type is found (e.g., parking lot), return empty.

9. Case_County:
   - This is the COURT county where the case is filed, NOT the defendant's county.
   - Look for "COUNTY OF [NAME]" in the caption header.
   - Must be ALL CAPS (e.g., "RICHMOND", "NEW YORK", "KINGS").
   - Do NOT use the defendant's address county - use the court filing county from the caption.

10. Plaintiff_County_:
    - Extract the county where the plaintiff resides.
    - If explicitly stated, use confidence 1.0.
    - If not explicitly stated but you can infer from the city/address , use confidence 0.75-0.85.
    - Use full county name (e.g., "RICHMOND", "NEW YORK", "KINGS").

Reasoning must be specific, for example:
- "Found in caption header 'COUNTY OF RICHMOND'"
- "Extracted from defendant address block"
- "Inferred from plaintiff address showing city and state, where the city is located in that county"

Avoid generic phrases like:
- "Extracted from case details"
- "Standard legal phrase"

Be precise and auditable.

Output JSON only.
"""

        if context_summary:
            system_prompt += f"\n\n{context_summary}"
        
        user_content = [{"type": "text", "text": f"Document: {document_name}\n\nExtract the requested fields from these document pages."}]
        
        # Convert images to base64 because the LLM only accepts base64 images
        for img_bytes in image_bytes_list:
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}})
        
        # Call the LLM
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
        
        
        # Get the response from the LLM
        message = response.choices[0].message
        if message.tool_calls and len(message.tool_calls) > 0:
            function_call = message.tool_calls[0].function
            if function_call.name == "extract_fields":
                arguments = json.loads(function_call.arguments)
                logger.info(f"Extracted {len(arguments)} fields")
                return arguments
        
        return {}
    
    async def process_document(self, pdf_path: str, all_fields: Optional[List[str]] = None) -> Dict[str, str]:
        """Process PDF document and extract fields."""
        if all_fields is None:
            all_fields = get_all_fields()
        
        logger.info(f"Processing document: {pdf_path}")
        
        image_bytes_list, _ = await self.extract_images_from_pdf(pdf_path)
        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            fields=all_fields,
            document_name=Path(pdf_path).name
        )
        
        logger.info(f"Extracted {len(extracted)}/{len(all_fields)} fields")
        return extracted
    
    async def execute_initial_extraction(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None
    ) -> ExtractionState:
        """
        Primary Pass: Process the Case Screen (or main doc) with the full schema.
        Processes all pages (default: all pages) to establish the baseline state.
        
        Args:
            pdf_path: Path to Case Screen PDF
            pages: List of page numbers to process (default: all pages)
        
        Returns:
            ExtractionState with initial extraction results
        """
        logger.info(f"Primary Pass: Initial Extraction - Processing {pdf_path}")
        
        phase1_fields = get_phase1_fields()
        all_fields = phase1_fields
        state = ExtractionState(iteration=1)
        
        # Extract images from PDF (all pages by default)
        image_bytes_list, page_count = await self.extract_images_from_pdf(pdf_path, pages=pages)
        logger.info(f"Converted {page_count} pages to images")
        
        # Extract fields with full schema
        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            fields=all_fields,
            document_name=Path(pdf_path).name
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
                    source_doc=Path(pdf_path).name
                )
                
                # Set status to EMPTY if confidence is 0.0 or value is empty
                if confidence == 0.0 or not value:
                    state.fields[field_name].status = FieldStatus.EMPTY
        
        # Force non Phase-1 fields to EMPTY
        for field_name in state.fields:
            if field_name not in phase1_fields:
                state.fields[field_name].value = ""
                state.fields[field_name].confidence = 0.0
                state.fields[field_name].status = FieldStatus.EMPTY
        
        logger.info(f"Primary Pass complete: {len([f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW])} fields pending review, {len(state.get_empty_fields())} empty")
        return state
    
    async def execute_targeted_refinement(
        self,
        pdf_path: str,
        state: ExtractionState,
        pages: Optional[List[int]] = None
    ) -> ExtractionState:
        """
        Secondary Pass: Refine missing fields using supporting documents.
        Only targets fields that are currently EMPTY (Gap Filling).
        
        Args:
            pdf_path: Path to supporting document (e.g., Police Report)
            state: Current ExtractionState
            pages: Optional list of page numbers to process
        
        Returns:
            Updated ExtractionState
        """
        logger.info(f"Secondary Pass: Targeted Refinement - Processing {pdf_path}")
        
        state.iteration += 1
        
        # Get only empty fields (exclude approved fields)
        empty_fields = state.get_empty_fields()
        if not empty_fields:
            logger.info("No empty fields to extract")
            return state
        
        # Generate context summary from approved fields
        context_summary = state.generate_context_summary()
        logger.info(f"Context: {context_summary}")
        logger.info(f"Targeting {len(empty_fields)} empty fields: {empty_fields}")
        
        # Extract images
        image_bytes_list, page_count = await self.extract_images_from_pdf(pdf_path, pages=pages)
        logger.info(f"Converted {page_count} pages to images")
        
        # Extract only empty fields
        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            fields=empty_fields,
            document_name=Path(pdf_path).name,
            context_summary=context_summary
        )
        
        # Update state with new extractions
        for field_name, field_data in extracted.items():
            if isinstance(field_data, dict):
                value = field_data.get("value", "")
                confidence = field_data.get("confidence", 0.0)
                reasoning = field_data.get("reasoning", "")
                
                # Guard against Venue/ LOA Hallucinations
                if field_name.startswith("Venue") or field_name.startswith("LOA"):
                    if "accident" not in reasoning.lower() and "venue" not in reasoning.lower() and "location" not in reasoning.lower():
                        value = ""
                        confidence = 0.0
                
                if confidence > 0.0 and value:
                    state.update_field(
                        field_name=field_name,
                        value=value,
                        confidence=confidence,
                        reasoning=reasoning,
                        source_doc=Path(pdf_path).name
                    )
                    state.fields[field_name].status = FieldStatus.PENDING_REVIEW
        
        logger.info(f"Refinement Pass complete: {len([f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW])} fields pending review, {len(state.get_empty_fields())} still empty")
        return state