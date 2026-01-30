"""
Database initialization script
Creates all tables and seeds initial data for COHAN LAW + Premises
"""
import sys
import logging
from pathlib import Path
from typing import Tuple, Dict
from sqlalchemy.orm import Session
from app.db.base import Base, engine, SessionLocal
from app.db.models import (
    LawFirm,
    CaseType,
    Template,
    TemplateField,
    Session as SessionModel,
    FieldValue,
)
from app.db.models.session import SessionStatus
from app.db.models.field_value import FieldValueStatus


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")


def extract_fields_for_template(
    db: Session,
    template: Template,
    extraction_service,
    logger
) -> Tuple[Dict, bool]:
    """
    Extract fields for a single template with error handling and rollback.
    
    Args:
        db: Database session
        template: Template model instance
        extraction_service: FieldExtractionService instance
        logger: Logger instance
    
    Returns:
        Tuple of (results_dict, success: bool)
        If success is False, any field changes have been rolled back.
    """
    from scripts.extract_template_fields import extract_and_store_template_fields
    
    # Use a savepoint to rollback only field extraction if it fails
    savepoint = db.begin_nested()
    try:
        results = extract_and_store_template_fields(
            db=db,
            template=template,
            extraction_service=extraction_service,
            auto_commit=False  # We'll handle commit/rollback here
        )
        
        # Check if extraction had errors
        if results.get("errors"):
            error_msg = f"Field extraction failed for template '{template.name}' (ID: {template.id})"
            logger.error(error_msg)
            for error in results["errors"]:
                logger.error(f"  - {error}")
            
            # Rollback any fields that were added for this template
            savepoint.rollback()
            return results, False
        else:
            # Success - commit the savepoint (fields are now saved)
            savepoint.commit()
            return results, True
            
    except Exception as e:
        # Rollback any partial field additions
        savepoint.rollback()
        error_msg = f"Unexpected error during field extraction for template '{template.name}' (ID: {template.id}): {str(e)}"
        logger.error(error_msg, exc_info=True)
        results = {
            "template_id": template.id,
            "template_name": template.name,
            "errors": [str(e)]
        }
        return results, False


