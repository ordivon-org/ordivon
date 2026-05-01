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


# ── Structural layers / governance planes tests (DG-6A-S) ─────────────


def test_valid_ontology_registry_entry_passes():
    """Ontology doc with valid structural_layers and governance_planes must pass."""
    entries = [
        _make_entry(
            doc_id="ordivon-core-pack-adapter-ontology",
            path="docs/architecture/ordivon-core-pack-adapter-ontology.md",
            doc_type="architecture",
            status="accepted",
            authority="source_of_truth",
            ai_read_priority=1,
            structural_layers=["core", "pack", "adapter", "governance_plane"],
            governance_planes=[
                "evidence_state",
                "authority_policy",
                "verification_safety",
                "orchestration_lifecycle",
                "knowledge_documentation",
                "risk_side_effect",
                "actor_trust",
                "surface_representation",
            ],
        ),
    ]
    exit_code, out = _run_checker(entries)
    assert exit_code == 0, f"Expected pass: {out}"


def test_invalid_structural_layer_fails():
    """Unknown structural_layer value must fail."""
    entries = [
        _make_entry(doc_id="bad", structural_layers=["not_a_real_layer"]),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_structural_layers_not_list_fails():
    """structural_layers as non-list must fail."""
    entries = [
        _make_entry(doc_id="bad", structural_layers="not_a_list"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_invalid_governance_plane_fails():
    """Unknown governance_plane value must fail."""
    entries = [
        _make_entry(doc_id="bad", governance_planes=["not_a_real_plane"]),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_governance_planes_not_list_fails():
    """governance_planes as non-list must fail."""
    entries = [
        _make_entry(doc_id="bad", governance_planes="not_a_list"),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_ontology_missing_structural_layers_fails():
    """Ontology architecture source_of_truth doc missing structural_layers must fail."""
    entries = [
        _make_entry(
            doc_id="ordivon-core-pack-adapter-ontology",
            path="docs/architecture/ordivon-core-pack-adapter-ontology.md",
            doc_type="architecture",
            status="accepted",
            authority="source_of_truth",
            ai_read_priority=1,
            governance_planes=["evidence_state"],
            # missing structural_layers
        ),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


def test_ontology_missing_governance_planes_fails():
    """Ontology architecture source_of_truth doc missing governance_planes must fail."""
    entries = [
        _make_entry(
            doc_id="ordivon-core-pack-adapter-ontology",
            path="docs/architecture/ordivon-core-pack-adapter-ontology.md",
            doc_type="architecture",
            status="accepted",
            authority="source_of_truth",
            ai_read_priority=1,
            structural_layers=["core", "pack", "adapter"],
            # missing governance_planes
        ),
    ]
    exit_code, _ = _run_checker(entries)
    assert exit_code != 0


# ── Legacy tests continue ─────────────────────────────────────────────


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


# ═══════════════════════════════════════════════════════════════════════
# PV-N2H: Coverage completeness + identity surface tests
# ═══════════════════════════════════════════════════════════════════════


def test_completeness_unregistered_doc_fails(tmp_path):
    """A .md file under docs/ not registered or excluded must fail."""
    from scripts.check_document_registry import check_completeness

    # Create a temp doc structure
    (tmp_path / "docs" / "product").mkdir(parents=True)
    (tmp_path / "docs" / "product" / "unregistered.md").write_text("# Unregistered\n")

    entries = []  # nothing registered
    exclusions = {"entries": []}

    # Override DISCOVERABLE_DIRS to use tmp_path
    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_completeness(entries, exclusions)
    finally:
        cdr.ROOT = orig_root

    assert len(errors) >= 1
    assert any("unregistered" in e for e in errors)


def test_completeness_registered_doc_passes(tmp_path):
    """Registered docs must not trigger completeness errors."""
    from scripts.check_document_registry import check_completeness

    (tmp_path / "docs" / "product").mkdir(parents=True)
    (tmp_path / "docs" / "product" / "ok.md").write_text("# OK\n")

    entries = [{"path": "docs/product/ok.md"}]
    exclusions = {"entries": []}

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_completeness(entries, exclusions)
    finally:
        cdr.ROOT = orig_root

    assert len(errors) == 0


def test_completeness_archive_passes(tmp_path):
    """Docs under docs/archive/ must not trigger completeness errors."""
    from scripts.check_document_registry import check_completeness

    (tmp_path / "docs" / "archive").mkdir(parents=True)
    (tmp_path / "docs" / "archive" / "old.md").write_text("# Old\n")

    entries = []
    exclusions = {"entries": []}

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_completeness(entries, exclusions)
    finally:
        cdr.ROOT = orig_root

    assert len(errors) == 0


def test_exclusion_with_reason_passes(tmp_path):
    """Excluded doc with valid reason must pass."""
    from scripts.check_document_registry import check_completeness

    (tmp_path / "docs" / "product").mkdir(parents=True)
    (tmp_path / "docs" / "product" / "ex.md").write_text("# Excluded\n")

    entries = []
    exclusions = {
        "entries": [
            {
                "path": "docs/product/ex.md",
                "reason": "Test exclusion",
                "classification": "intentionally_unregistered",
                "owner": "test",
                "reviewed_at": "2026-05-01",
            }
        ]
    }

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_completeness(entries, exclusions)
    finally:
        cdr.ROOT = orig_root

    assert len(errors) == 0


def test_exclusion_without_reason_fails(tmp_path):
    """Exclusion without reason must fail."""
    from scripts.check_document_registry import check_completeness

    (tmp_path / "docs" / "product").mkdir(parents=True)
    (tmp_path / "docs" / "product" / "no_reason.md").write_text("# No Reason\n")

    entries = []
    exclusions = {
        "entries": [
            {
                "path": "docs/product/no_reason.md",
                "classification": "intentionally_unregistered",
                "owner": "test",
                "reviewed_at": "2026-05-01",
                # missing reason
            }
        ]
    }

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_completeness(entries, exclusions)
    finally:
        cdr.ROOT = orig_root

    assert len(errors) >= 1
    assert any("reason" in e.lower() for e in errors)


def test_completeness_summary_includes_counts(capsys):
    """Checker output must include completeness and identity counts."""
    import scripts.check_document_registry as cdr

    entries = [
        _make_entry(
            doc_id="t",
            path="AGENTS.md",
            doc_type="root_context",
            status="current",
            authority="source_of_truth",
            ai_read_priority=0,
            last_verified="2026-05-01",
        )
    ]
    errors = cdr.check_invariants(entries)
    assert len(errors) == 0


# ── Identity surface tests ────────────────────────────────────────────


def test_identity_unsafe_pyproject_fails(tmp_path):
    """pyproject.toml with name='pfios' must fail."""
    from scripts.check_document_registry import check_identity_surfaces

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "pfios"\n')
    (tmp_path / "package.json").write_text('{"name": "ordivon"}\n')
    (tmp_path / "README.md").write_text("# Ordivon\n")
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "tests" / "conftest.py").write_text("# ok\n")

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_identity_surfaces()
    finally:
        cdr.ROOT = orig_root

    assert len(errors) >= 1
    assert any("pfios" in e for e in errors)


def test_identity_clean_pyproject_passes(tmp_path):
    """pyproject.toml with name='ordivon' must pass."""
    from scripts.check_document_registry import check_identity_surfaces

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ordivon"\n')
    (tmp_path / "package.json").write_text('{"name": "ordivon"}\n')
    (tmp_path / "README.md").write_text("# Ordivon\n")
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "tests" / "conftest.py").write_text("# clean\n")

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_identity_surfaces()
    finally:
        cdr.ROOT = orig_root

    assert len(errors) == 0


def test_identity_readme_aegisos_fails(tmp_path):
    """README opening with AegisOS must fail."""
    from scripts.check_document_registry import check_identity_surfaces

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ordivon"\n')
    (tmp_path / "package.json").write_text('{"name": "ordivon"}\n')
    (tmp_path / "README.md").write_text("# Financial AI OS\nAegisOS / CAIOS\n")
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "tests" / "conftest.py").write_text("# clean\n")

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_identity_surfaces()
    finally:
        cdr.ROOT = orig_root

    assert len(errors) >= 1
    assert any("AegisOS" in e for e in errors)


def test_identity_readme_ordivon_passes(tmp_path):
    """README opening with Ordivon must pass."""
    from scripts.check_document_registry import check_identity_surfaces

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ordivon"\n')
    (tmp_path / "package.json").write_text('{"name": "ordivon"}\n')
    (tmp_path / "README.md").write_text("# Ordivon\n\nOrdivon is a governance OS.\n")
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "tests" / "conftest.py").write_text("# clean\n")

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_identity_surfaces()
    finally:
        cdr.ROOT = orig_root

    assert len(errors) == 0
    assert "pfios" not in str(errors)


def test_identity_conftest_scoped_passes(tmp_path):
    """conftest.py with scoped PFIOS_DB_URL must pass."""
    from scripts.check_document_registry import check_identity_surfaces

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ordivon"\n')
    (tmp_path / "package.json").write_text('{"name": "ordivon"}\n')
    (tmp_path / "README.md").write_text("# Ordivon\n")
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "tests" / "conftest.py").write_text(
        'import os\nif "tests/contracts" in str(config.invocation_params):\n'
        '    os.environ["PFIOS_DB_URL"] = "duckdb:///:memory:"\n'
    )

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        errors = check_identity_surfaces()
    finally:
        cdr.ROOT = orig_root

    # Should pass because PFIOS_DB_URL is scoped to legacy paths
    assert not any("PFIOS_DB_URL" in e and "without scoping" in e for e in errors)


def test_checker_never_mutates_files(tmp_path):
    """Running identity check must not modify any files."""
    from scripts.check_document_registry import check_identity_surfaces

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ordivon"\n')
    (tmp_path / "package.json").write_text('{"name": "ordivon"}\n')
    (tmp_path / "README.md").write_text("# Ordivon\n")
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "tests" / "conftest.py").write_text("# clean\n")

    mtimes = {
        "pyproject.toml": (tmp_path / "pyproject.toml").stat().st_mtime,
        "package.json": (tmp_path / "package.json").stat().st_mtime,
        "README.md": (tmp_path / "README.md").stat().st_mtime,
    }

    import scripts.check_document_registry as cdr

    orig_root = cdr.ROOT
    cdr.ROOT = tmp_path
    try:
        check_identity_surfaces()
    finally:
        cdr.ROOT = orig_root

    for fname, orig in mtimes.items():
        assert (tmp_path / fname).stat().st_mtime == orig, f"{fname} was modified"


