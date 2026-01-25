#!/usr/bin/env python3
"""
Recreate MVA template with automatic field extraction
"""
from app.db.base import SessionLocal
from app.db.models import Template, TemplateField, LawFirm, CaseType
from app.services.template_service import create_template_with_auto_extraction

db = SessionLocal()
try:
    # Find the MVA template (ID: 2)
    old_template = db.query(Template).filter(Template.id == 2).first()
    
    if old_template:
        print(f"Found existing MVA template: {old_template.name} (ID: {old_template.id})")
        print("Deleting old template and its fields...")
        
        # Delete the template (fields will be deleted via CASCADE)
        db.delete(old_template)
        db.commit()
        print("✓ Old template deleted")
    else:
        print("No existing MVA template found")
    
    # Get the law firm and case type
    firm = db.query(LawFirm).filter(LawFirm.code == "COHAN").first()
    case_type = db.query(CaseType).filter(CaseType.code == "PI").first()
    
    if not firm or not case_type:
        print("❌ Error: COHAN firm or PI case type not found!")
        exit(1)
    
    print(f"\nCreating new MVA template with automatic field extraction...")
    
    # Create new template using the service function (automatic extraction)
    new_template = Template(
        law_firm_id=firm.id,
        case_type_id=case_type.id,
        name="MVA - 1 Plt. and 1 Deft.",
        file_path="templates/MVA - 1 plt. and 1 deft_.docx",
        version=1
    )
    
    created_template, extraction_results, extraction_success = create_template_with_auto_extraction(
        db=db,
        template=new_template,
        auto_extract=True
    )
    
    print(f"\n✓ Created new template: {created_template.name} (ID: {created_template.id})")
    
    if extraction_results is not None:
        if extraction_success:
            fields_count = len(extraction_results.get("created_fields", [])) + len(extraction_results.get("existing_fields", []))
            print(f"✓ Automatically extracted and inserted {fields_count} fields into database")
        else:
            print(f"❌ Automatic extraction failed:")
            for error in extraction_results.get("errors", []):
                print(f"  - {error}")
    else:
        print("⚠️  Extraction was skipped (file not found or not .docx)")
    
    print("\n✅ Done!")
    
finally:
    db.close()
