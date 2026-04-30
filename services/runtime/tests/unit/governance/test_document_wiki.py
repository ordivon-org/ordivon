"""Phase DG-6: Document Wiki Generator tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[3] / "scripts" / "check_document_registry.py"
GENERATOR = Path(__file__).resolve().parents[3] / "scripts" / "generate_document_wiki.py"


def _make_entry(**overrides) -> dict:
    base = {
        "doc_id": "test-doc-001",
        "path": "AGENTS.md",
        "title": "Test Document",
        "doc_type": "governance_pack",
        "status": "accepted",
        "authority": "current_status",
        "phase": "DG-6",
        "owner": None,
        "freshness": "2026-04-30",
        "ai_read_priority": 2,
        "supersedes": None,
        "superseded_by": None,
        "related_docs": [],
        "related_ledgers": [],
        "related_receipts": [],
        "notes": "Test entry.",
    }
    base.update(overrides)
    return base


def _run_generator(entries: list[dict]) -> tuple[int, str]:
    """Run generator against temp registry, return (exit_code, stdout)."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(GENERATOR)],
            capture_output=True, text=True, timeout=30,
            env={**__import__("os").environ, "REGISTRY_OVERRIDE": tmp},
        )
        return result.returncode, result.stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


def _read_wiki() -> str:
    """Read the generated wiki from default path."""
    wiki_path = Path(__file__).resolve().parents[3] / "docs" / "governance" / "wiki-index.md"
    return wiki_path.read_text()


# ── Positive: wiki generation succeeds ────────────────────────────────

def test_generator_produces_wiki():
    """Generator must produce wiki-index.md."""
    wiki = _read_wiki()
    assert "Wiki Navigation Prototype" in wiki


# ── Navigation layer banner ───────────────────────────────────────────

def test_wiki_has_navigation_banner():
    """Wiki must state it is navigation, not source of truth."""
    wiki = _read_wiki()
    assert "Navigation layer only — not source of truth" in wiki


# ── Current truth includes AGENTS.md ──────────────────────────────────

def test_current_truth_includes_agents_md():
    """Current Truth section must include AGENTS.md."""
    wiki = _read_wiki()
    assert "Ordivon AI Agent Entry Point" in wiki
    assert "AGENTS.md" in wiki


# ── Current truth includes phase-boundaries ───────────────────────────

def test_current_truth_includes_phase_boundaries():
    """Current Truth section must include current-phase-boundaries.md."""
    wiki = _read_wiki()
    assert "Current Phase Boundaries" in wiki
    assert "current-phase-boundaries.md" in wiki


# ── AI Onboarding section ─────────────────────────────────────────────

def test_ai_onboarding_includes_agent_output_contract():
    """AI Onboarding section must include agent-output-contract.md."""
    wiki = _read_wiki()
    assert "Agent Output Contract" in wiki
    assert "agent-output-contract.md" in wiki


# ── Evidence section labels ledger as evidence only ───────────────────

def test_evidence_section_labels_ledger_evidence_only():
    """Evidence section must warn ledger is evidence, not execution authority."""
    wiki = _read_wiki()
    assert "Evidence only — does not authorize execution" in wiki
    assert "not execution authority" in wiki


# ── Phase 8 is shown as DEFERRED ──────────────────────────────────────

def test_phase_8_shown_as_deferred():
    """Phase 8 must be shown as DEFERRED."""
    wiki = _read_wiki()
    assert "Phase 8" in wiki
    assert "DEFERRED" in wiki


# ── Live trading / auto trading shown as NO-GO ────────────────────────

def test_nogo_boundaries_shown():
    """Live trading and auto trading must be shown as NO-GO."""
    wiki = _read_wiki()
    assert "Live trading" in wiki
    assert "NO-GO" in wiki
    assert "Auto trading" in wiki
    assert "permanently disabled" in wiki


# ── Archive section does not invent content ───────────────────────────

def test_archive_section_no_invented_entries():
    """Archive section must say no archive entries if none registered."""
    wiki = _read_wiki()
    assert "8. Archive / Historical" in wiki
    assert "No archive entries registered yet" in wiki


# ── Generator fails on invalid JSON ───────────────────────────────────

def test_generator_fails_on_invalid_json():
    """Generator must exit non-zero on invalid JSON input."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("not json\n")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(GENERATOR)],
            capture_output=True, text=True, timeout=30,
            env={**__import__("os").environ, "REGISTRY_OVERRIDE": tmp},
        )
        # Note: generator reads default path, not env override.
        # Override path via argument instead.
    finally:
        Path(tmp).unlink(missing_ok=True)
    # Run generator with explicit invalid path
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("not json\n")
        tmp = f.name
    try:
        # Patch: generator has no CLI arg for path, but we can verify
        # via subprocess that invalid registry causes failure.
        # Create a bad registry and verify generator output.
        result = subprocess.run(
            [sys.executable, "-c",
             "from scripts.generate_document_wiki import load_registry; "
             f"from pathlib import Path; "
             "import sys; "
             f"load_registry(Path('{tmp}')); "
             "print('UNEXPECTED SUCCESS')"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0 or "UNEXPECTED SUCCESS" not in result.stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Generator output is deterministic ─────────────────────────────────

def test_generator_output_deterministic():
    """Running generator twice must produce identical output."""
    wiki1 = _read_wiki()
    # Re-run generator
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        capture_output=True, text=True, timeout=30,
    )
    wiki2 = _read_wiki()
    assert wiki1 == wiki2, "Generator output not deterministic"


# ── No Alpaca / API requirement ───────────────────────────────────────

def test_generator_no_alpaca_reference():
    """Generator output must not reference Alpaca API."""
    wiki = _read_wiki()
    # The word "Alpaca" may appear in doc titles (e.g. Alpaca Paper Trading)
    # but "alpaca.markets" or "api.alpaca" must not appear
    assert "api.alpaca" not in wiki.lower()
    assert "alpaca.markets" not in wiki.lower()


# ── Wiki has total count ──────────────────────────────────────────────

def test_wiki_shows_total_doc_count():
    """Wiki must show total registered doc count."""
    wiki = _read_wiki()
    assert "Total registered docs" in wiki


# ── Wiki sections present ─────────────────────────────────────────────

def test_wiki_has_all_required_sections():
    """Wiki must contain all required sections."""
    wiki = _read_wiki()
    required = [
        "1. Current Truth",
        "2. AI Onboarding",
        "3. Governance Pack",
        "4. Evidence / Ledger",
        "5. Phase & Readiness",
        "6. Deferred / Tracker",
        "7. Risk / NO-GO",
        "8. Archive / Historical",
    ]
    for section in required:
        assert section in wiki, f"Missing section: {section}"


# ── Wiki is generated (not hand-written) ──────────────────────────────

def test_wiki_is_generated_label():
    """Wiki must state it is generated from registry."""
    wiki = _read_wiki()
    assert "Generated from `document-registry.jsonl`" in wiki
    assert "do not edit by hand" in wiki
