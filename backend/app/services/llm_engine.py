"""
LLM Engine for dynamic field extraction from legal documents.
Supports iterative extraction with temporary field storage.
"""

import json
import logging
import io
import base64
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from openai import AsyncOpenAI, AsyncAzureOpenAI
from pdf2image import convert_from_path
from PIL import Image
from dataclasses import dataclass, field
from datetime import datetime
from app.core.config import settings
from app.services.extraction_tools import generate_extraction_tool, get_all_fields
import app.core.logging  # noqa: F401  # Initialize logging on import

logger = logging.getLogger(__name__)


@dataclass
class ExtractedField:
    """Temporary storage for extracted field values during iteration"""
    field_name: str
    value: str
    source_document: str
    page_number: Optional[int] = None
    confidence: float = 1.0
    iteration: int = 0
    extracted_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractionState:
    """Tracks extraction state across iterations"""
    all_fields: Set[str]
    extracted_fields: Dict[str, ExtractedField] = field(default_factory=dict)
    missing_fields: Set[str] = field(default_factory=set)
    processed_documents: Set[str] = field(default_factory=set)
    processed_pages: Dict[str, List[int]] = field(default_factory=dict)
    iteration_count: int = 0
    context_summary: str = ""
    
    def __post_init__(self):
        """Initialize missing fields from all fields"""
        if not self.missing_fields:
            self.missing_fields = self.all_fields.copy()
    
    def update_extracted(self, field_name: str, value: str, source_doc: str, 
                        page: Optional[int] = None, iteration: int = 0):
        """Update extracted field and remove from missing"""
        if field_name in self.all_fields and value:
            self.extracted_fields[field_name] = ExtractedField(
                field_name=field_name,
                value=value,
                source_document=source_doc,
                page_number=page,
                iteration=iteration
            )
            self.missing_fields.discard(field_name)
            logger.info(f"Extracted field '{field_name}': {value[:50]}...")
    
    def get_missing_fields_list(self) -> List[str]:
        """Get sorted list of missing fields"""
        return sorted(list(self.missing_fields))
    
    def get_extracted_dict(self) -> Dict[str, str]:
        """Get dictionary of extracted field values"""
        return {k: v.value for k, v in self.extracted_fields.items()}


class LLMEngine:
    """
    LLM Engine for extracting structured fields from legal documents.
    Supports dynamic tool generation and iterative extraction.
    """
    
    def __init__(self):
        """
        Initialize LLM Engine.
        
        Automatically detects Azure OpenAI or standard OpenAI from settings.
        """
        # 1. Determine if we are using Azure or Standard OpenAI
        self.use_azure = (
            settings.AZURE_OPENAI_KEY is not None 
            and settings.AZURE_OPENAI_ENDPOINT is not None
        )

        # 2. Initialize the correct client based on config
        if self.use_azure:
            # AZURE CLIENT
            self.client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            self.model = settings.AZURE_OPENAI_DEPLOYMENT
            logger.info(f"LLM Engine initialized with Azure OpenAI - Deployment: {self.model}")
        else:
            # STANDARD OPENAI CLIENT
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )
            self.model = settings.OPENAI_MODEL or "gpt-4-turbo"
            logger.info(f"LLM Engine initialized with standard OpenAI - Model: {self.model}")
    
    
    async def extract_images_from_pdf(self, pdf_path: str, pages: Optional[List[int]] = None) -> Tuple[List[bytes], int]:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to PDF file
            pages: Optional list of page numbers to extract (1-indexed). If None, extracts all pages.
            
        Returns:
            Tuple of (list of image bytes, total_pages)
        """
        try:
            # Convert PDF to images
            poppler_path = settings.POPPLER_PATH if settings.POPPLER_PATH else None
            
            if pages:
                # Convert specific pages (pdf2image uses 1-indexed)
                # Get all pages from first to last, then filter
                first_page = min(pages)
                last_page = max(pages)
                all_images = convert_from_path(
                    pdf_path,
                    first_page=first_page,
                    last_page=last_page,
                    poppler_path=poppler_path
                )
                # Filter to only requested pages (maintain order)
                sorted_pages = sorted(set(pages))
                images = [all_images[p - first_page] for p in sorted_pages if p - first_page < len(all_images)]
            else:
                # Convert all pages
                images = convert_from_path(pdf_path, poppler_path=poppler_path)
            
            total_pages = len(images)
            
            # Convert PIL Images to bytes
            image_bytes_list = []
            for img in images:
                # Convert to RGB if needed (some PDFs have RGBA)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to bytes buffer
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=85)
                image_bytes_list.append(img_bytes.getvalue())
            
            logger.info(f"Converted PDF {pdf_path} to {total_pages} images")
            return image_bytes_list, total_pages
            
        except Exception as e:
            logger.error(f"Error converting PDF to images {pdf_path}: {str(e)}")
            raise
    
    async def extract_fields_from_document(
        self,
        image_bytes_list: List[bytes],
        missing_fields: List[str],
        context_summary: str = "",
        document_name: str = ""
    ) -> Dict[str, str]:
        """
        Extract fields from document images using LLM vision.
        
        Args:
            image_bytes_list: List of image bytes (JPEG) from PDF pages
            missing_fields: List of fields to extract
            context_summary: Summary from previously processed documents
            document_name: Name of the document being processed
            
        Returns:
            Dictionary of extracted field values
        """
        if not missing_fields:
            logger.warning("No missing fields to extract")
            return {}
        
        if not image_bytes_list:
            logger.warning("No images provided")
            return {}
        
        # Generate dynamic tool
        tool = generate_extraction_tool(missing_fields)
        
        # Build system prompt
        system_prompt = f"""You are an expert legal document parser. Extract structured field values from legal documents for Summons & Complaint generation.

