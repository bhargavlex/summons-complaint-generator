from app.db.base import SessionLocal
from app.db.models import LawFirm, CaseType, Template, TemplateField, Session, Document, FieldValue
import sys

def print_header(title):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def view_all_tables():
    db = SessionLocal()
    try:
        # 1. Law Firms
        print_header("LAW FIRMS")
        firms = db.query(LawFirm).all()
        print(f"{'ID':<4} | {'Name':<35} | {'Code':<15}")
        print("-" * 80)
        for f in firms:
            print(f"{f.id:<4} | {f.name:<35} | {f.code:<15}")
        print(f"\nTotal Law Firms: {len(firms)}")

        # 2. Case Types
        print_header("CASE TYPES")
        case_types = db.query(CaseType).all()
        print(f"{'ID':<4} | {'Name':<25} | {'Code':<15}")
        print("-" * 80)
        for ct in case_types:
            print(f"{ct.id:<4} | {ct.name:<25} | {ct.code:<15}")
        print(f"\nTotal Case Types: {len(case_types)}")

        # 3. Templates
        print_header("TEMPLATES")
        templates = db.query(Template).all()
        print(f"{'ID':<4} | {'Name':<40} | {'Firm ID':<8} | {'Type ID':<8}")
        print("-" * 80)
        for t in templates:
            display_name = (t.name[:37] + '..') if len(t.name) > 37 else t.name
            print(f"{t.id:<4} | {display_name:<40} | {t.law_firm_id:<8} | {t.case_type_id:<8}")
        print(f"\nTotal Templates: {len(templates)}")

        # 4. Template Fields (Summary only if too many)
        print_header("TEMPLATE FIELDS (First 20)")
        fields = db.query(TemplateField).limit(20).all()
        total_fields = db.query(TemplateField).count()
        print(f"{'ID':<4} | {'Tpl ID':<6} | {'Field Key':<20} | {'Placeholder':<25} | {'Display Name':<25} | {'Format':<15}")
        print("-" * 110)
        for f in fields:
            # Truncate strings to keep table manageable
            pk = (f.placeholder[:22] + '..') if len(f.placeholder) > 22 else f.placeholder
            dn = (f.display_name[:22] + '..') if len(f.display_name) > 22 else f.display_name
            fmt = (f.expected_format[:12] + '..') if f.expected_format and len(f.expected_format) > 12 else (f.expected_format or "")
            
            print(f"{f.id:<4} | {f.template_id:<6} | {f.field_key:<20} | {pk:<25} | {dn:<25} | {fmt:<15}")
        
        if total_fields > 20:
            print(f"... and {total_fields - 20} more fields.")
        print(f"\nTotal Fields in DB: {total_fields}")

        # 5. Sessions
        print_header("SESSIONS")
        sessions = db.query(Session).all()
        print(f"{'ID':<4} | {'UUID':<38} | {'Status':<15}")
        print("-" * 80)
        for s in sessions:
            print(f"{s.id:<4} | {s.uuid:<38} | {s.status.value:<15}")
        print(f"\nTotal Sessions: {len(sessions)}")

    finally:
        db.close()

if __name__ == "__main__":
    view_all_tables()