def seed_data(db: Session):
    """Seed initial data: law firms, case types, templates, and fields"""
    
    # ============================================
    # 1. LAW FIRMS
    # ============================================
    print("\nSeeding law firms...")
    
    # Check if firms already exist
    firm1 = db.query(LawFirm).filter(LawFirm.code == "COHAN").first()
    if not firm1:
        firm1 = LawFirm(name="COHAN LAW, PLLC", code="COHAN")
        db.add(firm1)
        db.flush()
        print(f"✓ Created firm: {firm1.name} (ID: {firm1.id})")
    else:
        print(f"✓ Firm already exists: {firm1.name} (ID: {firm1.id})")
    
    firm2 = db.query(LawFirm).filter(LawFirm.code == "SMITH").first()
    if not firm2:
        firm2 = LawFirm(name="Smith & Associates", code="SMITH")
        db.add(firm2)
        db.flush()
        print(f"✓ Created firm: {firm2.name} (ID: {firm2.id})")
    else:
        print(f"✓ Firm already exists: {firm2.name} (ID: {firm2.id})")
    
    db.flush()  # Ensure IDs are available
    
    # ============================================
    # 2. CASE TYPES
    # ============================================
    print("\nSeeding case types...")
    
    # Check if case types already exist
    case_type1 = db.query(CaseType).filter(CaseType.code == "PREMISES").first()
    if not case_type1:
        case_type1 = CaseType(
            name="Premises Liability", 
            code="PREMISES", 
            description="Slip and fall, premises accidents"
        )
        db.add(case_type1)
        db.flush()
        print(f"✓ Created case type: {case_type1.name} (ID: {case_type1.id})")
    else:
        print(f"✓ Case type already exists: {case_type1.name} (ID: {case_type1.id})")
    
    case_type2 = db.query(CaseType).filter(CaseType.code == "PI").first()
    if not case_type2:
        case_type2 = CaseType(
            name="Personal Injury", 
            code="PI", 
            description="General personal injury cases"
        )
        db.add(case_type2)
        db.flush()
        print(f"✓ Created case type: {case_type2.name} (ID: {case_type2.id})")
    else:
        print(f"✓ Case type already exists: {case_type2.name} (ID: {case_type2.id})")
    
    case_type3 = db.query(CaseType).filter(CaseType.code == "MED_MAL").first()
    if not case_type3:
        case_type3 = CaseType(
            name="Medical Malpractice", 
            code="MED_MAL", 
            description="Medical malpractice cases"
        )
        db.add(case_type3)
        db.flush()
        print(f"✓ Created case type: {case_type3.name} (ID: {case_type3.id})")
    else:
        print(f"✓ Case type already exists: {case_type3.name} (ID: {case_type3.id})")
    
    db.flush()  # Ensure IDs are available
    
    # ============================================
    # 3. TEMPLATES
    # ============================================
    print("\nSeeding templates...")
    
    templates_data = [
        {
            "law_firm_id": firm1.id,
            "case_type_id": case_type1.id,
            "name": "Premises Liability - 1 Plt. and 1 Deft.",
            "file_path": "templates/Premises - 1 plt. and 1deft_.docx",
            "version": 1
        },
        {
            "law_firm_id": firm1.id,
            "case_type_id": case_type2.id,
            "name": "MVA - 1 Plt. and 1 Deft.",
            "file_path": "templates/MVA - 1 plt. and 1 deft_.docx",
            "version": 1
        },
        {
            "law_firm_id": firm1.id,
            "case_type_id": case_type3.id,
            "name": "Medical Malpractice - 1 Plt. and 1 Deft.",
            "file_path": "templates/Medical Malpractice - 1 plt. and 1 deft_.docx",
            "version": 1
        }
    ]
    
    # ============================================
    # 4. CREATE TEMPLATES WITH AUTO FIELD EXTRACTION
    # ============================================
    print("\nCreating/updating templates with automatic field extraction...")
    
    from app.services.template_service import create_template_with_auto_extraction
    
    templates = []
    total_fields = 0
    extraction_errors = []
    skipped_templates = []
    
    for t_data in templates_data:
        # Check if template already exists (by unique constraint: law_firm_id, case_type_id, version)
        existing_template = db.query(Template).filter(
            Template.law_firm_id == t_data["law_firm_id"],
            Template.case_type_id == t_data["case_type_id"],
            Template.version == t_data["version"]
        ).first()
        
        if existing_template:
            print(f"\n  Template already exists: {existing_template.name} (ID: {existing_template.id})")
            
            # Update file_path if it changed (e.g., .doc to .docx conversion)
            if existing_template.file_path != t_data["file_path"]:
                print(f"    Updating file path: {existing_template.file_path} -> {t_data['file_path']}")
                existing_template.file_path = t_data["file_path"]
                db.commit()
            
            # Check if template has fields - if not, try to extract them
            field_count = db.query(TemplateField).filter(
                TemplateField.template_id == existing_template.id
            ).count()
            
            if field_count == 0 and t_data["file_path"].endswith('.docx'):
                print(f"    Template has 0 fields - attempting automatic extraction...")
                from app.services.field_extraction import FieldExtractionService
                from scripts.extract_template_fields import extract_and_store_template_fields
                
                extraction_service = FieldExtractionService(db)
                results = extract_and_store_template_fields(
                    db=db,
                    template=existing_template,
                    extraction_service=extraction_service,
                    auto_commit=True
                )
                
                if results.get("errors"):
                    print(f"    ❌ Extraction failed: {results['errors'][0]}")
                    extraction_errors.append({
                        "template_id": existing_template.id,
                        "template_name": existing_template.name,
                        "errors": results.get("errors", ["Unknown error"])
                    })
                else:
                    fields_count = len(results.get("created_fields", [])) + len(results.get("existing_fields", []))
                    total_fields += fields_count
                    print(f"    ✓ Automatically extracted and inserted {fields_count} fields")
            else:
                print(f"    Skipping (already has {field_count} fields or not .docx)")
            
            templates.append(existing_template)
            skipped_templates.append(existing_template)
            continue
        
        # Template doesn't exist - create it with auto-extraction
        template = Template(**t_data)
        print(f"\n  Creating new template: {template.name}...")
        
        # Create template and automatically extract fields
        created_template, extraction_results, extraction_success = create_template_with_auto_extraction(
            db=db,
            template=template,
            auto_extract=True
        )
        
        templates.append(created_template)
        print(f"  ✓ Created template: {created_template.name} (ID: {created_template.id})")
        print(f"    Path: {created_template.file_path}")
        
        if extraction_results is not None:
            if extraction_success:
                fields_count = len(extraction_results.get("created_fields", [])) + len(extraction_results.get("existing_fields", []))
                total_fields += fields_count
                print(f"  ✓ Automatically extracted and inserted {fields_count} fields into database")
            else:
                extraction_errors.append({
                    "template_id": created_template.id,
                    "template_name": created_template.name,
                    "errors": extraction_results.get("errors", ["Unknown error"])
                })
                print(f"  ❌ Automatic extraction failed - template saved, fields rolled back")
        else:
            if not template.file_path.endswith('.docx'):
                print(f"  ⚠️  Skipped extraction: Only .docx supported")
            else:
                print(f"  ⚠️  Skipped extraction: File not found")
    
    created_count = len(templates) - len(skipped_templates)
    print(f"\n✓ Processed {len(templates)} templates ({created_count} new, {len(skipped_templates)} already existed)")
    print(f"✓ Extracted and inserted {total_fields} template fields automatically")
    
    # Report any extraction errors
    if extraction_errors:
        print(f"\n⚠️  WARNING: Field extraction failed for {len(extraction_errors)} template(s):")
        for error_info in extraction_errors:
            print(f"  - Template '{error_info['template_name']}' (ID: {error_info['template_id']})")
            for err in error_info['errors']:
                print(f"    Error: {err}")
        print(f"\n  Templates were created but field extraction must be run manually.")
        if extraction_errors:
            print(f"  Run: python -m scripts.extract_template_fields {extraction_errors[0]['template_id']}")

    # ============================================
    # 5. TEST SESSION (for frontend development)
    # ============================================
    print("\nSeeding test session (if none exist)...")
    import uuid as uuid_mod
    existing_session = db.query(SessionModel).first()
    if not existing_session and templates:
        template = templates[0]
        session_uuid = str(uuid_mod.uuid4())
        test_session = SessionModel(
            uuid=session_uuid,
            template_id=template.id,
            status=SessionStatus.CREATED,
        )
        db.add(test_session)
        db.flush()
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
            "current_month_year": "January 2024",
        }
        template_fields = db.query(TemplateField).filter(TemplateField.template_id == template.id).all()
        for tf in template_fields:
            value = sample_values.get(tf.field_key) or f"Sample {tf.display_name}"
            fv = FieldValue(
                session_id=test_session.id,
                template_field_id=tf.id,
                extracted_value=value,
                is_missing=False,
                status=FieldValueStatus.EXTRACTED,
            )
            db.add(fv)
        db.commit()
        print(f"✓ Created test session: {session_uuid} with {len(template_fields)} field values")
    else:
        print(f"✓ Test session already exists or no templates; skipping")

    print("\n✅ Database initialization complete!")
    
    # Get total field count from database (not just newly extracted)
    total_fields_in_db = db.query(TemplateField).count()
    
    print(f"\nSummary:")
    print(f"  - Law Firms: 2")
    print(f"  - Case Types: 3")
    print(f"  - Templates: {len(templates)}")
    print(f"  - Template Fields (total in DB): {total_fields_in_db}")
    if total_fields > 0:
        print(f"  - Template Fields (newly extracted this run): {total_fields}")
    print(f"\n⚠️  Next Steps:")
    print(f"  1. Review app/db/field_definitions.py to update field metadata")


def init_db():
    """Initialize database: create tables and seed data"""
    try:
        create_tables()
        
        db = SessionLocal()
        try:
            # Always run seed_data - it will skip existing records and add new ones
            seed_data(db)
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    init_db()
