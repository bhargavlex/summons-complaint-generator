"""
Extraction tools for legal document field extraction.
Contains field definitions and tool generation functions.
"""

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Phase 1 fields – Case Screen UI only (generic, no real example values)
PHASE1_FIELDS = [
    "plaintiff_name",
    "plaintiff_state",
    "plaintiff_address",
    "defendant_names",
    "defendant_addresses",
    "incident_description",
    "incident_location_type",
    "incident_month_year",
]

# Phase 1 field definitions – separate list, Case Screen UI only (generic placeholders)
PHASE1_FIELD_DEFINITIONS = {
    "plaintiff_name": {
        "description": (
            "Extract the full legal name of the primary plaintiff. "
            "Look at the top header bar of the case screen (Matter Manager title). "
            "Also confirm inside All Parties → Plaintiffs tab → Name column. "
            "If both locations exist, prefer All Parties → Plaintiffs. "
            "Return as: FirstName LastName. Do not include commas, roles, or labels. "
            "Return a single string. Example format: Plaintiff Firstname Lastname"
        )
    },
    "plaintiff_state": {
        "description": (
            "Extract the U.S. state where the plaintiff resides. "
            "Navigate to All Parties → Plaintiffs → Address block. "
            "Parse only the state from the mailing address. "
            "Normalize to full state name (not abbreviation). "
            "Do not infer county. If missing, return null. Example format: StateName"
        )
    },
    "plaintiff_address": {
        "description": (
            "Extract the complete mailing address of the plaintiff. "
            "Source exclusively from All Parties → Plaintiffs → Address. "
            "Capture street, city, state, and ZIP exactly as displayed. "
            "Preserve commas and spacing. Return as a single string. Do not reformat. "
            "Example format: Street Address, City, State ZIP"
        )
    },
    "defendant_names": {
        "description": (
            "Extract all defendant entity names listed in the case. "
            "Navigate to All Parties → Defendants tab. "
            "Collect every listed defendant. Preserve legal suffixes (LLC, INC, etc.). "
            "Return as a JSON array of strings. Do not merge multiple defendants. "
            "Example format: [\"Defendant Entity One\", \"Defendant Entity Two\"]"
        )
    },
    "defendant_addresses": {
        "description": (
            "Extract mailing addresses for each defendant. "
            "For every defendant card under All Parties → Defendants, read the associated Address field. "
            "Return a JSON array of objects, each with name and address. "
            "Do not infer county. Preserve formatting exactly as shown. "
            "Example format: [{\"name\": \"Defendant Entity\", \"address\": \"Street Address, City, State ZIP\"}]"
        )
    },
    "incident_description": {
        "description": (
            "Extract the full free-text narrative describing the incident. "
            "Navigate to Overview → Matter Summary. "
            "Capture the entire paragraph explaining what happened. "
            "Preserve original wording. Do not summarize or paraphrase. Return raw text. "
            "Example format: Client reports an incident occurring at the subject location..."
        )
    },
    "incident_location_type": {
        "description": (
            "Extract the general location category of the incident. "
            "From Matter Summary, identify the noun phrase describing location. "
            "Examples include categories like parking area, sidewalk, interior premises. "
            "Return lowercase noun phrase only. Do not extract addresses. "
            "Example format: location type"
        )
    },
    "incident_month_year": {
        "description": (
            "Extract the month and year of incident. "
            "Navigate to Overview → Important Dates. Read the value labeled DOI. "
            "Return in format: Month YYYY. Do not guess day. If missing, return null. "
            "Example format: Month YYYY"
        )
    },
}

PHASE2_FIELDS = [
    "Plaintiff_name_",
    "Date_of_accident",
    "LOA",
    "LOA__County",
    "LOA__State",
    "Defendant_Street_Address_",
    "Defendant_City",
    "Defendant_State",
    "Defendant_Zip_code",
    "hisher",
    "heshe",
]

