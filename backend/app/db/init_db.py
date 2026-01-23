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
    # 3. TEMPLATE (Premises Liability for COHAN LAW)
    # ============================================
    print("\nSeeding template...")
    
    # Template file path (user needs to upload this)
    template_path = "templates/cohan/premises/summons_complaint.docx"
    
    template = Template(
        law_firm_id=firm1.id,
        case_type_id=case_type1.id,
        name="Premises Liability - Summons & Complaint",
        file_path=template_path,
        version=1
    )
    
    db.add(template)
    db.flush()
    
    print(f"✓ Created template: {template.name} (ID: {template.id})")
    print(f"  Template path: {template_path}")
    print(f"  ⚠️  Make sure the template file exists at this path!")
    
    # ============================================
    # 4. TEMPLATE FIELDS (All 20 placeholders from PDF)
    # ============================================
    print("\nSeeding template fields...")
    
    fields_data = [
        {
            "field_key": "case_county",
            "placeholder": "«Case_County»",
            "display_name": "Case County",
            "description": "County where case is filed",
            "expected_format": "County Name",
            "field_order": 1,
        },
        {
            "field_key": "plaintiff_name",
            "placeholder": "«Plaintiff_name_»",
            "display_name": "Plaintiff Name",
            "description": "Full legal name of the plaintiff",
            "expected_format": "Full Name",
            "field_order": 2,
        },
        {
            "field_key": "defendant_name",
            "placeholder": "«Defendant_name»",
            "display_name": "Defendant Name",
            "description": "Full legal name of the defendant",
            "expected_format": "Full Name",
            "field_order": 3,
        },
        {
            "field_key": "venue_bases_on",
            "placeholder": "«Venue_bases_on»",
            "display_name": "Venue Basis",
            "description": "Basis for venue selection",
            "expected_format": "Text",
            "field_order": 4,
        },
        {
            "field_key": "venue_street_address",
            "placeholder": "«Venue_Street_Address_»",
            "display_name": "Venue Street Address",
            "description": "Street address for venue",
            "expected_format": "Street Address",
            "field_order": 5,
        },
        {
            "field_key": "venue_county_state",
            "placeholder": "«Venue_County_State»",
            "display_name": "Venue County and State",
            "description": "County and state for venue",
            "expected_format": "County, State",
            "field_order": 6,
        },
        {
            "field_key": "current_month_year",
            "placeholder": "«Current_Month_Year»",
            "display_name": "Current Month/Year",
            "description": "Current month and year for document dating",
            "expected_format": "Month Year (e.g., January 2024)",
            "field_order": 7,
        },
        {
            "field_key": "defendant_street_address",
            "placeholder": "«Defendant_Street_Address_»",
            "display_name": "Defendant Street Address",
            "description": "Street address of the defendant",
            "expected_format": "Street Address",
            "field_order": 8,
        },
        {
            "field_key": "defendant_city",
            "placeholder": "«Defendant_City»",
            "display_name": "Defendant City",
            "description": "City where defendant is located",
            "expected_format": "City Name",
            "field_order": 9,
        },
        {
            "field_key": "defendant_state",
            "placeholder": "«Defendant_State»",
            "display_name": "Defendant State",
            "description": "State where defendant is located",
            "expected_format": "State Name or Abbreviation",
            "field_order": 10,
        },
        {
            "field_key": "defendant_zip_code",
            "placeholder": "«Defendant_Zip_code»",
            "display_name": "Defendant ZIP Code",
            "description": "ZIP code of the defendant",
            "expected_format": "ZIP Code (5 or 9 digits)",
            "field_order": 11,
        },
        {
            "field_key": "defendant_county",
            "placeholder": "«Defendant_County»",
            "display_name": "Defendant County",
            "description": "County where defendant is located",
            "expected_format": "County Name",
            "field_order": 12,
        },
        {
            "field_key": "plaintiff_county",
            "placeholder": "«Plaintiff_County_»",
            "display_name": "Plaintiff County",
            "description": "County where plaintiff resides",
            "expected_format": "County Name",
            "field_order": 13,
        },
        {
            "field_key": "plaintiff_state",
            "placeholder": "«Plaintiff_State_»",
            "display_name": "Plaintiff State",
            "description": "State where plaintiff resides",
            "expected_format": "State Name or Abbreviation",
            "field_order": 14,
        },
        {
            "field_key": "date_of_accident",
            "placeholder": "«Date_of_accident»",
            "display_name": "Date of Accident",
            "description": "Date when the incident occurred",
            "expected_format": "MM/DD/YYYY",
            "field_order": 15,
        },
        {
            "field_key": "loa",
            "placeholder": "«LOA»",
            "display_name": "LOA (Location of Accident)",
            "description": "Location of accident or premises identifier",
            "expected_format": "Address or Location Identifier",
            "field_order": 16,
        },
        {
            "field_key": "loa_county",
            "placeholder": "«LOA_County»",
            "display_name": "LOA County",
            "description": "County where accident occurred",
            "expected_format": "County Name",
            "field_order": 17,
        },
        {
            "field_key": "loa_state",
            "placeholder": "«LOA_State»",
            "display_name": "LOA State",
            "description": "State where accident occurred",
            "expected_format": "State Name or Abbreviation",
            "field_order": 18,
        },
        {
            "field_key": "hisher",
            "placeholder": "«hisher»",
            "display_name": "His/Her",
            "description": "Pronoun: his or her (based on plaintiff gender)",
            "expected_format": "his or her",
            "field_order": 19,
        },
        {
            "field_key": "heshe",
            "placeholder": "«heshe»",
            "display_name": "He/She",
            "description": "Pronoun: he or she (based on plaintiff gender)",
            "expected_format": "he or she",
            "field_order": 20,
        },
    ]
    
    for field_data in fields_data:
        field = TemplateField(
            template_id=template.id,
            **field_data
        )
        db.add(field)
    
    db.commit()
    
    print(f"✓ Created {len(fields_data)} template fields")
    print("\n✅ Database initialization complete!")
    print(f"\nSummary:")
    print(f"  - Law Firms: 2")
    print(f"  - Case Types: 3")
    print(f"  - Templates: 1 (Premises Liability for COHAN LAW)")
    print(f"  - Template Fields: {len(fields_data)}")
    print(f"\n⚠️  Next Steps:")
    print(f"  1. Upload template file to: {template_path}")
    print(f"  2. Create the directory structure if it doesn't exist")


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
