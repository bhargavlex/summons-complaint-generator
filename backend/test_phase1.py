"""
Test script for Phase 1: Extraction
Run this from the backend directory: python test_phase1.py
"""

import asyncio
import json
from pathlib import Path
from app.services.llm_engine import LLMEngine
from dotenv import load_dotenv

load_dotenv()


async def test_phase1():
    """Test Phase 1 extraction."""
    # Initialize engine
    engine = LLMEngine()
    
    # Try to find the PDF file in common locations
    pdf_paths = [
        Path("app/services/Cohan Law PLLC - Sarante - case screen.pdf"),
        Path("Cohan Law PLLC - Sarante - case screen.pdf"),
        Path("D:/summons-complaint-generator/backend/app/services/Cohan Law PLLC - Sarante - case screen.pdf"),
    ]
    
    pdf_path = None
    for path in pdf_paths:
        if path.exists():
            pdf_path = str(path)
            break
    
    if not pdf_path:
        print("❌ Error: PDF file not found. Please update the path in test_phase1.py")
        return
    
    print(f"📄 Processing: {pdf_path}")
    print("=" * 80)
    
    # Run Phase 1: Extraction
    state = await engine.execute_initial_extraction(pdf_path, pages=[1, 2, 3, 4, 5, 6])
    
    # Print results
    print("\n✅ Phase 1 Complete!")
    print(f"   Case ID: {state.case_id}")
    print(f"   Iteration: {state.iteration}")
    
    # Count fields by status
    pending = [f for f in state.fields.values() if f.status.value == "PENDING_REVIEW"]
    empty = [f for f in state.fields.values() if f.status.value == "EMPTY"]
    approved = [f for f in state.fields.values() if f.status.value == "APPROVED"]
    
    print(f"\n📊 Field Status:")
    print(f"   PENDING_REVIEW: {len(pending)}")
    print(f"   EMPTY: {len(empty)}")
    print(f"   APPROVED: {len(approved)}")
    
    # Show sample extracted fields
    print("\n📋 Sample Extracted Fields (PENDING_REVIEW):")
    for i, (name, field) in enumerate(list(state.fields.items())[:5]):
        if field.status.value == "PENDING_REVIEW":
            print(f"   {name}:")
            print(f"      Value: {field.value[:50]}..." if len(field.value) > 50 else f"      Value: {field.value}")
            print(f"      Confidence: {field.confidence}")
            print(f"      Reasoning: {field.reasoning[:80]}..." if len(field.reasoning) > 80 else f"      Reasoning: {field.reasoning}")
    
    # Full JSON output
    print("\n" + "=" * 80)
    print("📄 Full JSON Output:")
    print(json.dumps(state.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(test_phase1())