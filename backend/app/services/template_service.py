"""
Template Service - Handles template creation with automatic field extraction
"""
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional
from sqlalchemy.orm import Session

from app.db.models import Template, TemplateField
from app.services.field_extraction import FieldExtractionService
from scripts.extract_template_fields import extract_and_store_template_fields

logger = logging.getLogger(__name__)


def create_template_with_auto_extraction(
    db: Session,
    template: Template,
    auto_extract: bool = True
) -> Tuple[Template, Optional[Dict], bool]:
    """
    Create a template in the database and automatically extract fields from the DOCX file.
    
    Args:
        db: Database session
        template: Template model instance (not yet committed)
        auto_extract: If True, automatically extract fields after template is created
    
    Returns:
        Tuple of (template_instance, extraction_results_dict, extraction_success: bool)
        - template_instance: The created template (with ID populated)
        - extraction_results: Results dict if extraction was attempted, None otherwise
        - extraction_success: True if extraction succeeded, False if failed, None if not attempted
    """
    # First, commit the template so it has an ID
    db.add(template)
    db.flush()  # Get the ID without committing yet
    
    logger.info(f"Created template: {template.name} (ID: {template.id})")
    
    # Commit template first so it exists even if extraction fails
    db.commit()
    
    extraction_results = None
    extraction_success = None
    
    if auto_extract:
        # Check if file exists and is .docx
        file_path = Path(template.file_path)
        if not file_path.is_absolute():
            # Resolve relative path
            from app.core.config import settings
            backend_dir = Path(__file__).parent.parent.parent
            file_path = backend_dir / template.file_path
            
            if not file_path.exists():
                template_dir = Path(settings.TEMPLATE_DIR)
                if template_dir.is_absolute():
                    file_path = template_dir / Path(template.file_path).name
                else:
                    file_path = backend_dir / template_dir / Path(template.file_path).name
        
        if file_path.exists() and template.file_path.endswith('.docx'):
            logger.info(f"Starting automatic field extraction for template '{template.name}' (ID: {template.id})")
            
            # Use a savepoint to rollback only field extraction if it fails
            savepoint = db.begin_nested()
            try:
                extraction_service = FieldExtractionService(db)
                extraction_results = extract_and_store_template_fields(
                    db=db,
                    template=template,
                    extraction_service=extraction_service,
                    auto_commit=False  # We'll handle commit/rollback here
                )
                
                # Check if extraction had errors
                if extraction_results.get("errors"):
                    error_msg = f"Field extraction failed for template '{template.name}' (ID: {template.id})"
                    logger.error(error_msg)
                    for error in extraction_results["errors"]:
                        logger.error(f"  - {error}")
                    
                    # Rollback any fields that were added for this template
                    savepoint.rollback()
                    extraction_success = False
                else:
                    # Success - commit the savepoint (fields are now saved)
                    savepoint.commit()
                    fields_count = len(extraction_results.get("created_fields", [])) + len(extraction_results.get("existing_fields", []))
                    logger.info(f"✓ Successfully extracted {fields_count} fields for template '{template.name}'")
                    extraction_success = True
                    
            except Exception as e:
                # Rollback any partial field additions
                savepoint.rollback()
                error_msg = f"Unexpected error during field extraction for template '{template.name}' (ID: {template.id}): {str(e)}"
                logger.error(error_msg, exc_info=True)
                extraction_results = {
                    "template_id": template.id,
                    "template_name": template.name,
                    "errors": [str(e)]
                }
                extraction_success = False
        else:
            if not template.file_path.endswith('.docx'):
                logger.warning(f"Skipping field extraction for '{template.name}': Only .docx files supported")
            else:
                logger.warning(f"Skipping field extraction for '{template.name}': File not found at {file_path}")
    
    return template, extraction_results, extraction_success
