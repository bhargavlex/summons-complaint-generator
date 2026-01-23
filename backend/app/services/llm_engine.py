"""
LLM Engine for dynamic field extraction from legal documents.
Supports iterative extraction with temporary field storage.
"""

import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from openai import AsyncOpenAI
import pdfplumber
from dataclasses import dataclass, field
from datetime import datetime
from app.core.config import settings

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
    
    # Template field definitions with descriptions
    FIELD_DEFINITIONS = {
        'Venue_Street_Address_': {
            'type': 'string',
            'description': 'The street address of the venue/court where the case will be filed',
            'required': True
        },
        'Plaintiff_County_': {
            'type': 'string',
            'description': 'The county where the plaintiff resides',
            'required': True
        },
        'Defendant_City': {
            'type': 'string',
            'description': 'The city where the defendant resides',
            'required': True
        },
        'Defendant_Street_Address_': {
            'type': 'string',
            'description': 'The complete street address of the defendant',
            'required': True
        },
        'Defendant_County': {
            'type': 'string',
            'description': 'The county where the defendant resides',
            'required': True
        },
        'Currtent_Month_Year': {
            'type': 'string',
            'description': 'Current month and year in format like "January 2024" or "01/2024"',
            'required': True
        },
        'Plaintiff_name_': {
            'type': 'string',
            'description': 'Full legal name of the plaintiff',
            'required': True
        },
        'LOA': {
            'type': 'string',
            'description': 'Letter of Authorization or Location of Accident',
            'required': True
        },
        'hisher': {
            'type': 'string',
            'description': 'Pronoun "his" or "her" based on plaintiff gender',
            'required': True
        },
        'heshe': {
            'type': 'string',
            'description': 'Pronoun "he" or "she" based on plaintiff gender',
            'required': True
        },
        'Defendant_State': {
            'type': 'string',
            'description': 'The state where the defendant resides (2-letter abbreviation preferred)',
            'required': True
        },
        'Defendant_name': {
            'type': 'string',
            'description': 'Full legal name of the defendant',
            'required': True
        },
        'Defendant_Zip_code': {
            'type': 'string',
            'description': 'ZIP code of the defendant address',
            'required': True
        },
        'Plaintiff_State_': {
            'type': 'string',
            'description': 'The state where the plaintiff resides (2-letter abbreviation preferred)',
            'required': True
        },
        'Case_County': {
            'type': 'string',
            'description': 'The county where the case will be filed',
            'required': True
        },
        'LOA__County': {
            'type': 'string',
            'description': 'County where the accident/location of authorization occurred',
            'required': True
        },
        'Date_of_accident': {
            'type': 'string',
            'description': 'Date when the accident occurred (format: MM/DD/YYYY or similar)',
            'required': True
        },
        'Venue_bases_on': {
            'type': 'string',
            'description': 'Basis for venue selection (e.g., "where accident occurred", "where defendant resides")',
            'required': True
        },
        'Venue_County_State': {
            'type': 'string',
            'description': 'County and state of the venue (e.g., "New York County, New York")',
            'required': True
        },
        'LOA__State': {
            'type': 'string',
            'description': 'State where the accident/location of authorization occurred (2-letter abbreviation)',
            'required': True
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM Engine.
        
        Args:
            api_key: OpenAI API key. If not provided, loads from settings (from .env file)
            model: Model to use. If not provided, loads from settings (from .env file), defaults to "gpt-4o"
        """
        # Load from settings if not provided
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file or pass as parameter.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"LLM Engine initialized with model: {self.model}")
    
    def generate_extraction_tool(self, missing_fields: List[str]) -> Dict:
        """
        Generate dynamic tool/schema for extraction based on missing fields.
        
        Args:
            missing_fields: List of field names that still need to be extracted
            
        Returns:
            Tool definition dictionary for OpenAI function calling
        """
        properties = {}
        required = []
        
        for field_name in missing_fields:
            if field_name in self.FIELD_DEFINITIONS:
                field_def = self.FIELD_DEFINITIONS[field_name]
                properties[field_name] = {
                    "type": field_def['type'],
                    "description": field_def['description']
                }
                if field_def.get('required', False):
                    required.append(field_name)
            else:
                # Fallback for unknown fields
                properties[field_name] = {
                    "type": "string",
                    "description": f"Extract the value for {field_name}"
                }
                required.append(field_name)
        
        tool = {
            "type": "function",
            "function": {
                "name": "extract_fields",
                "description": "Extract field values from the legal document. Only extract fields that are clearly present in the document. If a field is not found, do not include it in the response.",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
        
        logger.info(f"Generated tool for {len(missing_fields)} missing fields")
        return tool
    
    async def extract_text_from_pdf(self, pdf_path: str, pages: Optional[List[int]] = None) -> Tuple[str, int]:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            pages: Optional list of page numbers to extract (1-indexed). If None, extracts all pages.
            
        Returns:
            Tuple of (extracted_text, total_pages)
        """
        try:
            text_parts = []
            total_pages = 0
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                if pages:
                    # Extract specific pages
                    for page_num in pages:
                        if 1 <= page_num <= total_pages:
                            page = pdf.pages[page_num - 1]  # Convert to 0-indexed
                            text = page.extract_text()
                            if text:
                                text_parts.append(f"--- Page {page_num} ---\n{text}")
                else:
                    # Extract all pages
                    for page_num, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text()
                        if text:
                            text_parts.append(f"--- Page {page_num} ---\n{text}")
            
            extracted_text = "\n\n".join(text_parts)
            logger.info(f"Extracted text from {pdf_path}: {len(extracted_text)} characters, {total_pages} pages")
            return extracted_text, total_pages
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            raise
    
    async def extract_fields_from_document(
        self,
        document_text: str,
        missing_fields: List[str],
        context_summary: str = "",
        document_name: str = ""
    ) -> Dict[str, str]:
        """
        Extract fields from document text using LLM.
        
        Args:
            document_text: Text content of the document
            missing_fields: List of fields to extract
            context_summary: Summary from previously processed documents
            document_name: Name of the document being processed
            
        Returns:
            Dictionary of extracted field values
        """
        if not missing_fields:
            logger.warning("No missing fields to extract")
            return {}
        
        # Generate dynamic tool
        tool = self.generate_extraction_tool(missing_fields)
        
        # Build system prompt
        system_prompt = f"""You are an expert legal document parser. Extract structured field values from legal documents for Summons & Complaint generation.

CONTEXT FROM PREVIOUSLY PROCESSED DOCUMENTS:
{context_summary if context_summary else "No previous context available."}

CURRENT TASK:
Extract the following fields from the document below: {', '.join(missing_fields)}

INSTRUCTIONS:
1. Only extract fields that are clearly and explicitly present in the document
2. If a field is not found or unclear, do NOT include it in your response
3. Use the context from previous documents to maintain consistency (e.g., same plaintiff name, same dates)
4. If there's a conflict between context and current document, prefer the current document
5. For dates, use consistent format (MM/DD/YYYY preferred)
6. For states, use 2-letter abbreviations when possible
7. Extract exact values as they appear in the document

Be precise and accurate. Only return fields you are confident about."""
        
        # Build user prompt
        user_prompt = f"""Document: {document_name if document_name else 'Legal Document'}

{document_text[:8000]}  # Limit to avoid token limits

Extract the requested fields using the provided tool."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
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
            all_fields = list(self.FIELD_DEFINITIONS.keys())
        
        # Initialize extraction state
        state = ExtractionState(all_fields=set(all_fields))
        state.iteration_count = 1
        
        logger.info(f"Processing case-screen document: {pdf_path}")
        logger.info(f"Total fields to extract: {len(all_fields)}")
        
        # Extract text from PDF (all pages for case-screen)
        document_text, total_pages = await self.extract_text_from_pdf(pdf_path)
        
        # Get missing fields
        missing_fields = state.get_missing_fields_list()
        
        # Extract fields from case-screen document
        extracted = await self.extract_fields_from_document(
            document_text=document_text,
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
            # Extract all pages
            document_text, total_pages = await self.extract_text_from_pdf(pdf_path)
            pages_to_process = list(range(1, total_pages + 1))
        else:
            # Extract specific pages
            document_text, total_pages = await self.extract_text_from_pdf(pdf_path, pages=pages)
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
        
        # Extract fields with context
        extracted = await self.extract_fields_from_document(
            document_text=document_text,
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
