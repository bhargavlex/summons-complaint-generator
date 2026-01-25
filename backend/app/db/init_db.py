"""
Database initialization script
Creates all tables and seeds initial data for COHAN LAW + Premises
"""
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.base import Base, engine, SessionLocal
from app.db.models import (
    LawFirm,
    CaseType,
    Template,
    TemplateField,
)


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")


def seed_data(db: Session):
    """Seed initial data: law firms, case types, templates, and fields"""
    
    # ============================================
    # 1. LAW FIRMS
    # ============================================
    print("\nSeeding law firms...")
    
    firm1 = LawFirm(name="COHAN LAW, PLLC", code="COHAN")
    firm2 = LawFirm(name="Smith & Associates", code="SMITH")
    
    db.add(firm1)
    db.add(firm2)
    db.flush()  # Get IDs
    
    print(f"✓ Created firm: {firm1.name} (ID: {firm1.id})")
    print(f"✓ Created firm: {firm2.name} (ID: {firm2.id})")
    
    # ============================================
    # 2. CASE TYPES
    # ============================================
    print("\nSeeding case types...")
    
    case_type1 = CaseType(
        name="Premises Liability", 
        code="PREMISES", 
        description="Slip and fall, premises accidents"
    )
    case_type2 = CaseType(
        name="Personal Injury", 
        code="PI", 
        description="General personal injury cases"
    )
    case_type3 = CaseType(
        name="Medical Malpractice", 
        code="MED_MAL", 
        description="Medical malpractice cases"
    )
    
    db.add(case_type1)
    db.add(case_type2)
    db.add(case_type3)
    db.flush()
    
    print(f"✓ Created case type: {case_type1.name} (ID: {case_type1.id})")
    print(f"✓ Created case type: {case_type2.name} (ID: {case_type2.id})")
    print(f"✓ Created case type: {case_type3.name} (ID: {case_type3.id})")
    
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
            "file_path": "templates/MVA - 1 plt. and 1 deft_.doc",
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
    
    templates = []
    for t_data in templates_data:
        template = Template(**t_data)
        db.add(template)
        templates.append(template)
    
    db.flush()  # Get IDs
    
    for template in templates:
        print(f"✓ Created template: {template.name} (ID: {template.id})")
        print(f"  Path: {template.file_path}")
    
    # ============================================
    # 4. TEMPLATE FIELDS (Generalized Extraction)
    # ============================================
    print("\nExtracting and seeding fields for all templates...")
    
    # Import the extraction logic locally to avoid circular dependencies
    from scripts.extract_template_fields import extract_and_store_template_fields
    from app.services.field_extraction import FieldExtractionService
    
    extraction_service = FieldExtractionService(db)
    
    total_fields = 0
    for template in templates:
        # Check if file exists before trying to extract
        file_path = Path(template.file_path)
        if not file_path.is_absolute():
            file_path = Path(__file__).parent.parent.parent / file_path
            
        if file_path.exists() and template.file_path.endswith('.docx'):
            print(f"  Processing: {template.name}...")
            results = extract_and_store_template_fields(
                db=db,
                template=template,
                extraction_service=extraction_service
            )
            total_fields += len(results["created_fields"]) + len(results["existing_fields"])
        else:
            if not template.file_path.endswith('.docx'):
                print(f"  ⚠️  Skipping {template.name}: Only .docx supported for extraction.")
            else:
                print(f"  ⚠️  Skipping {template.name}: File not found at {file_path}")

    db.commit()
    
    print(f"✓ Created/Verified {total_fields} template fields across templates")
    print("\n✅ Database initialization complete!")
    print(f"\nSummary:")
    print(f"  - Law Firms: 2")
    print(f"  - Case Types: 3")
    print(f"  - Templates: {len(templates)}")
    print(f"  - Template Fields: {total_fields}")
    print(f"\n⚠️  Next Steps:")
    print(f"  1. Review app/db/field_definitions.py to update field metadata")


def init_db():
    """Initialize database: create tables and seed data"""
    try:
        create_tables()
        
        db = SessionLocal()
        try:
            # Check if data already exists
            existing_firm = db.query(LawFirm).first()
            if existing_firm:
                print("\n⚠️  Database already seeded. Skipping seed data.")
                print("   To reset, drop and recreate the database.")
                return
            
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
