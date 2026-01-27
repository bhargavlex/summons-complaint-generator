"""
Extraction tools for legal document field extraction.
Contains field definitions and tool generation functions.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid


# Phase 1 fields
PHASE1_FIELDS = [
    "Case_County",
    "Plaintiff_name_",
    "Plaintiff_State_",
    "Plaintiff_County_",
    "Defendant_name",
    "Defendant_Street_Address_",
    "Defendant_City",
    "Defendant_State",
    "Defendant_Zip_code",
    "hisher",
    "heshe"
]



# Field definitions for legal document extraction
# Each field uses nested schema: {value, confidence, reasoning}
FIELD_DEFINITIONS = {

    "Case_County": {
        "description": "Court filing county from the caption header (e.g., 'COUNTY OF RICHMOND'). This is the COURT county where the case is filed, NOT the defendant's county. Must be ALL CAPS."
    },

    "Plaintiff_name_": {
        "description": "Full plaintiff name exactly as shown in caption (UPPERCASE preferred)."
    },

    "Plaintiff_County_": {
        "description": "Plaintiff residence county as full word. If not explicitly stated in the document, infer from the plaintiff's city and state address information. Use confidence 0.75-0.85 for inferred values based on city/state context."
    },

    "Plaintiff_State_": {
        "description": "Plaintiff residence state FULL NAME. Do NOT abbreviate."
    },

    "Defendant_name": {
        "description": "All defendant entities exactly as captioned. If multiple, join with ' and '."
    },

    "Defendant_Street_Address_": {
        "description": "Primary defendant street address only."
    },

    "Defendant_City": {
        "description": "Defendant city."
    },

    "Defendant_State": {
        "description": "Defendant state FULL NAME."
    },

    "Defendant_Zip_code": {
        "description": "5 digit ZIP only."
    },

    "Defendant_County": {
        "description": "Defendant business county."
    },

    "Venue_bases_on": {
        "description": "Legal basis for venue (e.g., defendant’s place of business, location of accident, plaintiff residence)."
    },

    "Venue_Street_Address_": {
        "description": "Street address explicitly stated in venue paragraph."
    },

    "Venue_County_State": {
        "description": "Venue location formatted as '<City>, <County> County, <State>'."
    },

    "Currtent_Month_Year": {
        "description": "Current month in legal template format '<Month>_____, <Year>'."
    },

    "Date_of_accident": {
        "description": "Accident date in narrative legal format '<Month> <Day>, <Year>'."
    },

    "LOA": {
        "description": "Full postal accident address (street, city, state, zip) ONLY if accident location is explicitly stated."
    },

    "LOA__County": {
        "description": "County where accident occurred."
    },

    "LOA__State": {
        "description": "State where accident occurred (FULL NAME)."
    },

    "hisher": {
        "description": "Lowercase possessive pronoun: his or her."
    },

    "heshe": {
        "description": "Lowercase subject pronoun: he or she."
    }
}




def generate_extraction_tool(missing_fields: List[str]) -> Dict:
    """
    Generate dynamic tool/schema for extraction based on missing fields.
    Uses nested schema: each field returns {value, confidence, reasoning}
    
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
            # Nested schema: each field is an object with value, confidence, reasoning
            properties[field_name] = {
                "type": "object",
                "description": field_def['description'],
                "properties": {
                    "value": {
                        "type": "string",
                        "description": "The extracted value. Return empty string if not found."
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score from 0.0 to 1.0. 1.0 = Explicit text in document. 0.5 = Inferred from context. 0.0 = Not found or ambiguous."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Quote the text from the document or explain why you chose this value. If not found, state 'Not found in document'."
                    }
                },
                "required": ["value", "confidence", "reasoning"]
            }
            if field_def.get('required', False):
                required.append(field_name)
        else:
            # Fallback for unknown fields
            properties[field_name] = {
                "type": "object",
                "description": f"Extract the value for {field_name}. If not found, return empty string for value and 0.0 for confidence.",
                "properties": {
                    "value": {"type": "string", "description": "The extracted value. Return empty string if not found."},
                    "confidence": {"type": "number", "description": "Confidence score from 0.0 to 1.0."},
                    "reasoning": {"type": "string", "description": "Explanation or quote from document."}
                },
                "required": ["value", "confidence", "reasoning"]
            }
            required.append(field_name)
    
    tool = {
        "type": "function",
        "function": {
            "name": "extract_fields",
            "description": "Extract field values from the legal document with confidence scores. Follow each field's description carefully - some fields allow inference from context (use confidence 0.75-0.85 for inferred values). If a field is truly not found or ambiguous, return empty string with confidence 0.0.",
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


def get_phase1_fields() -> List[str]:
    """
    Get list of phase 1 fields.
    
    Returns:
        List of phase 1 fields
    """
    return PHASE1_FIELDS

class FieldStatus(str, Enum):
    """Status of a field in the extraction process."""
    PENDING_REVIEW = "PENDING_REVIEW"  # Extracted, awaiting user approval
    APPROVED = "APPROVED"  # User confirmed correct - locked for Phase 3
    EMPTY = "EMPTY"  # Not found or ambiguous - target for Phase 3


@dataclass
class ExtractedField:
    """Represents a single extracted field with metadata."""
    value: str
    confidence: float
    reasoning: str
    status: FieldStatus = FieldStatus.PENDING_REVIEW
    source_doc: Optional[str] = None
    iteration: int = 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "value": self.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "status": self.status.value,
            "source_doc": self.source_doc
        }


@dataclass
class ExtractionState:
    """
    Single source of truth for extraction state.
    Tracks all fields, their values, confidence, and status.
    """
    case_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    iteration: int = 1
    fields: Dict[str, ExtractedField] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize all fields as EMPTY if not already set."""
        all_field_names = get_all_fields()
        for field_name in all_field_names:
            if field_name not in self.fields:
                self.fields[field_name] = ExtractedField(
                    value="",
                    confidence=0.0,
                    reasoning="",
                    status=FieldStatus.EMPTY
                )
    
    def update_field(
        self,
        field_name: str,
        value: str,
        confidence: float,
        reasoning: str,
        source_doc: Optional[str] = None
    ):
        """Update a field with new extraction results."""
        if field_name not in self.fields:
            self.fields[field_name] = ExtractedField(
                value=value,
                confidence=confidence,
                reasoning=reasoning,
                status=FieldStatus.PENDING_REVIEW,
                source_doc=source_doc,
                iteration=self.iteration
            )
        else:
            # Only update if confidence is higher or field was empty
            current = self.fields[field_name]
            if current.status != FieldStatus.APPROVED:
                if confidence > current.confidence or current.status == FieldStatus.EMPTY:
                    self.fields[field_name].value = value
                    self.fields[field_name].confidence = confidence
                    self.fields[field_name].reasoning = reasoning
                    self.fields[field_name].status = FieldStatus.PENDING_REVIEW
                    if source_doc:
                        self.fields[field_name].source_doc = source_doc
                    self.fields[field_name].iteration = self.iteration
    
    def approve_fields(self, field_names: List[str]):
        """Mark fields as APPROVED (locked for Phase 3)."""
        for field_name in field_names:
            if field_name in self.fields:
                self.fields[field_name].status = FieldStatus.APPROVED
    
    def get_empty_fields(self) -> List[str]:
        """Get list of field names that are still EMPTY."""
        return [
            name for name, field_obj in self.fields.items()
            if field_obj.status == FieldStatus.EMPTY
        ]
    
    def get_approved_fields(self) -> Dict[str, ExtractedField]:
        """Get dictionary of approved fields."""
        return {
            name: field_obj for name, field_obj in self.fields.items()
            if field_obj.status == FieldStatus.APPROVED
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "case_id": self.case_id,
            "iteration": self.iteration,
            "fields": {
                name: field_obj.to_dict()
                for name, field_obj in self.fields.items()
            }
        }
    
    def generate_context_summary(self) -> str:
        """Generate context summary from approved fields for Phase 3."""
        approved = self.get_approved_fields()
        if not approved:
            return "No context available."
        
        context_parts = []
        for name, field_obj in approved.items():
            if field_obj.value:
                context_parts.append(f"{name}: {field_obj.value}")
        
        return "Context: " + ". ".join(context_parts) + "."
