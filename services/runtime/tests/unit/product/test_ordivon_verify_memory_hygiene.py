"""Tests for Memory / Content Hygiene Scanner Alpha."""

from __future__ import annotations

from pathlib import Path

from ordivon_verify.scanners.memory_hygiene import discover_memory_surfaces

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "memory_hygiene"


def _findings_for(code: str, findings):
    return [f for f in findings if f.code == code]


def test_clean_memory_no_blocked():
    """Clean memory with proper source/freshness should have no BLOCKED."""
    findings, records = discover_memory_surfaces(FIXTURES / "clean_memory", fixture_mode=True)
    blocked = [f for f in findings if f.status == "BLOCKED"]
    assert len(blocked) == 0, f"Unexpected BLOCKED: {blocked}"


def test_missing_source_degraded_or_blocked():
    """Memory without source -> DEGRADED or BLOCKED."""
    findings, records = discover_memory_surfaces(FIXTURES / "missing_source", fixture_mode=True)
    hits = _findings_for("MEMORY-SOURCE-MISSING", findings)
    assert len(hits) >= 1
    assert hits[0].status in ("DEGRADED", "BLOCKED")


def test_missing_freshness_degraded():
    """Memory without freshness -> DEGRADED."""
    findings, records = discover_memory_surfaces(FIXTURES / "missing_freshness", fixture_mode=True)
    hits = _findings_for("MEMORY-FRESHNESS-MISSING", findings)
    assert len(hits) >= 1
    assert hits[0].status == "DEGRADED"


def test_stale_as_current_blocked():
    """Stale memory marked current_truth_allowed -> BLOCKED."""
    findings, records = discover_memory_surfaces(FIXTURES / "stale_as_current", fixture_mode=True)
    hits = _findings_for("MEMORY-STALE-AS-CURRENT", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_cross_project_memory_blocked():
    """Cross-project memory marked current -> BLOCKED."""
    findings, records = discover_memory_surfaces(FIXTURES / "cross_project_memory", fixture_mode=True)
    hits = _findings_for("MEMORY-CROSS-PROJECT-SCOPE", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_candidate_rule_as_policy_blocked():
    """CandidateRule presented as policy -> BLOCKED."""
    findings, records = discover_memory_surfaces(FIXTURES / "candidate_rule_as_policy", fixture_mode=True)
    hits = _findings_for("CANDIDATE-RULE-AS-POLICY", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_lesson_as_policy_blocked_or_degraded():
    """Lesson presented as policy -> BLOCKED or DEGRADED."""
    findings, records = discover_memory_surfaces(FIXTURES / "lesson_as_policy", fixture_mode=True)
    hits = _findings_for("LESSON-AS-POLICY", findings)
    assert len(hits) >= 1
    assert hits[0].status in ("BLOCKED", "DEGRADED")


def test_degraded_blocked_as_fact():
    """DEGRADED/BLOCKED treated as factual business state -> findings."""
    findings, records = discover_memory_surfaces(FIXTURES / "degraded_blocked_as_fact", fixture_mode=True)
    hits = _findings_for("DEGRADED-BLOCKED-AS-FACT", findings)
    assert len(hits) >= 1


def test_memory_records_not_current_truth_by_default():
    """Discovered memory records must not be current_truth_allowed."""
    findings, records = discover_memory_surfaces(FIXTURES / "clean_memory", fixture_mode=True)
    for r in records:
        assert r.current_truth_allowed is False


def test_memory_surfaces_produce_artifact_records():
    """Discovered memory files should produce ArtifactRecord entries."""
    findings, records = discover_memory_surfaces(FIXTURES / "clean_memory", fixture_mode=True)
    assert len(records) >= 1
    types = {r.artifact_type for r in records}
    assert "memory_ledger" in types


def test_memory_records_are_t3():
    """Memory artifact records should default to T3."""
    findings, records = discover_memory_surfaces(FIXTURES / "clean_memory", fixture_mode=True)
    for r in records:
        assert r.authority_tier.value == "T3_CANDIDATE_PROPOSAL"


def test_fixture_mode_scans_unsafe():
    """Fixture mode should scan unsafe fixtures."""
    findings, records = discover_memory_surfaces(FIXTURES / "missing_source", fixture_mode=True)
    assert len(findings) > 0


def test_production_mode_excludes_fixtures():
    """Production mode should not find fixtures when run from parent."""
    # Run from parent dir, not the fixture dir directly
    findings, _ = discover_memory_surfaces(FIXTURES, fixture_mode=False)
    # All fixtures are under tests/fixtures/ -> excluded
    assert len(findings) == 0
