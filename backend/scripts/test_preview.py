"""
Test script for preview generation functionality

This script:
1. Creates a test session with field values
2. Tests the preview generation endpoint
3. Verifies the preview file is created

Usage:
    python -m scripts.test_preview
"""
import sys
import logging
from pathlib import Path
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import SessionLocal
from app.db.models import (
    Session as SessionModel,
    Template,
    TemplateField,
    FieldValue,
    SessionStatus,
    FieldValueStatus
)
from app.services.preview_service import PreviewService
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_session(db: Session) -> SessionModel:
    """
    Create a test session with sample field values.
    
    Returns:
        Created Session instance
    """
    # Get the first active template
    template = db.query(Template).filter(Template.is_active == True).first()
    
    if not template:
        raise ValueError("No active template found in database. Please initialize the database first.")
    
    logger.info(f"Using template: {template.name} (ID: {template.id})")
    
    # Create a new session
    session = SessionModel(
        uuid=str(uuid.uuid4()),
        template_id=template.id,
        status=SessionStatus.CREATED
    )
    db.add(session)
    db.flush()  # Get the session ID
    
    logger.info(f"Created test session: {session.uuid} (ID: {session.id})")
    
    # Get all template fields for this template
    template_fields = db.query(TemplateField).filter(
        TemplateField.template_id == template.id
    ).all()
    
    logger.info(f"Found {len(template_fields)} template fields")
    
    # Create sample field values
    sample_values = {
        "case_county": "New York County",
        "plaintiff_name": "John Doe",
        "plaintiff_street_address": "123 Main Street",
        "plaintiff_city": "New York",
        "plaintiff_state": "NY",
        "plaintiff_zip_code": "10001",
        "plaintiff_county": "New York County",
        "defendant_name": "ABC Corporation",
        "defendant_street_address": "456 Business Ave",
        "defendant_city": "New York",
        "defendant_state": "NY",
        "defendant_zip_code": "10002",
        "defendant_county": "New York County",
        "venue_street_address": "789 Court Street",
        "venue_city": "New York",
        "venue_state": "NY",
        "venue_zip_code": "10003",
        "start_date_service": "2024-01-15",
        "end_date_service": "2024-01-20",
        "current_month_year": "January 2024"
    }
    
    created_count = 0
    for template_field in template_fields:
        # Try to find a matching sample value by field_key
        value = sample_values.get(template_field.field_key)
        
        if value is None:
            # Use a default value
            value = f"Sample {template_field.display_name}"
        
        field_value = FieldValue(
            session_id=session.id,
            template_field_id=template_field.id,
            extracted_value=value,
            is_missing=False,
            status=FieldValueStatus.EXTRACTED
        )
        db.add(field_value)
        created_count += 1
    
    db.commit()
    logger.info(f"Created {created_count} field values for session {session.uuid}")
    
    return session


def test_preview_generation(db: Session, session: SessionModel):
    """
    Test preview generation for a session.
    
    Args:
        db: Database session
        session: Session to generate preview for
    """
    logger.info(f"Testing preview generation for session {session.uuid}")
    
    try:
        preview_service = PreviewService(db)
        preview_path = preview_service.generate_preview(session)
        
        logger.info(f"✓ Preview generated successfully: {preview_path}")
        
        # Verify file exists
        preview_file = Path(preview_path)
        if preview_file.exists():
            file_size = preview_file.stat().st_size
            logger.info(f"✓ Preview file exists: {preview_path} ({file_size} bytes)")
            return True
        else:
            logger.error(f"✗ Preview file not found: {preview_path}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Preview generation failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main test function"""
    db = SessionLocal()
    
    try:
        logger.info("=" * 60)
        logger.info("Testing Preview Generation")
        logger.info("=" * 60)
        
        # Create test session with field values
        logger.info("\n1. Creating test session with field values...")
        session = create_test_session(db)
        
        # Test preview generation
        logger.info("\n2. Testing preview generation...")
        success = test_preview_generation(db, session)
        
        if success:
            logger.info("\n" + "=" * 60)
            logger.info("✓ All tests passed!")
            logger.info(f"Session UUID: {session.uuid}")
            logger.info(f"Preview endpoint: GET /api/v1/sessions/{session.uuid}/preview")
            logger.info("=" * 60)
        else:
            logger.error("\n" + "=" * 60)
            logger.error("✗ Tests failed!")
            logger.error("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
