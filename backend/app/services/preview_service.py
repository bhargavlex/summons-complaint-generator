"""
Preview Service - Generates DOCX previews using MailMerge
"""
import logging
from pathlib import Path
from typing import Dict
from sqlalchemy.orm import Session
from mailmerge import MailMerge

from app.core.config import settings
from app.db.models import Session as SessionModel, FieldValue

logger = logging.getLogger(__name__)


class PreviewService:
    """Service for generating DOCX previews using MailMerge"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _resolve_template_path(self, template_path: str) -> Path:
        """
        Resolve template file path (handles relative/absolute paths).
        
        Args:
            template_path: Template file path from database
            
        Returns:
            Resolved Path object
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        file_path = Path(template_path)
        
        # If absolute path, use it directly
        if file_path.is_absolute():
            if not file_path.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")
            return file_path
        
        # Try relative to backend directory
        backend_dir = Path(__file__).parent.parent.parent
        resolved_path = backend_dir / template_path
        
        if not resolved_path.exists():
            # Try using TEMPLATE_DIR from settings
            template_dir = Path(settings.TEMPLATE_DIR)
            if template_dir.is_absolute():
                resolved_path = template_dir / Path(template_path).name
            else:
                resolved_path = backend_dir / template_dir / Path(template_path).name
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        return resolved_path
    
    def generate_preview(self, session: SessionModel) -> str:
        """
        Generate a DOCX preview for a session by merging field values into the template.
        
        Args:
            session: Session model instance
            
        Returns:
            Path to the generated preview file
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If session has no template
        """
        # Get the session's template
        if not session.template:
            raise ValueError(f"Session {session.uuid} has no associated template")
        
        template = session.template
        
        # Build preview file path
        preview_dir = Path(settings.PREVIEW_DIR)
        if not preview_dir.is_absolute():
            backend_dir = Path(__file__).parent.parent.parent
            preview_dir = backend_dir / preview_dir
        
        # Create previews directory if it doesn't exist
        preview_dir.mkdir(parents=True, exist_ok=True)
        
        preview_filename = f"session_{session.uuid}_preview.docx"
        preview_path = preview_dir / preview_filename
        
        # Get all field_values for the session
        field_values = self.db.query(FieldValue).filter(
            FieldValue.session_id == session.id
        ).all()
        
        # Build dictionary mapping field names (without «») to values
        values_dict: Dict[str, str] = {}
        for field_value in field_values:
            # Get the template field to access placeholder
            template_field = field_value.template_field
            if not template_field:
                logger.warning(f"FieldValue {field_value.id} has no template_field, skipping")
                continue
            
            # Remove « and » from placeholder to get the merge field name
            placeholder = template_field.placeholder
            # Remove « and » characters
            merge_field_name = placeholder.replace('«', '').replace('»', '')
            
            # Use final_value (manual_value if set, otherwise extracted_value)
            value = field_value.final_value
            # Convert None to empty string for MailMerge
            values_dict[merge_field_name] = value if value is not None else ""
        
        # Resolve template file path
        template_path = self._resolve_template_path(template.file_path)
        
        logger.info(f"Generating preview for session {session.uuid}: merging {len(values_dict)} fields")
        
        # Open the original template file using MailMerge
        # Merge all values and write to preview path (overwrites if exists)
        try:
            with MailMerge(str(template_path)) as doc:
                # Merge all values
                doc.merge(**values_dict)
                # Write to preview path (overwrites automatically if file exists)
                doc.write(str(preview_path))
            
            logger.info(f"Preview generated successfully: {preview_path}")
            return str(preview_path)
            
        except Exception as e:
            logger.error(f"Error generating preview for session {session.uuid}: {str(e)}", exc_info=True)
            raise
