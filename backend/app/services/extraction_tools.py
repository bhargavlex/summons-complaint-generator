"""
Extraction tools for legal document field extraction.
Contains field definitions and tool generation functions.
"""

from typing import Dict, List


# Field definitions for legal document extraction
FIELD_DEFINITIONS = {
    'Venue_Street_Address_': {
        'type': 'string',
        'description': 'The street address of the venue/court where the case will be filed. If not found, return empty string.',
        'required': True
    },
    'Plaintiff_County_': {
        'type': 'string',
        'description': 'The county where the plaintiff resides. If not found, return empty string.',
        'required': True
    },
    'Defendant_City': {
        'type': 'string',
        'description': 'The city where the defendant resides. If not found, return empty string.',
        'required': True
    },
    'Defendant_Street_Address_': {
        'type': 'string',
        'description': 'The complete street address of the defendant including street number, street name, and any apartment/unit number. If not found, return empty string.',
        'required': True
    },
    'Defendant_County': {
        'type': 'string',
        'description': 'The county where the defendant resides. If not found, return empty string.',
        'required': True
    },
    'Currtent_Month_Year': {
        'type': 'string',
        'description': 'Current month and year in format like "January 2024" or "01/2024". Extract from document if present, otherwise return empty string.',
        'required': True
    },
    'Plaintiff_name_': {
        'type': 'string',
        'description': 'Full legal name of the plaintiff as it appears in the document. If not found, return empty string.',
        'required': True
    },
    'LOA': {
        'type': 'string',
        'description': 'Letter of Authorization or Location of Accident. Extract the location or authorization details. If not found, return empty string.',
        'required': True
    },
    'hisher': {
        'type': 'string',
        'description': 'Pronoun "his" or "her" based on plaintiff gender. Determine from document context. If not found, return empty string.',
        'required': True
    },
    'heshe': {
        'type': 'string',
        'description': 'Pronoun "he" or "she" based on plaintiff gender. Determine from document context. If not found, return empty string.',
        'required': True
    },
    'Defendant_State': {
        'type': 'string',
        'description': 'The state where the defendant resides. Use 2-letter abbreviation preferred (e.g., "NY", "CA"). If not found, return empty string.',
        'required': True
    },
    'Defendant_name': {
        'type': 'string',
        'description': 'Full legal name of the defendant as it appears in the document. If not found, return empty string.',
        'required': True
    },
    'Defendant_Zip_code': {
        'type': 'string',
        'description': 'ZIP code of the defendant address. Extract the 5-digit or ZIP+4 format. If not found, return empty string.',
        'required': True
    },
    'Plaintiff_State_': {
        'type': 'string',
        'description': 'The state where the plaintiff resides. Use 2-letter abbreviation preferred (e.g., "NY", "CA"). If not found, return empty string.',
        'required': True
    },
    'Case_County': {
        'type': 'string',
        'description': 'The county where the case will be filed. If not found, return empty string.',
        'required': True
    },
    'LOA__County': {
        'type': 'string',
        'description': 'County where the accident/location of authorization occurred. If not found, return empty string.',
        'required': True
    },
    'Date_of_accident': {
        'type': 'string',
        'description': 'Date when the accident occurred in MM/DD/YYYY format. If not found, return empty string.',
        'required': True
    },
    'Venue_bases_on': {
        'type': 'string',
        'description': 'Basis for venue selection (e.g., "where accident occurred", "where defendant resides", "where plaintiff resides"). If not found, return empty string.',
        'required': True
    },
    'Venue_County_State': {
        'type': 'string',
        'description': 'County and state of the venue (e.g., "New York County, New York" or "Kings County, NY"). If not found, return empty string.',
        'required': True
    },
    'LOA__State': {
        'type': 'string',
        'description': 'State where the accident/location of authorization occurred. Use 2-letter abbreviation preferred (e.g., "NY", "CA"). If not found, return empty string.',
        'required': True
    }
}


def generate_extraction_tool(missing_fields: List[str]) -> Dict:
    """
    Generate dynamic tool/schema for extraction based on missing fields.
    
    Args:
        missing_fields: List of field names that still need to be extracted
        
    Returns:
        Tool definition dictionary for OpenAI function calling
    """
    properties = {}
    required = []
    
    for field_name in missing_fields:
        if field_name in FIELD_DEFINITIONS:
            field_def = FIELD_DEFINITIONS[field_name]
            properties[field_name] = {
                "type": field_def['type'],
                "description": field_def['description']
            }
            if field_def.get('required', False):
                required.append(field_name)
        else:
            # Fallback for unknown fields
            properties[field_name] = {
                "type": "string",
                "description": f"Extract the value for {field_name}. If not found, return empty string."
            }
            required.append(field_name)
    
    tool = {
        "type": "function",
        "function": {
            "name": "extract_fields",
            "description": "Extract field values from the legal document. Only extract fields that are clearly and explicitly present in the document. If a field is not found or unclear, return an empty string for that field. Do not make assumptions or guess values.",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }
    
    return tool


def get_all_fields() -> List[str]:
    """
    Get list of all defined field names.
    
    Returns:
        List of all field names
    """
    return list(FIELD_DEFINITIONS.keys())
