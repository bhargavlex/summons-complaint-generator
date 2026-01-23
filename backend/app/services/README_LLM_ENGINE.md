# LLM Engine Implementation

## Overview

The LLM Engine (`llm_engine.py`) implements dynamic field extraction from legal documents using OpenAI's function calling API. It supports iterative extraction with temporary field storage across multiple document processing iterations.

## Key Features

1. **Dynamic Tool Generation**: Creates JSON schema tools based on missing fields only
2. **Iterative Extraction**: Processes documents in priority order, updating missing fields after each iteration
3. **Temporary Field Storage**: Uses `ExtractionState` to track extracted fields across iterations
4. **Case-Screen Priority**: Processes case-screen documents first (primary iteration)
5. **Context Management**: Maintains context summary from previously processed documents

## Core Components

### 1. ExtractionState
Tracks extraction progress::
- `all_fields`: Set of all fields to extract
- `extracted_fields`: Dictionary of extracted field values
- `missing_fields`: Set of fields still needed
- `processed_documents`: Set of processed document names
- `processed_pages`: Dictionary tracking processed pages per document
- `context_summary`: Aggregated context from all processed documents

### 2. LLMEngine
Main engine class with methods:
- `process_case_screen_document()`: Primary iteration for case-screen PDF
- `process_additional_document()`: Subsequent iterations for supporting documents
- `generate_extraction_tool()`: Creates dynamic tool schema
- `extract_fields_from_document()`: Calls LLM API with document text

## Template Fields

The engine is configured with 20 template fields:
- Venue_Street_Address_
- Plaintiff_County_
- Defendant_City
- Defendant_Street_Address_
- Defendant_County
- Currtent_Month_Year
- Plaintiff_name_
- LOA
- hisher
- heshe
- Defendant_State
- Defendant_name
- Defendant_Zip_code
- Plaintiff_State_
- Case_County
- LOA__County
- Date_of_accident
- Venue_bases_on
- Venue_County_State
- LOA__State

Each field has:
- Type (string)
- Description (for LLM context)
- Required flag

## Usage Example

```python
from app.services.llm_engine import LLMEngine
from app.core.config import settings

# Initialize engine
llm_engine = LLMEngine(
    api_key=settings.OPENAI_API_KEY,
    model=settings.OPENAI_MODEL
)

# Process case-screen document (Primary iteration)
state = await llm_engine.process_case_screen_document(
    pdf_path="Cohan Law PLLC - Sarante - Claim leter.pdf"
)

# Get extraction summary
summary = llm_engine.get_extraction_summary(state)
print(f"Extracted: {summary['extracted_fields']}/{summary['total_fields']}")

# Process additional documents if needed
if summary['missing_fields'] > 0:
    state = await llm_engine.process_additional_document(
        pdf_path="additional_document.pdf",
        state=state
    )

# Access extracted fields
for field_name, extracted_field in state.extracted_fields.items():
    print(f"{field_name}: {extracted_field.value}")
    print(f"  Source: {extracted_field.source_document}")
    print(f"  Iteration: {extracted_field.iteration}")
```

## Workflow

1. **Primary Iteration (Case-Screen)**:
   - Extract all text from case-screen PDF
   - Generate tool with all required fields
   - Call LLM to extract fields
   - Store extracted fields in `ExtractionState`
   - Generate context summary

2. **Subsequent Iterations**:
   - Get list of missing fields
   - Generate tool with only missing fields
   - Process additional documents
   - Update state with new extractions
   - Update context summary

3. **Field Storage**:
   - Each extracted field stored as `ExtractedField` object
   - Contains: field_name, value, source_document, iteration, timestamp
   - Automatically removed from `missing_fields` when extracted

## Configuration

Set in `.env` file:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
```

## Dependencies

- `openai>=1.3.0`: OpenAI API client
- `pdfplumber>=0.10.3`: PDF text extraction

## Notes

- The engine limits document text to 8000 characters per LLM call to manage token usage
- Temperature set to 0.1 for consistent extraction
- Only non-empty field values are stored
- Pages are tracked to avoid reprocessing
