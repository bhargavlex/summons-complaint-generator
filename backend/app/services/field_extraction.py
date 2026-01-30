"""
Field Extraction Service
Extracts merge fields from DOCX files using mailmerge2 and stores them in the database
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from mailmerge import MailMerge

from app.db.models import (
    Document,
    Session as SessionModel,
    Template,
    TemplateField,
    FieldValue,
    FieldValueStatus,
)
from app.services.party_sync import sync_parties_from_field_values

logger = logging.getLogger(__name__)


class FieldExtractionService:
    """Service for extracting fields from DOCX files using mailmerge2"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_fields_from_docx(self, docx_path: str) -> List[str]:
        """
        Extract merge field names from a DOCX file using mailmerge2.
        
        Args:
            docx_path: Path to the DOCX file
            
        Returns:
            List of merge field names found in the document
            
        Raises:
            FileNotFoundError: If the DOCX file doesn't exist
            Exception: If there's an error reading the DOCX file
        """
        docx_path_obj = Path(docx_path)
        
        if not docx_path_obj.exists():
            raise FileNotFoundError(f"DOCX file not found: {docx_path}")
        
        try:
            with MailMerge(str(docx_path_obj)) as document:
                merge_fields = document.get_merge_fields()
                logger.info(f"Extracted {len(merge_fields)} merge fields from {docx_path}")
                return merge_fields
        except Exception as e:
            logger.error(f"Error extracting fields from {docx_path}: {str(e)}")
            raise
    
    def normalize_placeholder(self, placeholder: str) -> str:
        """
        Normalize a placeholder string to match database format.
        Handles variations in placeholder format (with/without «», spaces, etc.)
        
        Args:
            placeholder: The placeholder string from the DOCX
            
        Returns:
            Normalized placeholder string
        """
        # Remove common delimiters and whitespace
        normalized = placeholder.strip()
        
        # Remove « and » if present
        normalized = normalized.replace('«', '').replace('»', '')
        normalized = normalized.replace('<<', '').replace('>>', '')
        normalized = normalized.replace('{{', '').replace('}}', '')
        
        # Remove leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    def map_extracted_fields_to_template_fields(
        self,
        extracted_fields: List[str],
        template: Template
    ) -> Dict[str, TemplateField]:
        """
        Map extracted merge fields to TemplateField records.
        
        Args:
            extracted_fields: List of merge field names from DOCX
            template: Template model instance
            
        Returns:
            Dictionary mapping normalized field names to TemplateField objects
        """
        # Get all template fields for this template
        template_fields = self.db.query(TemplateField).filter(
            TemplateField.template_id == template.id
        ).all()
        
        # Create a mapping: normalized placeholder -> TemplateField
        placeholder_map = {}
        for tf in template_fields:
            normalized = self.normalize_placeholder(tf.placeholder)
            placeholder_map[normalized] = tf
        
        # Map extracted fields to template fields
        mapped_fields = {}
        for extracted_field in extracted_fields:
            normalized = self.normalize_placeholder(extracted_field)
            if normalized in placeholder_map:
                mapped_fields[normalized] = placeholder_map[normalized]
            else:
                logger.warning(
                    f"Extracted field '{extracted_field}' (normalized: '{normalized}') "
                    f"not found in template fields for template {template.id}"
                )
        
        return mapped_fields
    
    def store_extracted_fields(
        self,
        session: SessionModel,
        document: Document,
        extracted_fields: List[str],
        template: Template
    ) -> List[FieldValue]:
        """
        Extract fields from a DOCX file and store them in the database.
        
        Args:
            session: Session model instance
            document: Document model instance (the uploaded DOCX file)
            extracted_fields: List of merge field names extracted from the DOCX
            template: Template model instance
            
        Returns:
            List of created/updated FieldValue records
        """
        # Map extracted fields to template fields
        mapped_fields = self.map_extracted_fields_to_template_fields(
            extracted_fields,
            template
        )
        
        field_values = []
        
        # Create or update FieldValue records for each mapped field
        for normalized_name, template_field in mapped_fields.items():
            # Check if FieldValue already exists for this session + field
            existing_value = self.db.query(FieldValue).filter(
                FieldValue.session_id == session.id,
                FieldValue.template_field_id == template_field.id
            ).first()
            
            if existing_value:
                # Update existing record
                existing_value.extracted_value = None  # Will be populated by LLM later
                existing_value.source_document_id = document.id
                existing_value.status = FieldValueStatus.PENDING
                existing_value.is_missing = False
                field_values.append(existing_value)
                logger.debug(
                    f"Updated FieldValue for session {session.id}, "
                    f"field {template_field.field_key}"
                )
            else:
                # Create new FieldValue record
                field_value = FieldValue(
                    session_id=session.id,
                    template_field_id=template_field.id,
                    extracted_value=None,  # Will be populated by LLM later
                    source_document_id=document.id,
                    status=FieldValueStatus.PENDING,
                    is_missing=False
                )
                self.db.add(field_value)
                field_values.append(field_value)
                logger.debug(
                    f"Created FieldValue for session {session.id}, "
                    f"field {template_field.field_key}"
                )
        
        # Also create FieldValue records for template fields that weren't found
        # in the extracted fields (mark them as missing)
        all_template_fields = self.db.query(TemplateField).filter(
            TemplateField.template_id == template.id
        ).all()
        
        found_field_ids = {tf.id for tf in mapped_fields.values()}
        
        for template_field in all_template_fields:
            if template_field.id not in found_field_ids:
                # Check if FieldValue already exists
                existing_value = self.db.query(FieldValue).filter(
                    FieldValue.session_id == session.id,
                    FieldValue.template_field_id == template_field.id
                ).first()
                
                if not existing_value:
                    field_value = FieldValue(
                        session_id=session.id,
                        template_field_id=template_field.id,
                        extracted_value=None,
                        source_document_id=document.id,
                        status=FieldValueStatus.PENDING,
                        is_missing=True
                    )
                    self.db.add(field_value)
                    field_values.append(field_value)
                    logger.debug(
                        f"Created missing FieldValue for session {session.id}, "
                        f"field {template_field.field_key}"
                    )
        
        self.db.commit()
        logger.info(
            f"Stored {len(field_values)} field values for session {session.id}, "
            f"document {document.id}"
        )
        # Sync plaintiff/defendant from field_values when LLM or user later fills them
        try:
            sync_parties_from_field_values(session, self.db)
        except Exception as e:
            logger.warning("Failed to sync parties from field values: %s", e)
        
        return field_values
    
    def process_document(
        self,
        session: SessionModel,
        document: Document,
        template: Optional[Template] = None
    ) -> List[FieldValue]:
        """
        Complete workflow: Extract fields from DOCX and store in database.
        
        Args:
            session: Session model instance
            document: Document model instance (the uploaded DOCX file)
            template: Template model instance (if None, uses session.template)
            
        Returns:
            List of created/updated FieldValue records
            
        Raises:
            FileNotFoundError: If the DOCX file doesn't exist
            Exception: If there's an error processing the document
        """
        if template is None:
            template = session.template
        
        if template is None:
            raise ValueError("Template is required but not found")
        
        # Extract fields from DOCX
        extracted_fields = self.extract_fields_from_docx(document.file_path)
        
        # Store extracted fields in database
        field_values = self.store_extracted_fields(
            session=session,
            document=document,
            extracted_fields=extracted_fields,
            template=template
        )
        
        # Mark document as processed
        document.is_processed = True
        self.db.commit()
        
        return field_values
