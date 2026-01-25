"""
Centralized metadata for all known template fields.
Developers should add new field definitions here.
"""

FIELD_DEFINITIONS = {
    # Common fields
    "case_county": {
        "display_name": "Case County",
        "description": "County where case is filed",
        "expected_format": "County Name",
    },
    "plaintiff_name": {
        "display_name": "Plaintiff Name",
        "description": "Full legal name of the plaintiff",
        "expected_format": "Full Name",
    },
    "defendant_name": {
        "display_name": "Defendant Name",
        "description": "Full legal name of the primary defendant",
        "expected_format": "Full Name",
    },
    "venue_bases_on": {
        "display_name": "Venue Basis",
        "description": "Basis for venue selection",
        "expected_format": "Text",
    },
    "venue_street_address": {
        "display_name": "Venue Street Address",
        "description": "Street address for venue",
        "expected_format": "Street Address",
    },
    "venue_county": {
        "display_name": "Venue County",
        "description": "County for venue",
        "expected_format": "County Name",
    },
    "venue_state": {
        "display_name": "Venue State",
        "description": "State for venue",
        "expected_format": "State Name or Abbreviation",
    },
    "current_month_year": {
        "display_name": "Current Month/Year",
        "description": "Current month and year for document dating",
        "expected_format": "Month Year",
    },
    "hisher": {
        "display_name": "His/Her",
        "description": "Pronoun (his or her)",
        "expected_format": "his or her",
    },
    "heshe": {
        "display_name": "He/She",
        "description": "Pronoun (he or she)",
        "expected_format": "he or she",
    },
    
    # Premises specific
    "loa": {
        "display_name": "LOA (Location of Accident)",
        "description": "Location of accident or premises identifier",
        "expected_format": "Address or Location Identifier",
    },
    "loa_county": {
        "display_name": "LOA County",
        "description": "County where accident occurred",
        "expected_format": "County Name",
    },
    "loa_state": {
        "display_name": "LOA State",
        "description": "State where accident occurred",
        "expected_format": "State Name or Abbreviation",
    },
    "date_of_accident": {
        "display_name": "Date of Accident",
        "description": "Date when the incident occurred",
        "expected_format": "MM/DD/YYYY",
    },

    # Medical Malpractice specific
    "body_part_name": {
        "display_name": "Body Part",
        "description": "Affected body part in the malpractice claim",
        "expected_format": "Text (e.g., left knee)",
    },
    "start_date_service": {
        "display_name": "Service Start Date",
        "description": "Date when medical service started",
        "expected_format": "MM/DD/YYYY",
    },
    "end_date_service": {
        "display_name": "Service End Date",
        "description": "Date when medical service ended",
        "expected_format": "MM/DD/YYYY",
    },
    
    # Generic Location fields (for various entities)
    "plaintiff_county": {
        "display_name": "Plaintiff County",
        "description": "County where plaintiff resides",
        "expected_format": "County Name",
    },
    "plaintiff_city": {
        "display_name": "Plaintiff City",
        "description": "City where plaintiff resides",
        "expected_format": "City Name",
    },
    "plaintiff_state": {
        "display_name": "Plaintiff State",
        "description": "State where plaintiff resides",
        "expected_format": "State Name or Abbreviation",
    },
    "defendant_street_address": {
        "display_name": "Defendant Street Address",
        "description": "Street address of the primary defendant",
        "expected_format": "Street Address",
    },
    "defendant_city": {
        "display_name": "Defendant City",
        "description": "City where primary defendant is located",
        "expected_format": "City Name",
    },
    "defendant_state": {
        "display_name": "Defendant State",
        "description": "State where primary defendant is located",
        "expected_format": "State Name or Abbreviation",
    },
    "defendant_zip_code": {
        "display_name": "Defendant ZIP Code",
        "description": "ZIP code of the primary defendant",
        "expected_format": "ZIP Code",
    },
    "defendant_county": {
        "display_name": "Defendant County",
        "description": "County where primary defendant is located",
        "expected_format": "County Name",
    },
}

def get_field_metadata(field_key: str) -> dict:
    """Get metadata for a field key, or return default values if not found"""
    return FIELD_DEFINITIONS.get(field_key, {
        "display_name": field_key.replace("_", " ").title(),
        "description": "Auto-extracted field",
        "expected_format": "Text"
    })
