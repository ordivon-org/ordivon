"""Phase DG-2: Document Registry tests.

Covers the checker's invariant validation: valid registry passes,
invalid data is caught for each invariant category.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[3] / "scripts" / "check_document_registry.py"


def _make_entry(**overrides) -> dict:
    """Create a valid baseline entry with optional field overrides."""
    base = {
        "doc_id": "test-doc-001",
        "path": "AGENTS.md",  # exists in repo
        "title": "Test Document",
        "doc_type": "governance_pack",
        "status": "accepted",
        "authority": "current_status",
        "phase": "DG-2",
        "owner": None,
        "freshness": "2026-04-30",
        "ai_read_priority": 2,
        "supersedes": None,
        "superseded_by": None,
        "related_docs": [],
        "related_ledgers": [],
        "related_receipts": [],
        "notes": "Test entry for unit tests.",
    }
    base.update(overrides)
    return base


def _run_checker(entries: list[dict]) -> tuple[int, str]:
    """Run the checker against a temp registry, return (exit_code, stdout)."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode, result.stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Positive cases ────────────────────────────────────────────────────

def test_valid_registry_passes():
    """A registry with all valid entries must pass."""
    entries = [
        _make_entry(doc_id="a", path="AGENTS.md", doc_type="root_context", status="current",
                    authority="source_of_truth", ai_read_priority=0),
        _make_entry(doc_id="b", path="docs/ai/README.md", doc_type="ai_onboarding", status="current",
                    authority="current_status", ai_read_priority=1),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code == 0, f"Expected pass but got: {out}"
    assert "All document registry invariants pass" in out


# ── Negative: JSON validity ───────────────────────────────────────────

def test_invalid_json_fails():
    """Non-JSON line must fail."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("this is not json\n")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Negative: required fields ─────────────────────────────────────────

def test_missing_required_field_fails():
    """Entry missing a required field must fail."""
    entries = [_make_entry(doc_id="x")]
    del entries[0]["authority"]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: duplicate doc_id ────────────────────────────────────────

def test_duplicate_doc_id_fails():
    """Duplicate doc_id must fail."""
    entries = [
        _make_entry(doc_id="dup"),
        _make_entry(doc_id="dup"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: missing path ────────────────────────────────────────────

def test_missing_registered_path_fails():
    """Path that doesn't exist on disk must fail."""
    entries = [_make_entry(doc_id="bad-path", path="nonexistent/file.md")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: invalid doc_type ────────────────────────────────────────

def test_invalid_doc_type_fails():
    """Unknown doc_type must fail."""
    entries = [_make_entry(doc_id="bad-type", doc_type="not_a_real_type")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: invalid status ──────────────────────────────────────────

def test_invalid_status_fails():
    """Unknown status must fail."""
    entries = [_make_entry(doc_id="bad-status", status="nonexistent_status")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: invalid authority ───────────────────────────────────────

def test_invalid_authority_fails():
    """Unknown authority must fail."""
    entries = [_make_entry(doc_id="bad-auth", authority="supreme_leader")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: stale source_of_truth ───────────────────────────────────

def test_stale_source_of_truth_fails():
    """source_of_truth doc with status=stale must fail."""
    entries = [_make_entry(doc_id="stale-sot", doc_type="phase_boundary",
                           status="stale", authority="source_of_truth")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: archived high-priority AI doc ───────────────────────────

def test_archived_high_priority_ai_doc_fails():
    """Archived doc with AI priority 0 or 1 must fail."""
    entries = [_make_entry(doc_id="arch-hi", status="archived", ai_read_priority=0)]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: ledger as source_of_truth ───────────────────────────────

def test_ledger_marked_source_of_truth_fails():
    """Ledger doc with authority=source_of_truth must fail."""
    entries = [_make_entry(doc_id="bad-ledger", doc_type="ledger",
                           authority="source_of_truth",
                           path="docs/runtime/paper-trades/paper-dogfood-ledger.jsonl")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: paper ledger as execution authority ─────────────────────

def test_paper_ledger_execution_authority_fails():
    """Paper dogfood ledger described as execution authority must fail."""
    entries = [_make_entry(
        doc_id="paper-dogfood-ledger", doc_type="ledger",
        authority="supporting_evidence",
        path="docs/runtime/paper-trades/paper-dogfood-ledger.jsonl",
        notes="This is execution authority for paper trades.",
    )]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: CandidateRule as Policy ─────────────────────────────────

def test_candidate_rule_as_policy_fails():
    """Doc with candidate in title/id and Policy in notes must fail."""
    entries = [_make_entry(
        doc_id="cr-001", title="CandidateRule about Policy",
        doc_type="runtime",
        authority="current_status",
        notes="This is a Policy rule.",
    )]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: Phase 8 not deferred ────────────────────────────────────

def test_phase_8_not_deferred_fails():
    """Phase 8 doc not in deferred status must fail."""
    entries = [_make_entry(
        doc_id="phase-8-tracker", title="Phase 8 Readiness Tracker",
        doc_type="tracker", status="current",
        authority="current_status",
    )]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: supersedes unknown doc_id ───────────────────────────────

def test_supersedes_unknown_doc_id_fails():
    """supersedes referencing unknown doc_id must fail."""
    entries = [
        _make_entry(doc_id="a", supersedes="nonexistent"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: superseded_by unknown doc_id ────────────────────────────

def test_superseded_by_unknown_doc_id_fails():
    """superseded_by referencing unknown doc_id must fail."""
    entries = [
        _make_entry(doc_id="a", superseded_by="nonexistent"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: root_context archived ───────────────────────────────────

def test_root_context_archived_fails():
    """root_context doc archived must fail."""
    entries = [_make_entry(doc_id="agents-md", doc_type="root_context",
                           status="archived", authority="archive",
                           ai_read_priority=4)]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: phase_boundary stale ────────────────────────────────────

def test_phase_boundary_stale_fails():
    """phase_boundary doc stale must fail."""
    entries = [_make_entry(doc_id="pb-stale", doc_type="phase_boundary",
                           status="stale", authority="source_of_truth")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: critical AI doc wrong priority ──────────────────────────

def test_critical_ai_doc_wrong_priority_fails():
    """agents-md with ai_read_priority 3 must fail."""
    entries = [_make_entry(doc_id="agents-md", doc_type="root_context",
                           status="current", authority="source_of_truth",
                           ai_read_priority=3)]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Negative: phase-boundaries not source_of_truth ────────────────────

def test_phase_boundaries_not_source_of_truth_fails():
    """phase-boundaries without source_of_truth authority must fail."""
    entries = [_make_entry(doc_id="phase-boundaries", doc_type="phase_boundary",
                           status="current", authority="current_status",
                           ai_read_priority=1)]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Summary count test ────────────────────────────────────────────────

def test_checker_summary_counts():
    """Verify summary contains correct counts for a known set of entries."""
    entries = [
        _make_entry(doc_id="a", path="AGENTS.md", doc_type="root_context", status="current",
                    authority="source_of_truth", ai_read_priority=0),
        _make_entry(doc_id="b", path="docs/ai/README.md", doc_type="ai_onboarding", status="current",
                    authority="current_status", ai_read_priority=1),
        _make_entry(doc_id="c", path="docs/governance/README.md", doc_type="governance_pack",
                    status="accepted", authority="current_status", ai_read_priority=2),
        _make_entry(doc_id="d", path="docs/runtime/paper-trades/paper-dogfood-ledger.jsonl",
                    doc_type="ledger", status="closed", authority="supporting_evidence",
                    ai_read_priority=3),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code == 0
    assert "Total registered docs:     4" in out
    assert "source_of_truth:           1" in out
    assert "current_status:            2" in out
    assert "supporting_evidence:       1" in out


# ── accepted status is valid ──────────────────────────────────────────

def test_accepted_status_is_valid():
    """Status 'accepted' must be treated as valid (alias for current)."""
    entries = [_make_entry(doc_id="acc", status="accepted")]
    exit_code, _ = _run_checker(entries)
    assert exit_code == 0