CONTEXT FROM PREVIOUSLY PROCESSED DOCUMENTS:
{context_summary if context_summary else "No previous context available."}

CURRENT TASK:
Extract the following fields from the document images: {', '.join(missing_fields)}

INSTRUCTIONS:
1. Only extract fields that are clearly and explicitly present in the document
2. If a field is not found or unclear, do NOT include it in your response
3. Use the context from previous documents to maintain consistency (e.g., same plaintiff name, same dates)
4. If there's a conflict between context and current document, prefer the current document
5. For dates, use consistent format (MM/DD/YYYY preferred)
6. For states, use 2-letter abbreviations when possible
7. Extract exact values as they appear in the document

Be precise and accurate. Only return fields you are confident about."""
        
        # Build user message with images
        user_content = [
            {
                "type": "text",
                "text": f"Document: {document_name if document_name else 'Legal Document'}\n\nExtract the requested fields from these document pages using the provided tool."
            }
        ]
        
        # Add images to user content
        for i, img_bytes in enumerate(image_bytes_list):
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": "extract_fields"}},
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Parse function call response
            message = response.choices[0].message
            
            if message.tool_calls and len(message.tool_calls) > 0:
                function_call = message.tool_calls[0].function
                if function_call.name == "extract_fields":
                    arguments = json.loads(function_call.arguments)
                    logger.info(f"Extracted {len(arguments)} fields from document")
                    return arguments
            
            logger.warning("No function call in LLM response")
            return {}
            
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise
    
    async def process_case_screen_document(
        self,
        pdf_path: str,
        all_fields: Optional[List[str]] = None
    ) -> ExtractionState:
        """
        Process case-screen document (primary iteration).
        This is the first document processed and typically contains maximum data.
        
        Args:
            pdf_path: Path to case-screen PDF
            all_fields: List of all fields to extract. If None, uses default template fields.
            
        Returns:
            ExtractionState with extracted fields
        """
        if all_fields is None:
            all_fields = get_all_fields()
        
        # Initialize extraction state
        state = ExtractionState(all_fields=set(all_fields))
        state.iteration_count = 1
        
        logger.info(f"Processing case-screen document: {pdf_path}")
        logger.info(f"Total fields to extract: {len(all_fields)}")
        
        # Convert PDF to images (all pages for case-screen)
        image_bytes_list, total_pages = await self.extract_images_from_pdf(pdf_path)
        
        # Get missing fields
        missing_fields = state.get_missing_fields_list()
        
        # Extract fields from case-screen document images
        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            missing_fields=missing_fields,
            context_summary="",  # No context for first iteration
            document_name=Path(pdf_path).name
        )
        
        # Update state with extracted fields
        for field_name, value in extracted.items():
            if value:  # Only store non-empty values
                state.update_extracted(
                    field_name=field_name,
                    value=str(value),
                    source_doc=Path(pdf_path).name,
                    page=None,  # Could track pages if needed
                    iteration=1
                )
        
        # Mark document as processed
        state.processed_documents.add(Path(pdf_path).name)
        state.processed_pages[Path(pdf_path).name] = list(range(1, total_pages + 1))
        
        # Generate initial context summary
        state.context_summary = self._generate_context_summary(state)
        
        logger.info(f"Case-screen processing complete. Extracted {len(state.extracted_fields)}/{len(all_fields)} fields")
        logger.info(f"Missing fields: {state.get_missing_fields_list()}")
        
        return state
    
    def _generate_context_summary(self, state: ExtractionState) -> str:
        """
        Generate context summary from extracted fields.
        This will be used in subsequent iterations.
        
        Args:
            state: Current extraction state
            
        Returns:
            Context summary string
        """
        if not state.extracted_fields:
            return ""
        
        extracted_dict = state.get_extracted_dict()
        
        summary_parts = [
            "Previously extracted information:",
            json.dumps(extracted_dict, indent=2)
        ]
        
        return "\n".join(summary_parts)
    
    async def process_additional_document(
        self,
        pdf_path: str,
        state: ExtractionState,
        pages: Optional[List[int]] = None
    ) -> ExtractionState:
        """
        Process additional document in subsequent iterations.
        
        Args:
            pdf_path: Path to PDF document
            state: Current extraction state
            pages: Optional list of pages to process. If None, processes all unprocessed pages.
            
        Returns:
            Updated extraction state
        """
        state.iteration_count += 1
        doc_name = Path(pdf_path).name
        
        logger.info(f"Iteration {state.iteration_count}: Processing document: {doc_name}")
        
        # Determine which pages to process
        processed_pages_for_doc = state.processed_pages.get(doc_name, [])
        
        if pages is None:
            # Convert all pages to images
            image_bytes_list, total_pages = await self.extract_images_from_pdf(pdf_path)
            pages_to_process = list(range(1, total_pages + 1))
        else:
            # Convert specific pages to images
            image_bytes_list, total_pages = await self.extract_images_from_pdf(pdf_path, pages=pages)
            pages_to_process = pages
        
        # Filter out already processed pages
        unprocessed_pages = [p for p in pages_to_process if p not in processed_pages_for_doc]
        
        if not unprocessed_pages:
            logger.info(f"All pages of {doc_name} already processed")
            return state
        
        # Get missing fields
        missing_fields = state.get_missing_fields_list()
        
        if not missing_fields:
            logger.info("All fields already extracted")
            return state
        
        # Extract fields with context from images
        extracted = await self.extract_fields_from_document(
            image_bytes_list=image_bytes_list,
            missing_fields=missing_fields,
            context_summary=state.context_summary,
            document_name=doc_name
        )
        
        # Update state
        for field_name, value in extracted.items():
            if value:
                state.update_extracted(
                    field_name=field_name,
                    value=str(value),
                    source_doc=doc_name,
                    page=None,
                    iteration=state.iteration_count
                )
        
        # Mark pages as processed
        if doc_name not in state.processed_pages:
            state.processed_pages[doc_name] = []
        state.processed_pages[doc_name].extend(unprocessed_pages)
        state.processed_documents.add(doc_name)
        
        # Update context summary
        state.context_summary = self._generate_context_summary(state)
        
        logger.info(f"Extracted {len(extracted)} fields. Total extracted: {len(state.extracted_fields)}/{len(state.all_fields)}")
        
        return state
    
    def get_extraction_summary(self, state: ExtractionState) -> Dict:
        """
        Get summary of extraction state.
        
        Args:
            state: Extraction state
            
        Returns:
            Summary dictionary
        """
        return {
            "total_fields": len(state.all_fields),
            "extracted_fields": len(state.extracted_fields),
            "missing_fields": len(state.missing_fields),
            "extraction_rate": f"{(len(state.extracted_fields) / len(state.all_fields) * 100):.1f}%",
            "iterations": state.iteration_count,
            "processed_documents": list(state.processed_documents),
            "extracted_values": state.get_extracted_dict(),
            "missing_field_names": state.get_missing_fields_list()
        }
