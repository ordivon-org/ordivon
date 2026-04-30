"""Phase DG-4: Document Registry tests with freshness + semantic checks.

Covers the checker's invariant validation: valid registry passes,
freshness windows, semantic phrase checks, staleness detection.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[3] / "scripts" / "check_document_registry.py"


def _make_entry(**overrides) -> dict:
    """Create a valid baseline entry with optional field overrides."""
    base = {
        "doc_id": "test-doc-001",
        "path": "AGENTS.md",
        "title": "Test Document",
        "doc_type": "governance_pack",
        "status": "accepted",
        "authority": "current_status",
        "phase": "DG-4",
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


def _run_checker(entries: list[dict], env: dict = None) -> tuple[int, str]:
    """Run the checker against a temp registry, return (exit_code, stdout)."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = f.name
    try:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True,
            text=True,
            timeout=30,
            env=run_env,
        )
        return result.returncode, result.stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Positive: valid registry passes ───────────────────────────────────


def test_valid_registry_passes():
    """A registry with all valid entries must pass."""
    entries = [
        _make_entry(
            doc_id="a",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
            last_verified="2026-04-30",
            stale_after_days=7,
        ),
        _make_entry(
            doc_id="b",
            path="docs/ai/README.md",
            doc_type="ai_onboarding",
            status="current",
            authority="current_status",
            ai_read_priority=1,
            last_verified="2026-04-30",
            stale_after_days=14,
        ),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code == 0, f"Expected pass but got: {out}"
    assert "All document registry invariants pass" in out


# ── Negative: missing last_verified on critical AI doc ────────────────


def test_critical_ai_doc_missing_last_verified_fails():
    """Critical AI doc without last_verified must fail."""
    entries = [
        _make_entry(
            doc_id="agents-md",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
            last_verified="2026-04-30",
            stale_after_days=7,
        ),
        _make_entry(
            doc_id="ai-readme",
            path="docs/ai/README.md",
            doc_type="ai_onboarding",
            status="current",
            authority="current_status",
            ai_read_priority=1,
            last_verified="2026-04-30",
            stale_after_days=14,
        ),
        _make_entry(
            doc_id="phase-boundaries",
            path="docs/ai/current-phase-boundaries.md",
            doc_type="phase_boundary",
            status="current",
            authority="source_of_truth",
            ai_read_priority=1,
            # Missing last_verified!
            stale_after_days=7,
        ),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code != 0, f"Expected fail but passed: {out}"


# ── Freshness: stale when exceeded ────────────────────────────────────


def test_stale_last_verified_fails():
    """Doc with last_verified older than stale_after_days must fail."""
    entries = [
        _make_entry(
            doc_id="agents-md",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
            last_verified="2026-04-20",
            stale_after_days=7,
        ),
    ]
    # REFERENCE_DATE=2026-04-30: 10 days ago > 7 day max
    exit_code, _ = _run_checker(entries, env={"REFERENCE_DATE": "2026-04-30"})
    assert exit_code != 0


# ── Freshness: fresh passes ───────────────────────────────────────────


def test_fresh_last_verified_passes():
    """Doc within staleness window must pass."""
    entries = [
        _make_entry(
            doc_id="agents-md",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
            last_verified="2026-04-28",
            stale_after_days=7,
        ),
    ]
    # REFERENCE_DATE=2026-04-30: 2 days ago <= 7 day max
    exit_code, _ = _run_checker(entries, env={"REFERENCE_DATE": "2026-04-30"})
    assert exit_code == 0


# ── Semantic: Phase 8 ACTIVE phrase fails ─────────────────────────────


def test_phase_8_active_phrase_fails():
    """Current doc containing 'Phase 8 ACTIVE' must fail semantic check."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Doc\n\nPhase 8 is active and ready for live trading.\n")
        tmp = f.name
    try:
        entries = [
            _make_entry(
                doc_id="test",
                path=tmp,
                doc_type="runtime",
                status="current",
                authority="current_status",
                ai_read_priority=3,
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code != 0, f"Expected fail: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Semantic: live trading active phrase fails ────────────────────────


def test_live_trading_active_phrase_fails():
    """Current doc saying 'live trading is active' must fail."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nLive trading is now active.\n")
        tmp = f.name
    try:
        entries = [
            _make_entry(
                doc_id="test",
                path=tmp,
                doc_type="runtime",
                status="current",
                authority="current_status",
                ai_read_priority=3,
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code != 0, f"Expected fail: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Semantic: CandidateRule as Policy fails ───────────────────────────


def test_candidate_rule_as_policy_phrase_fails():
    """Doc saying 'CandidateRule is Policy' must fail."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nThis CandidateRule is Policy and active.\n")
        tmp = f.name
    try:
        entries = [
            _make_entry(
                doc_id="test",
                path=tmp,
                doc_type="runtime",
                status="current",
                authority="current_status",
                ai_read_priority=3,
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code != 0, f"Expected fail: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Semantic: ledger as execution authority fails ─────────────────────


def test_ledger_as_execution_authority_phrase_fails():
    """Doc saying 'ledger is execution authority' must fail."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nThe JSONL ledger authorizes execution.\n")
        tmp = f.name
    try:
        entries = [
            _make_entry(
                doc_id="test",
                path=tmp,
                doc_type="runtime",
                status="current",
                authority="current_status",
                ai_read_priority=3,
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code != 0, f"Expected fail: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Semantic: Phase 6 ACTIVE stale phrase fails ───────────────────────


def test_phase_6_active_phrase_fails():
    """Doc saying 'Phase 6 ACTIVE' must fail (should be COMPLETE)."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Doc\n\nPhase 6 is ACTIVE.\n")
        tmp = f.name
    try:
        entries = [
            _make_entry(
                doc_id="test",
                path=tmp,
                doc_type="runtime",
                status="current",
                authority="current_status",
                ai_read_priority=3,
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code != 0, f"Expected fail: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Semantic: safe NO-GO context passes ───────────────────────────────


def test_safe_nogo_context_passes():
    """Doc with 'Phase 8 remains DEFERRED' in safe context must pass."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nPhase 8 remains DEFERRED. No live trading is NO-GO.\n")
        f.write("CandidateRules are NOT Policy — advisory only.\n")
        f.write("JSONL ledger is evidence, not execution authority.\n")
        tmp = f.name
    try:
        entries = [
            _make_entry(
                doc_id="test",
                path=tmp,
                doc_type="runtime",
                status="current",
                authority="current_status",
                ai_read_priority=3,
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code == 0, f"Expected pass: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Deterministic date injection works ────────────────────────────────


def test_deterministic_date_injection_works():
    """REFERENCE_DATE env var controls staleness comparison."""
    entries = [
        _make_entry(
            doc_id="agents-md",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
            last_verified="2026-04-20",
            stale_after_days=7,
        ),
    ]
    # With reference date 2026-04-25 (5 days after) → should pass
    exit_code, _ = _run_checker(entries, env={"REFERENCE_DATE": "2026-04-25"})
    assert exit_code == 0
    # With reference date 2026-04-30 (10 days after) → should fail
    exit_code, _ = _run_checker(entries, env={"REFERENCE_DATE": "2026-04-30"})
    assert exit_code != 0


# ── Checker summary includes freshness count ──────────────────────────


def test_checker_summary_includes_freshness_counts():
    """Summary must show last_verified and stale_after_days counts."""
    entries = [
        _make_entry(
            doc_id="a",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
            last_verified="2026-04-30",
            stale_after_days=7,
        ),
        _make_entry(
            doc_id="b",
            path="docs/ai/README.md",
            doc_type="ai_onboarding",
            status="current",
            authority="current_status",
            ai_read_priority=1,
            last_verified="2026-04-30",
            stale_after_days=14,
        ),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code == 0
    assert "With last_verified:" in out
    assert "With stale_after_days:" in out
    assert "Semantic scan targets:" in out


# ── Original DG-2 tests retained below ────────────────────────────────


def test_invalid_json_fails():
    """Non-JSON line must fail."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("this is not json\n")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_missing_required_field_fails():
    """Entry missing a required field must fail."""
    entries = [_make_entry(doc_id="x")]
    del entries[0]["authority"]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_duplicate_doc_id_fails():
    """Duplicate doc_id must fail."""
    entries = [
        _make_entry(doc_id="dup"),
        _make_entry(doc_id="dup"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_missing_registered_path_fails():
    """Path that doesn't exist on disk must fail."""
    entries = [_make_entry(doc_id="bad-path", path="nonexistent/file.md")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_invalid_doc_type_fails():
    """Unknown doc_type must fail."""
    entries = [_make_entry(doc_id="bad-type", doc_type="not_a_real_type")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_invalid_status_fails():
    """Unknown status must fail."""
    entries = [_make_entry(doc_id="bad-status", status="nonexistent_status")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_invalid_authority_fails():
    """Unknown authority must fail."""
    entries = [_make_entry(doc_id="bad-auth", authority="supreme_leader")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_stale_source_of_truth_fails():
    """source_of_truth doc with status=stale must fail."""
    entries = [_make_entry(doc_id="stale-sot", doc_type="phase_boundary", status="stale", authority="source_of_truth")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_archived_high_priority_ai_doc_fails():
    """Archived doc with AI priority 0 or 1 must fail."""
    entries = [_make_entry(doc_id="arch-hi", status="archived", ai_read_priority=0)]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_ledger_marked_source_of_truth_fails():
    """Ledger doc with authority=source_of_truth must fail."""
    entries = [
        _make_entry(
            doc_id="bad-ledger",
            doc_type="ledger",
            authority="source_of_truth",
            path="docs/runtime/paper-trades/paper-dogfood-ledger.jsonl",
        )
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_paper_ledger_execution_authority_fails():
    """Paper dogfood ledger described as execution authority must fail."""
    entries = [
        _make_entry(
            doc_id="paper-dogfood-ledger",
            doc_type="ledger",
            authority="supporting_evidence",
            path="docs/runtime/paper-trades/paper-dogfood-ledger.jsonl",
            notes="This is execution authority for paper trades.",
        )
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_candidate_rule_as_policy_fails():
    """Doc with candidate in title/id and Policy in notes must fail."""
    entries = [
        _make_entry(
            doc_id="cr-001",
            title="CandidateRule about Policy",
            doc_type="runtime",
            authority="current_status",
            notes="This is a Policy rule.",
        )
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_phase_8_not_deferred_fails():
    """Phase 8 doc not in deferred status must fail."""
    entries = [
        _make_entry(
            doc_id="phase-8-tracker",
            title="Phase 8 Readiness Tracker",
            doc_type="tracker",
            status="current",
            authority="current_status",
        )
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_supersedes_unknown_doc_id_fails():
    """supersedes referencing unknown doc_id must fail."""
    entries = [
        _make_entry(doc_id="a", supersedes="nonexistent"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_superseded_by_unknown_doc_id_fails():
    """superseded_by referencing unknown doc_id must fail."""
    entries = [
        _make_entry(doc_id="a", superseded_by="nonexistent"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_root_context_archived_fails():
    """root_context doc archived must fail."""
    entries = [
        _make_entry(
            doc_id="agents-md", doc_type="root_context", status="archived", authority="archive", ai_read_priority=4
        )
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_phase_boundary_stale_fails():
    """phase_boundary doc stale must fail."""
    entries = [_make_entry(doc_id="pb-stale", doc_type="phase_boundary", status="stale", authority="source_of_truth")]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_critical_ai_doc_wrong_priority_fails():
    """agents-md with ai_read_priority 3 must fail."""
    entries = [
        _make_entry(
            doc_id="agents-md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=3,
            last_verified="2026-04-30",
            stale_after_days=7,
        )
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_phase_boundaries_not_source_of_truth_fails():
    """phase-boundaries without source_of_truth authority must fail."""
    entries = [
        _make_entry(
            doc_id="phase-boundaries",
            doc_type="phase_boundary",
            status="current",
            authority="current_status",
            ai_read_priority=1,
            last_verified="2026-04-30",
            stale_after_days=7,
        )
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_checker_summary_counts():
    """Verify summary contains correct counts for a known set of entries."""
    entries = [
        _make_entry(
            doc_id="a",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
        ),
        _make_entry(
            doc_id="b",
            path="docs/ai/README.md",
            doc_type="ai_onboarding",
            status="current",
            authority="current_status",
            ai_read_priority=1,
        ),
        _make_entry(
            doc_id="c",
            path="docs/governance/README.md",
            doc_type="governance_pack",
            status="accepted",
            authority="current_status",
            ai_read_priority=2,
        ),
        _make_entry(
            doc_id="d",
            path="docs/runtime/paper-trades/paper-dogfood-ledger.jsonl",
            doc_type="ledger",
            status="closed",
            authority="supporting_evidence",
            ai_read_priority=3,
        ),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code == 0
    assert "Total registered docs:     4" in out
    assert "source_of_truth:           1" in out
    assert "current_status:            2" in out
    assert "supporting_evidence:       1" in out


def test_accepted_status_is_valid():
    """Status 'accepted' must be treated as valid (alias for current)."""
    entries = [_make_entry(doc_id="acc", status="accepted")]
    exit_code, _ = _run_checker(entries)
    assert exit_code == 0