# ── Inline-date consistency checks ────────────────────────────────────


def test_inline_date_stale_fails():
    """Doc with inline Date older than last_verified must fail."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Doc\n\nDate: 2026-04-20\n\nSome content.\n")
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
                last_verified="2026-05-01",
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code != 0, f"Expected fail for stale inline date: {out}"
        assert "inline date" in out.lower()
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_inline_date_fresh_passes():
    """Doc with inline Date matching last_verified must pass."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Doc\n\nDate: 2026-05-01\n\nSome content.\n")
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
                last_verified="2026-05-01",
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code == 0, f"Expected pass: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_inline_date_future_passes():
    """Doc with inline Date newer than last_verified must pass (body was updated)."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Doc\n\nDate: 2026-05-05\n\nSome content.\n")
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
                last_verified="2026-05-01",
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code == 0, f"Expected pass: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_inline_date_no_last_verified_passes():
    """Doc with inline date but no last_verified must pass (no cross-check)."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Doc\n\nDate: 2026-04-01\n\nSome content.\n")
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


def test_inline_date_no_inline_date_passes():
    """Doc with last_verified but no inline date must pass (no false positives)."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Doc\n\nNo date field here.\n")
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
                last_verified="2026-05-01",
            ),
        ]
        exit_code, out = _run_checker(entries)
        assert exit_code == 0, f"Expected pass: {out}"
    finally:
        Path(tmp).unlink(missing_ok=True)
