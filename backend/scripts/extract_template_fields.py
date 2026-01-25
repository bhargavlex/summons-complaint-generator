"""
Extract fields from template DOCX file and populate/verify template_fields table.

This script:
1. Reads the template DOCX file from the templates folder
2. Extracts merge fields using mailmerge2
3. Creates/updates TemplateField records in the database with hardcoded metadata
4. Verifies extraction and provides a report

Usage:
    python -m scripts.extract_template_fields [template_id] [--local]
    
    If template_id is not provided, processes all active templates.
    Use --local to test with a local SQLite database (sqlite:///test.db).
"""
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import Base, SessionLocal
from app.db.models import Template, TemplateField, LawFirm, CaseType
from app.services.field_extraction import FieldExtractionService
from app.db.field_definitions import get_field_metadata
from app.core.config import settings

# Mapping of messy placeholders to clean field_keys
# This helps the script know that "Plaintiff_name_" is actually "plaintiff_name"
PLACEHOLDER_MAPPING = {
    "plaintiff_name_": "plaintiff_name",
    "plaintiff_county_": "plaintiff_county",
    "plaintiff_city_": "plaintiff_city",
    "plaintiff_state_": "plaintiff_state",
    "defendant1_name": "defendant_name",
    "defendant1_street_address_": "defendant_street_address",
    "defendant1_city": "defendant_city",
    "defendant1_state": "defendant_state",
    "defendant1_zip_code": "defendant_zip_code",
    "defendant1_county": "defendant_county",
    "venue_street_address_": "venue_street_address",
    "start_date_of_service_of_defendant1": "start_date_service",
    "end_date_of_service_of_defendant1": "end_date_service",
    "currtent_month_year": "current_month_year",
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_placeholder(placeholder: str) -> str:
    """Normalize placeholder to match database format"""
    normalized = placeholder.strip()
    normalized = normalized.replace('«', '').replace('»', '')
    normalized = normalized.replace('<<', '').replace('>>', '')
    normalized = normalized.replace('{{', '').replace('}}', '')
    return normalized.strip()


def extract_and_store_template_fields(
    db: Session,
    template: Template,
    extraction_service: FieldExtractionService
) -> Dict:
    """
    Extract fields from template DOCX and create/update TemplateField records.
    
    Returns:
        Dictionary with extraction results and statistics
    """
    results = {
        "template_id": template.id,
        "template_name": template.name,
        "template_path": template.file_path,
        "extracted_fields": [],
        "created_fields": [],
        "updated_fields": [],
        "existing_fields": [],
        "missing_in_docx": [],
        "errors": []
    }
    
    # Resolve template file path
    template_file_path = Path(template.file_path)
    if not template_file_path.is_absolute():
        # Try relative to backend directory (works in Docker and local)
        backend_dir = Path(__file__).parent.parent
        template_file_path = backend_dir / template_file_path
        
        # Also try using TEMPLATE_DIR from settings if file not found
        if not template_file_path.exists():
            template_dir = Path(settings.TEMPLATE_DIR)
            if template_dir.is_absolute():
                # If TEMPLATE_DIR is absolute, use it directly
                template_file_path = template_dir / Path(template.file_path).name
            else:
                # If TEMPLATE_DIR is relative, combine with backend_dir
                template_file_path = backend_dir / template_dir / Path(template.file_path).name
    
    if not template_file_path.exists():
        error_msg = f"Template file not found: {template_file_path}"
        logger.error(error_msg)
        results["errors"].append(error_msg)
        return results
    
    logger.info(f"Processing template: {template.name} (ID: {template.id})")
    logger.info(f"Template file: {template_file_path}")
    
    # Extract fields from DOCX
    try:
        extracted_fields = extraction_service.extract_fields_from_docx(str(template_file_path))
        logger.info(f"Extracted {len(extracted_fields)} merge fields from DOCX")
        results["extracted_fields"] = extracted_fields
    except Exception as e:
        error_msg = f"Error extracting fields: {str(e)}"
        logger.error(error_msg)
        results["errors"].append(error_msg)
        return results
    
    # Get existing template fields
    existing_fields = {
        normalize_placeholder(tf.placeholder): tf
        for tf in db.query(TemplateField).filter(
            TemplateField.template_id == template.id
        ).all()
    }
    
    # Process each extracted field
    field_order = 1
    for extracted_field in extracted_fields:
        normalized = normalize_placeholder(extracted_field)
        
        if normalized in existing_fields:
            # Field already exists - update if needed
            tf = existing_fields[normalized]
            updated = False
            
            # Update placeholder if it changed
            if tf.placeholder != extracted_field:
                tf.placeholder = extracted_field
                updated = True
            
            if updated:
                results["updated_fields"].append({
                    "field_key": tf.field_key,
                    "placeholder": tf.placeholder,
                    "display_name": tf.display_name
                })
                logger.info(f"Updated field: {tf.field_key} ({tf.placeholder})")
            else:
                results["existing_fields"].append({
                    "field_key": tf.field_key,
                    "placeholder": tf.placeholder,
                    "display_name": tf.display_name
                })
        else:
            # Create new field
            # Generate field_key from normalized placeholder
            raw_key = normalized.lower().replace(' ', '_').replace('-', '_')
            raw_key = ''.join(c for c in raw_key if c.isalnum() or c == '_')
            
            # Map messy placeholder key to a clean definition key if it exists
            field_key = PLACEHOLDER_MAPPING.get(raw_key, raw_key)
            
            # Use centralized definitions
            metadata = get_field_metadata(field_key)
            display_name = metadata.get("display_name")
            description = metadata.get("description")
            expected_format = metadata.get("expected_format")
            
            new_field = TemplateField(
                template_id=template.id,
                field_key=field_key,
                placeholder=extracted_field,
                display_name=display_name,
                description=description,
                expected_format=expected_format,
                field_order=field_order,
                is_required=True
            )
            
            db.add(new_field)
            results["created_fields"].append({
                "field_key": field_key,
                "placeholder": extracted_field,
                "display_name": display_name,
                "description": description
            })
            logger.info(f"Created new field: {field_key} ({extracted_field})")
        
        field_order += 1
    
    # Check for fields in database that weren't found in DOCX
    extracted_normalized = {normalize_placeholder(f) for f in extracted_fields}
    for normalized, tf in existing_fields.items():
        if normalized not in extracted_normalized:
            results["missing_in_docx"].append({
                "field_key": tf.field_key,
                "placeholder": tf.placeholder,
                "display_name": tf.display_name
            })
            logger.warning(
                f"Field '{tf.field_key}' exists in database but not found in DOCX: {tf.placeholder}"
            )
    
    # Commit changes
    try:
        db.commit()
        logger.info("✓ Successfully saved template fields to database")
    except Exception as e:
        db.rollback()
        error_msg = f"Error saving to database: {str(e)}"
        logger.error(error_msg)
        results["errors"].append(error_msg)
    
    return results


def print_extraction_report(results: Dict):
    """Print a formatted report of the extraction results"""
    print("\n" + "=" * 80)
    print(f"TEMPLATE FIELD EXTRACTION REPORT")
    print("=" * 80)
    print(f"Template ID: {results['template_id']}")
    print(f"Template Name: {results['template_name']}")
    print(f"Template Path: {results['template_path']}")
    print("-" * 80)
    
    if results["errors"]:
        print(f"\n❌ ERRORS ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  • {error}")
        return
    
    print(f"\n📄 EXTRACTED FROM DOCX: {len(results['extracted_fields'])} fields")
    for field in results["extracted_fields"]:
        print(f"  • {field}")
    
    print(f"\n✅ CREATED NEW FIELDS: {len(results['created_fields'])}")
    for field in results["created_fields"]:
        print(f"  • {field['field_key']}: {field['placeholder']} ({field['display_name']})")
    
    print(f"\n🔄 UPDATED FIELDS: {len(results['updated_fields'])}")
    for field in results["updated_fields"]:
        print(f"  • {field['field_key']}: {field['placeholder']} ({field['display_name']})")
    
    print(f"\n✓ EXISTING FIELDS (no changes): {len(results['existing_fields'])}")
    for field in results["existing_fields"]:
        print(f"  • {field['field_key']}: {field['placeholder']} ({field['display_name']})")
    
    if results["missing_in_docx"]:
        print(f"\n⚠️  FIELDS IN DATABASE BUT NOT IN DOCX: {len(results['missing_in_docx'])}")
        for field in results["missing_in_docx"]:
            print(f"  • {field['field_key']}: {field['placeholder']} ({field['display_name']})")
    
    print("\n" + "=" * 80)
    print("✓ Extraction complete!")
    print("=" * 80 + "\n")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Extract fields from template DOCX")
    parser.add_argument("template_id", type=int, nargs="?", help="Specific template ID to process")
    parser.add_argument("--local", action="store_true", help="Use local SQLite database for testing")
    args = parser.parse_args()
    
    if args.local:
        # Set up local SQLite database for testing
        print("Using local SQLite database for testing (test.db)")
        local_engine = create_engine("sqlite:///test.db")
        Base.metadata.create_all(bind=local_engine)
        SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)
        db = SessionLocalTest()
        
        # Seed basic data if needed for local test
        if not db.query(LawFirm).first():
            firm = LawFirm(name="Test Law Firm", code="TEST")
            case_type = CaseType(name="Test Case Type", code="TEST")
            db.add(firm)
            db.add(case_type)
            db.flush()
            
            template = Template(
                law_firm_id=firm.id,
                case_type_id=case_type.id,
                name="Test Template",
                file_path="templates/cohan/premises/summons_complaint.docx",
                version=1
            )
            db.add(template)
            db.commit()
            print("✓ Seeded local test data")
    else:
        db = SessionLocal()
    
    extraction_service = FieldExtractionService(db)
    
    try:
        # Get template ID from arguments
        template_id = args.template_id
        if template_id:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                print(f"Error: Template with ID {template_id} not found")
                sys.exit(1)
            templates = [template]
        else:
            # Process all active templates
            templates = db.query(Template).filter(Template.is_active == True).all()
            if not templates:
                print("No active templates found in database")
                sys.exit(1)
            print(f"Found {len(templates)} active template(s) to process\n")
        
        # Process each template
        all_results = []
        for template in templates:
            results = extract_and_store_template_fields(
                db=db,
                template=template,
                extraction_service=extraction_service
            )
            all_results.append(results)
            print_extraction_report(results)
        
        # Summary
        if len(all_results) > 1:
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            total_extracted = sum(len(r["extracted_fields"]) for r in all_results)
            total_created = sum(len(r["created_fields"]) for r in all_results)
            total_updated = sum(len(r["updated_fields"]) for r in all_results)
            total_errors = sum(len(r["errors"]) for r in all_results)
            
            print(f"Templates processed: {len(all_results)}")
            print(f"Total fields extracted: {total_extracted}")
            print(f"Total fields created: {total_created}")
            print(f"Total fields updated: {total_updated}")
            if total_errors > 0:
                print(f"Total errors: {total_errors}")
            print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