PHASE2_FIELD_DEFINITIONS = {

    "Plaintiff_name_": {
        "description": (
            "Extract claimant/plaintiff name from labeled fields such as 'Claimant:' "
            "or narrative references. Prefer structured RE blocks. "
            "Return full name only. Do not include titles. "
            "Overwrite Phase-1 only if Phase-1 is EMPTY."
        )
    },

    "Date_of_accident": {
        "description": (
            "Extract accident date from labels such as 'D/A:' or explicit narrative dates. "
            "Ignore time component. Format as 'Month Day, Year'. "
            "Prefer structured D/A fields over narrative. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "LOA": {
        "description": (
            "Extract full accident street address from labeled 'Place:' fields or narrative. "
            "Must include street + city + state + ZIP if present. "
            "Never reuse defendant mailing address unless explicitly marked as accident location. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "LOA__County": {
        "description": (
            "Extract county from accident location. Only populate if LOA exists. "
            "If county is explicitly stated in the document, use confidence 0.9+. "
            "If not stated but inferable from LOA (e.g. city + state: Bronx, NY → Bronx County), "
            "you MAY infer county and use confidence 0.75–0.85. Return full county name without 'County'. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "LOA__State": {
        "description": (
            "Extract state from accident location. Only populate if LOA exists. "
            "If state is explicitly stated, use confidence 0.9+. "
            "If LOA contains state abbreviation (e.g. NY, CA), you MAY normalize to full name (New York, California) "
            "and use confidence 0.75–0.85. Overwrite only if Phase-1 is EMPTY."
        )
    },

    "Defendant_Street_Address_": {
        "description": (
            "Extract defendant mailing/business street address from recipient blocks or entity records. "
            "Do NOT confuse with accident location. "
            "Do NOT reuse LOA. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "Defendant_City": {
        "description": (
            "Extract defendant mailing/business city from address block. "
            "Do NOT infer. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "Defendant_State": {
        "description": (
            "Extract defendant mailing/business state. Normalize to full name. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "Defendant_Zip_code": {
        "description": (
            "Extract defendant ZIP code from mailing/business address. "
            "Do NOT infer. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "hisher": {
        "description": (
            "Lowercase possessive pronoun derived from plaintiff gender: his or her. "
            "Infer gender only from plaintiff name or explicit document references. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },

    "heshe": {
        "description": (
            "Lowercase subject pronoun derived from plaintiff gender: he or she. "
            "Infer gender only from plaintiff name or explicit document references. "
            "Overwrite only if Phase-1 is EMPTY."
        )
    },
}




# Field definitions for legal document extraction
# Each field uses nested schema: {value, confidence, reasoning}
FIELD_DEFINITIONS = {

    "Case_County": {
        "description": (
            "Court filing county extracted ONLY from formal court caption containing 'COUNTY OF <X>'. "
            "If caption is not visible in this document, return empty with confidence 0.0. "
            "Do NOT infer from addresses, cities, or defendant locations."
        )
    },

    "Plaintiff_name_": {
        "description": (
            "Full plaintiff name exactly as shown in caption. "
            "Prefer uppercase if document uses uppercase."
        )
    },

    "Plaintiff_County_": {
        "description": (
            "Plaintiff residence county (full name). "
            "Never use 1.0 unless county explicitly stated. "
            "If missing but city/state present, infer county from city/state using confidence between 0.75–0.85. "
            "If cannot infer, return empty."
        )
    },

    "Plaintiff_State_": {
        "description": (
            "Plaintiff residence state FULL NAME (no abbreviations)."
        )
    },

    "Defendant_name": {
        "description": (
            "All defendant entities exactly as captioned. "
            "If multiple defendants, join using ' and '."
        )
    },

    "Defendant_Street_Address_": {
        "description": (
            "Extract ONLY from defendant mailing/business address block. "
            "These values must NOT be reused for Venue or LOA unless explicitly referenced there."
            "If no mailing/business address block exists, return empty with confidence 0.0."
        )
    },

    "Defendant_City": {
        "description": (
            "Extract ONLY from defendant mailing/business address block. "
            "These values must NOT be reused for Venue or LOA unless explicitly referenced there."
            "If no mailing/business address block exists, return empty with confidence 0.0."
        )
    },

    "Defendant_State": {
        "description": (
            "Extract ONLY from defendant mailing/business address block. "
            "These values must NOT be reused for Venue or LOA unless explicitly referenced there."
            "If no mailing/business address block exists, return empty with confidence 0.0."
        )
    },

    "Defendant_Zip_code": {
        "description": (
            "Extract ONLY from defendant mailing/business address block. "
            "These values must NOT be reused for Venue or LOA unless explicitly referenced there."
            "If no mailing/business address block exists, return empty with confidence 0.0."
        )
    },

    "Venue_bases_on": {
        "description": (
            "Legal basis for venue such as defendant place of business, "
            "location of accident, or plaintiff residence. "
            "Must come from venue paragraph."
        )
    },

    "Venue_Street_Address_": {
        "description": (
            "Street address explicitly stated in venue paragraph. "
            "Do NOT reuse defendant address unless venue paragraph confirms it."
        )
    },

    "Venue_County_State": {
        "description": (
            "Venue location formatted as '<City>, <County> County, <State>'. "
            "Must be explicitly stated or strongly implied by venue paragraph."
        )
    },

    "Currtent_Month_Year": {
        "description": (
            "Current month formatted exactly as '<Month>_____, <Year>'."
        )
    },

    "Date_of_accident": {
        "description": (
            "Accident date formatted '<Month> <Day>, <Year>'. "
            "Must come from accident narrative."
        )
    },

    "LOA": {
        "description": (
            "Extract ONLY if accident narrative explicitly provides full street-level address. "
            "If only general location is mentioned, return empty. "
            "Never reuse defendant or plaintiff addresses."
            "If no accident narrative exists, return empty with confidence 0.0."
        )
    },

    "LOA__County": {
        "description": (
            "Only populate if LOA exists OR accident narrative explicitly states county/state. "
            "Otherwise return empty. "
            "If no accident narrative exists, return empty with confidence 0.0."

        )
    },

    "LOA__State": {
        "description": (
            "Only populate if LOA exists OR accident narrative explicitly states county/state. "
            "Otherwise return empty. "
            "If no accident narrative exists, return empty with confidence 0.0."
        )
    },

    "hisher": {
        "description": (
            "Lowercase possessive pronoun based on plaintiff gender: his or her. "
            "Infer only if gender clearly implied by name or document."
        )
    },

    "heshe": {
        "description": (
            "Lowercase subject pronoun based on plaintiff gender: he or she. "
            "Infer only if gender clearly implied by name or document."
        )
    },
}




# Phase 1: Case Screen extraction – system prompt (attach once per phase-1 run)
PHASE1_SYSTEM_PROMPT = """
You are a legal intake extraction engine.

You will be provided with a Case Screen PDF containing screenshots of a legal matter management system (CloudLex / Matter Manager style UI).

This PDF represents case overview data only, not pleadings.

Your task is to extract structured fields exclusively from this Case Screen PDF.

---

## Scope Restrictions (Critical)

You must follow these rules strictly:

* Extract ONLY from visible Case Screen UI.
* NEVER infer missing data.
* NEVER use legal pleading knowledge.
* NEVER guess venue, county, or street unless explicitly shown.
* NEVER fabricate values.
* If a field is not present, return null.
* Do NOT rely on external assumptions.
* Do NOT complete partial addresses.
* Do NOT expand abbreviations unless they appear expanded.

If information is not directly visible, output null.

---

## Allowed UI Sources

You may ONLY read from these sections:

1. Top header bar (Matter Manager title)
2. Overview → Matter Summary
3. Overview → Important Dates
4. All Parties → Plaintiffs
5. All Parties → Defendants

Ignore everything else.

---

## Extraction Objective

Populate fields only if explicitly present in the Case Screen. Follow each field's description in the tool parameters.

---

## Forbidden Fields

Do NOT attempt to extract:

* Case County
* Venue
* Accident day
* Property street
* LOA full address
* Plaintiff county
* Jurisdiction

These do not belong to Phase-1.

Return null if encountered.

---

## Extraction Behavior

* Favor precision over completeness.
* Prefer nulls over guesses.
* Never extrapolate.
* Never merge unrelated UI fields.
* Always preserve original wording.

You are performing grounded visual extraction, not legal interpretation.
"""



PHASE2_SYSTEM_PROMPT = """You are a legal field extraction engine operating in Phase-2 (Gap Fill).

You will be provided with supporting documents such as Claim Letters, Matter Notes, and Entity Search PDFs.

Phase-2 exists only to populate fields that are currently EMPTY after Phase-1.

You must follow these rules strictly:

SCOPE
- Extract ONLY from the provided supporting document.
- Do NOT use Case Screen UI knowledge.
- Do NOT use Summons & Complaint knowledge.
- Do NOT rely on assumptions or external context.

OVERWRITE RULES
- Populate a field ONLY if it is currently EMPTY.
- Never overwrite an existing Phase-1 value.
- If a value already exists, leave it unchanged.

ALLOWED FIELDS (Phase-2 only)
- Plaintiff_name_
- Date_of_accident
- LOA
- LOA__County
- LOA__State
- Defendant_Street_Address_
- Defendant_City
- Defendant_State
- Defendant_Zip_code
- hisher
- heshe

Do not attempt to populate any other fields.

EXTRACTION PRIORITY
- Prefer structured labels such as:
  Claimant:
  D/A:
  Place:
- Prefer explicitly stated addresses over narrative mentions.
- Prefer accident location blocks over defendant mailing addresses for LOA.
- Prefer defendant recipient blocks or entity registry records for defendant addresses.

HARD CONSTRAINTS
- Never reuse defendant mailing address as accident location unless explicitly labeled as the accident site.
- Never infer venue or court county.
- Never guess missing values.
- Never fabricate ZIP codes, streets, or dates.
- If uncertainty exists, return empty value with confidence 0.0.

FORMATTING
- Date_of_accident must be formatted: Month Day, Year (ignore time).
- LOA must be full street-level address if present.
- Normalize states to full names.
- Return pronouns in lowercase.

CONFIDENCE
- Use 0.9+ only for clearly labeled values.
- Use 0.75–0.85 for inferred county/state derived directly from LOA.
- Use 0.0 if not explicitly supported.

BEHAVIOR
- Favor precision over completeness.
- Prefer nulls over guesses.
- Preserve original wording where applicable.

You are performing targeted legal gap filling, not document summarization.
"""


def get_phase1_system_prompt() -> str:
    """Return the system prompt used for phase-1 (Case Screen) extraction."""
    return PHASE1_SYSTEM_PROMPT.strip()


def get_phase2_system_prompt() -> str:
    """Return the system prompt used for phase-2 (gap fill) extraction."""
    return PHASE2_SYSTEM_PROMPT.strip()


def get_phase2_fields() -> List[str]:
    """Return the list of phase-2 field names (allowed for gap fill)."""
    return list(PHASE2_FIELDS)


def generate_phase2_extraction_tool(missing_fields: List[str]) -> Dict:
    """
    Generate extraction tool for phase-2 (gap fill) only.
    Uses PHASE2_FIELD_DEFINITIONS; only includes fields that are in PHASE2_FIELDS.
    Same nested schema (value, confidence, reasoning) as phase-1.
    """
    properties = {}
    required = []
    for field_name in missing_fields:
        if field_name in PHASE2_FIELD_DEFINITIONS:
            field_def = PHASE2_FIELD_DEFINITIONS[field_name]
            properties[field_name] = {
                "type": "object",
                "description": field_def["description"],
                "properties": {
                    "value": {
                        "type": "string",
                        "description": "The extracted value. Return empty string if not found.",
                    },
                    "confidence": {
                        "type": "number",
                        "description": (
                            "0.0 = not found. "
                            "0.5 = inferred from context. "
                            "0.75–0.85 = allowed inference. "
                            "0.9+ = explicitly stated."
                        ),
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Quote the text from the document or explain why you chose this value. If not found, state 'Not found in document'.",
                    },
                },
                "required": ["value", "confidence", "reasoning"],
            }
            required.append(field_name)
        else:
            properties[field_name] = {
                "type": "object",
                "description": f"Extract the value for {field_name}. If not found, return empty string for value and 0.0 for confidence.",
                "properties": {
                    "value": {"type": "string", "description": "The extracted value. Return empty string if not found."},
                    "confidence": {"type": "number", "description": "Confidence score from 0.0 to 1.0."},
                    "reasoning": {"type": "string", "description": "Explanation or quote from document."},
                },
                "required": ["value", "confidence", "reasoning"],
            }
            required.append(field_name)
    tool = {
        "type": "function",
        "function": {
            "name": "extract_fields",
            "description": (
                "Extract field values from the supporting document (Phase-2 gap fill only). "
                "Populate ONLY fields that are currently EMPTY. Never overwrite existing Phase-1 values. "
                "Follow each field's description. Return value, confidence (0.0–1.0), and reasoning."
            ),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
    logger.info("generate_phase2_extraction_tool: built tool for %d fields", len(missing_fields))
    return tool


def generate_phase1_extraction_tool(missing_fields: Optional[List[str]] = None) -> Dict:
    """
    Generate extraction tool for phase-1 (Case Screen UI only).
    Uses PHASE1_FIELD_DEFINITIONS; PHASE1_FIELDS if missing_fields is None.
    Same nested schema (value, confidence, reasoning) as generate_extraction_tool.
    """
    fields = missing_fields if missing_fields is not None else list(PHASE1_FIELDS)
    properties = {}
    required = []
    for field_name in fields:
        if field_name in PHASE1_FIELD_DEFINITIONS:
            field_def = PHASE1_FIELD_DEFINITIONS[field_name]
            properties[field_name] = {
                "type": "object",
                "description": field_def["description"],
                "properties": {
                    "value": {
                        "type": "string",
                        "description": "The extracted value. Return empty string if not found.",
                    },
                    "confidence": {
                        "type": "number",
                        "description": (
                            "0.0 = not found. "
                            "0.5 = inferred from context. "
                            "0.75–0.85 = allowed inference. "
                            "0.9+ = explicitly stated."
                        ),
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Quote the text from the document or explain why you chose this value. If not found, state 'Not found in document'.",
                    },
                },
                "required": ["value", "confidence", "reasoning"],
            }
            required.append(field_name)
        else:
            properties[field_name] = {
                "type": "object",
                "description": f"Extract the value for {field_name}. If not found, return empty string for value and 0.0 for confidence.",
                "properties": {
                    "value": {"type": "string", "description": "The extracted value. Return empty string if not found."},
                    "confidence": {"type": "number", "description": "Confidence score from 0.0 to 1.0."},
                    "reasoning": {"type": "string", "description": "Explanation or quote from document."},
                },
                "required": ["value", "confidence", "reasoning"],
            }
            required.append(field_name)
    tool = {
        "type": "function",
        "function": {
            "name": "extract_fields",
            "description": (
                "Extract field values from the Case Screen UI only. "
                "Follow each field's description and allowed sources. "
                "Return value, confidence (0.0–1.0), and reasoning. "
                "If a field is not present in the Case Screen, return empty value with confidence 0.0."
            ),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
    logger.info("generate_phase1_extraction_tool: built tool for %d fields", len(fields))
    return tool


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
                        "description": (
                            "0.0 = not found. "
                            "0.5 = inferred from context. "
                            "0.75–0.85 = allowed inference. "
                            "0.9+ = explicitly stated."
                        )
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
    logger.info("generate_extraction_tool: built tool for %d fields", len(missing_fields))
    return tool


def get_all_fields() -> List[str]:
    """
    Get list of all defined field names (FIELD_DEFINITIONS + phase-1 fields).
    
    Returns:
        List of all field names
    """
    phase1_only = [k for k in PHASE1_FIELDS if k not in FIELD_DEFINITIONS]
    all_names = list(FIELD_DEFINITIONS.keys()) + phase1_only
    logger.debug("get_all_fields: %d total fields", len(all_names))
    return all_names


def get_phase1_fields() -> List[str]:
    """
    Get list of phase 1 fields.
    
    Returns:
        List of phase 1 fields
    """
    logger.debug("get_phase1_fields: %d phase-1 fields", len(PHASE1_FIELDS))
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
        logger.debug("ExtractionState initialized: case_id=%s, iteration=%d, %d fields", self.case_id, self.iteration, len(self.fields))
    
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
            # Only update if field is EMPTY (Phase-2 must never overwrite Phase-1 or approved values)
            current = self.fields[field_name]
            if current.status == FieldStatus.EMPTY:
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
    
    def generate_context_summary(self, include_pending: bool = True) -> str:
        """Generate context summary for Phase-2/3. By default includes APPROVED and PENDING_REVIEW (phase-1) fields with values."""
        if include_pending:
            fields_with_values = [
                (name, f) for name, f in self.fields.items()
                if f.value and f.status in (FieldStatus.APPROVED, FieldStatus.PENDING_REVIEW)
            ]
        else:
            fields_with_values = [(name, f) for name, f in self.get_approved_fields().items() if f.value]
        if not fields_with_values:
            return "No context available."
        context_parts = [f"{name}: {f.value}" for name, f in fields_with_values]
        return "Context: " + ". ".join(context_parts) + "."
