"""
Test extraction pipeline: Phase-1 (Case Screen) then Phase-2 (Claim letter).

Runs one full pipeline: execute_extraction_pipeline with Case Screen + Claim letter PDF.
Run from backend: python test_extraction_phase1_phase2.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add backend to path when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

load_dotenv()

from app.services.extraction_tools import FieldStatus, get_phase1_fields
from app.services.llm_engine import LLMEngine


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for extraction and tools."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Reduce noise from third-party libs
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def find_pdf(name: str, search_dirs: list) -> str | None:
    """Return first existing path for a PDF with given name (stem or full)."""
    for d in search_dirs:
        base = Path(d)
        if base.is_file() and base.suffix.lower() == ".pdf":
            if name in base.name or base.stem == name:
                return str(base)
        if base.is_dir():
            for p in base.rglob("*.pdf"):
                if name in p.name or p.stem == name:
                    return str(p)
    return None


def _sample_state(state) -> None:
    """Print a short sample of state fields."""
    phase1_names = get_phase1_fields()
    for name in phase1_names[:4]:
        if name not in state.fields:
            continue
        f = state.fields[name]
        val = (f.value[:60] + "...") if len(f.value) > 60 else f.value
        print(f"  {name}: value={val!r} confidence={f.confidence} status={f.status.value}")


async def test_phase1_only(engine: LLMEngine, case_screen_path: str, pages: list[int] | None = None) -> None:
    """Run Phase-1 only and print state."""
    logging.info("=== Phase-1 only ===")
    state = await engine.execute_phase1(
        case_screen_pdf_path=case_screen_path,
        pages=pages,
    )
    assert state is not None
    assert state.case_id
    assert state.iteration == 1
    phase1_names = get_phase1_fields()
    for name in phase1_names:
        assert name in state.fields, f"Phase-1 field missing: {name}"
    pending = [f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW]
    empty = state.get_empty_fields()
    logging.info("Phase-1 result: pending_review=%d, empty=%d", len(pending), len(empty))
    print("\n--- Phase-1 state (sample) ---")
    _sample_state(state)
    print("---\n")
    return state


async def test_phase1_then_phase2(
    engine: LLMEngine,
    case_screen_path: str,
    supporting_doc_path: str | None,
    case_screen_pages: list[int] | None = None,
    supporting_pages: list[int] | None = None,
) -> None:
    """Run Phase-1 then Phase-2 (if supporting doc provided) and print state."""
    logging.info("=== Phase-1 then Phase-2 ===")
    state = await engine.execute_phase1(
        case_screen_pdf_path=case_screen_path,
        pages=case_screen_pages,
    )
    assert state is not None
    assert state.iteration == 1

    if supporting_doc_path:
        state = await engine.execute_phase2(
            supporting_doc_pdf_path=supporting_doc_path,
            state=state,
            pages=supporting_pages,
        )
        assert state.iteration == 2
        logging.info("Phase-2 completed; iteration=%d", state.iteration)
    else:
        logging.info("No supporting doc; skipping Phase-2")

    pending = [f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW]
    empty = state.get_empty_fields()
    logging.info("Final state: pending_review=%d, empty=%d", len(pending), len(empty))
    print("\n--- Final state summary ---")
    print(json.dumps(state.to_dict(), indent=2, default=str)[:2000] + "\n...")
    print("---\n")
    return state


async def test_pipeline_function(
    engine: LLMEngine,
    case_screen_path: str,
    supporting_doc_path: str | None,
    case_screen_pages: list[int] | None = None,
    supporting_pages: list[int] | None = None,
) -> None:
    """Run execute_extraction_pipeline (Phase-1 then Phase-2 in one call)."""
    logging.info("=== execute_extraction_pipeline ===")
    state = await engine.execute_extraction_pipeline(
        case_screen_pdf_path=case_screen_path,
        supporting_doc_pdf_path=supporting_doc_path,
        case_screen_pages=case_screen_pages,
        supporting_doc_pages=supporting_pages,
    )
    assert state is not None
    pending = [f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW]
    empty = state.get_empty_fields()
    logging.info("Pipeline result: pending_review=%d, empty=%d", len(pending), len(empty))
    return state


async def main() -> None:
    setup_logging(logging.INFO)

    engine = LLMEngine()

    backend = Path(__file__).resolve().parent
    case_screen_path = find_pdf(
        "case screen",
        [
            backend / "app" / "services",
            backend,
            Path("D:/summons-complaint-generator/backend/app/services"),
        ],
    )
    if not case_screen_path:
        case_screen_path = str(backend / "app/services/Cohan Law PLLC - Sarante - case screen.pdf")
    if not Path(case_screen_path).exists():
        print("Case Screen PDF not found. Put a Case Screen PDF in backend/app/services or set path in script.")
        return

    # Phase-2: Claim letter PDF (supporting doc for gap filling)
    claim_letter_path = str(backend / "app/services/Cohan Law PLLC - Sarante - Claim leter.pdf")
    supporting_path = (
        find_pdf("police report", [backend / "app" / "services", backend])
        or find_pdf("claim", [backend / "app" / "services", backend])
        or (claim_letter_path if Path(claim_letter_path).exists() else None)
    )

    print("Case Screen:", case_screen_path)
    print("Supporting doc (Phase-2):", supporting_path or "(none)")
    print()
    sys.stdout.flush()

    # Phase-1
    logging.info("=== Phase-1 ===")
    sys.stdout.flush()
    state = await engine.execute_phase1(
        case_screen_pdf_path=case_screen_path,
        pages=[1, 2, 3, 4, 5, 6],
    )
    sys.stdout.flush()
    assert state is not None
    assert state.case_id
    for name in get_phase1_fields():
        assert name in state.fields, f"Phase-1 field missing: {name}"

    print("\n" + "=" * 60)
    print("AFTER PHASE-1 — Full JSON output")
    print("=" * 60)
    print(json.dumps(state.to_dict(), indent=2, default=str))
    print("=" * 60 + "\n")
    sys.stdout.flush()

    # Phase-2 (if supporting doc provided)
    if supporting_path:
        logging.info("=== Phase-2 ===")
        sys.stdout.flush()
        state = await engine.execute_phase2(
            supporting_doc_pdf_path=supporting_path,
            state=state,
            pages=None,
        )
        sys.stdout.flush()

        print("\n" + "=" * 60)
        print("AFTER PHASE-2 — Full JSON output")
        print("=" * 60)
        print(json.dumps(state.to_dict(), indent=2, default=str))
        print("=" * 60 + "\n")
        sys.stdout.flush()
    else:
        logging.info("No supporting doc; skipping Phase-2")

    pending = [f for f in state.fields.values() if f.status == FieldStatus.PENDING_REVIEW]
    empty = state.get_empty_fields()
    logging.info("Final: pending_review=%d, empty=%d", len(pending), len(empty))
    print("Full pipeline (Phase-1 + Phase-2) completed.")
    sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
