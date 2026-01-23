"""
Example usage of LLM Engine for field extraction.

This demonstrates how to use the LLM engine to extract fields from
case-screen documents and additional supporting documents.
"""

import asyncio
import os
import json
from pathlib import Path
from app.services.llm_engine import LLMEngine, ExtractionState
from app.core.config import settings


async def example_extraction():
    """
    Example: Extract fields from case-screen PDF.
    
    Example PDF: "Cohan Law PLLC - Sarante - Claim leter.pdf"
    """
    
    # Initialize LLM Engine
    llm_engine = LLMEngine(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL
    )
    
    # Path to case-screen PDF
    case_screen_pdf = "Cohan Law PLLC - Sarante - Claim leter.pdf"
    
    # Check if file exists
    if not Path(case_screen_pdf).exists():
        print(f"Error: PDF file not found: {case_screen_pdf}")
        return
    
    print(f"Processing case-screen document: {case_screen_pdf}")
    print("=" * 80)
    
    # Process case-screen document (Primary iteration)
    state = await llm_engine.process_case_screen_document(case_screen_pdf)
    
    # Get summary
    summary = llm_engine.get_extraction_summary(state)
    
    print("\nExtraction Summary:")
    print(f"  Total fields: {summary['total_fields']}")
    print(f"  Extracted: {summary['extracted_fields']}")
    print(f"  Missing: {summary['missing_fields']}")
    print(f"  Extraction rate: {summary['extraction_rate']}")
    print(f"  Iterations: {summary['iterations']}")
    
    print("\nExtracted Fields:")
    for field_name, value in summary['extracted_values'].items():
        print(f"  {field_name}: {value[:100]}...")
    
    print("\nMissing Fields:")
    for field_name in summary['missing_field_names']:
        print(f"  - {field_name}")
    
    # If there are missing fields, process additional documents
    if summary['missing_fields'] > 0:
        print("\n" + "=" * 80)
        print("Processing additional documents to extract missing fields...")
        
        # Example: Process another document
        # additional_pdf = "path/to/additional/document.pdf"
        # if Path(additional_pdf).exists():
        #     state = await llm_engine.process_additional_document(
        #         pdf_path=additional_pdf,
        #         state=state
        #     )
        #     
        #     # Get updated summary
        #     summary = llm_engine.get_extraction_summary(state)
        #     print(f"\nAfter additional document: {summary['extracted_fields']}/{summary['total_fields']} fields extracted")
    
    # Final state
    print("\n" + "=" * 80)
    print("Final Extraction State:")
    print(f"  Extracted fields: {len(state.extracted_fields)}")
    print(f"  Missing fields: {len(state.missing_fields)}")
    print(f"  Processed documents: {', '.join(state.processed_documents)}")
    
    # Access extracted fields from state
    print("\nAll Extracted Fields (from state):")
    for field_name, extracted_field in state.extracted_fields.items():
        print(f"  {field_name}:")
        print(f"    Value: {extracted_field.value}")
        print(f"    Source: {extracted_field.source_document}")
        print(f"    Iteration: {extracted_field.iteration}")
        print(f"    Extracted at: {extracted_field.extracted_at}")


async def example_iterative_extraction():
    """
    Example: Iterative extraction with multiple documents.
    """
    
    llm_engine = LLMEngine(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL
    )
    
    # List of documents in priority order
    documents = [
        "Cohan Law PLLC - Sarante - Claim leter.pdf",  # Priority 1: Case-screen
        # "medical_records.pdf",  # Priority 2
        # "police_report.pdf",     # Priority 3
    ]
    
    # Start with case-screen
    case_screen = documents[0]
    if not Path(case_screen).exists():
        print(f"Error: Case-screen PDF not found: {case_screen}")
        return
    
    print("Starting iterative extraction...")
    state = await llm_engine.process_case_screen_document(case_screen)
    
    # Process additional documents
    for doc_path in documents[1:]:
        if Path(doc_path).exists():
            print(f"\nProcessing: {doc_path}")
            state = await llm_engine.process_additional_document(
                pdf_path=doc_path,
                state=state
            )
            
            # Check if all fields extracted
            if len(state.missing_fields) == 0:
                print("All fields extracted!")
                break
    
    # Final summary
    summary = llm_engine.get_extraction_summary(state)
    print("\n" + "=" * 80)
    print("Final Results:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    # Make sure OPENAI_API_KEY is set in environment
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it in .env file or environment")
        exit(1)
    
    # Run example
    asyncio.run(example_extraction())
