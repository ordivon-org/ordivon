"""Tests for Trace / Harness Evidence Import Scanner Alpha."""

from __future__ import annotations

from pathlib import Path

from ordivon_verify.scanners.trace_evidence import discover_trace_surfaces

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "trace_evidence"


def _findings_for(code: str, findings):
    return [f for f in findings if f.code == code]


def test_clean_trace_no_blocked():
    findings, _ = discover_trace_surfaces(FIXTURES / "clean_trace", fixture_mode=True)
    blocked = [f for f in findings if f.status == "BLOCKED"]
    assert len(blocked) == 0, f"Unexpected BLOCKED: {blocked}"


def test_missing_failed_tool_call_blocked():
    findings, _ = discover_trace_surfaces(FIXTURES / "missing_failed_tool_call", fixture_mode=True)
    hits = _findings_for("TRACE-FAILED-TOOL-CALL-MISSING", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_checkpoint_as_approval_blocked():
    findings, _ = discover_trace_surfaces(FIXTURES / "checkpoint_as_approval", fixture_mode=True)
    hits = _findings_for("CHECKPOINT-AS-APPROVAL", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_review_after_boundary_blocked_or_degraded():
    findings, _ = discover_trace_surfaces(FIXTURES / "review_after_boundary", fixture_mode=True)
    hits = _findings_for("REVIEW-AFTER-DECISION-BOUNDARY", findings)
    assert len(hits) >= 1
    assert hits[0].status in ("BLOCKED", "DEGRADED")


def test_trace_as_truth_blocked():
    findings, _ = discover_trace_surfaces(FIXTURES / "trace_as_truth", fixture_mode=True)
    hits = _findings_for("TRACE-AS-TRUTH", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_tool_success_as_safe_action_blocked():
    findings, _ = discover_trace_surfaces(FIXTURES / "tool_success_as_safe_action", fixture_mode=True)
    hits = _findings_for("TOOL-SUCCESS-AS-SAFE-ACTION", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_incomplete_trace_degraded():
    findings, _ = discover_trace_surfaces(FIXTURES / "incomplete_trace", fixture_mode=True)
    hits = _findings_for("TRACE-COMPLETENESS-MISSING", findings)
    assert len(hits) >= 1
    assert hits[0].status == "DEGRADED"


def test_trace_records_not_current_truth_by_default():
    _, records = discover_trace_surfaces(FIXTURES / "clean_trace", fixture_mode=True)
    for r in records:
        assert r.current_truth_allowed is False


def test_trace_surfaces_produce_artifact_records():
    _, records = discover_trace_surfaces(FIXTURES / "clean_trace", fixture_mode=True)
    assert len(records) >= 1
    types = {r.artifact_type for r in records}
    assert "runtime_trace" in types


def test_trace_records_have_authority_tier():
    _, records = discover_trace_surfaces(FIXTURES / "clean_trace", fixture_mode=True)
    for r in records:
        assert r.authority_tier is not None


def test_fixture_mode_scans_unsafe():
    findings, _ = discover_trace_surfaces(FIXTURES / "trace_as_truth", fixture_mode=True)
    assert len(findings) > 0


def test_production_mode_excludes_fixtures():
    findings, _ = discover_trace_surfaces(FIXTURES, fixture_mode=False)
    assert len(findings) == 0


def test_review_record_missing_source_handled():
    """Review record without source fields should produce findings."""
    findings, _ = discover_trace_surfaces(FIXTURES / "review_after_boundary", fixture_mode=True)
    # At minimum, the review-after-boundary finding should exist
    assert len(findings) > 0
