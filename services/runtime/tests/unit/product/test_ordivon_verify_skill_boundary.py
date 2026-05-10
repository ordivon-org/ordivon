"""Tests for Skill / Tool Boundary Scanner Alpha."""

from __future__ import annotations

from pathlib import Path

from ordivon_verify.scanners.skill_boundary import discover_skill_surfaces

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "skill_boundary"


def _findings_for(code: str, findings):
    return [f for f in findings if f.code == code]


def test_clean_skill_no_blocked():
    """Clean skill with proper boundaries should have no BLOCKED findings."""
    findings, records = discover_skill_surfaces(FIXTURES / "clean_skill", fixture_mode=True)
    blocked = [f for f in findings if f.status == "BLOCKED"]
    assert len(blocked) == 0, f"Unexpected BLOCKED findings: {blocked}"


def test_clean_skill_produces_record():
    """Clean skill should generate an artifact record."""
    findings, records = discover_skill_surfaces(FIXTURES / "clean_skill", fixture_mode=True)
    assert len(records) == 1
    assert records[0].artifact_type == "skill"
    assert records[0].current_truth_allowed is False


def test_credential_request_blocked():
    """Skill requesting credentials without boundary -> BLOCKED."""
    findings, records = discover_skill_surfaces(FIXTURES / "credential_request_skill", fixture_mode=True)
    hits = _findings_for("SKILL-CREDENTIAL-REQUEST", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_broad_allowed_tools_blocked():
    """Bash(*) / overbroad allowed-tools -> BLOCKED."""
    findings, records = discover_skill_surfaces(FIXTURES / "broad_allowed_tools_skill", fixture_mode=True)
    hits = _findings_for("SKILL-ALLOWED-TOOLS-BROAD", findings)
    assert len(hits) >= 1
    assert hits[0].status == "BLOCKED"


def test_deploy_authorization_laundering_blocked():
    """Skill claiming deploy/approve authority -> BLOCKED."""
    findings, records = discover_skill_surfaces(FIXTURES / "deploy_authorization_laundering_skill", fixture_mode=True)
    deploy_hits = _findings_for("SKILL-DEPLOY-AUTHORIZATION-LAUNDERING", findings)
    tool_hits = _findings_for("SKILL-TOOL-AS-AUTHORIZATION", findings)
    assert len(deploy_hits) + len(tool_hits) >= 1
    all_blocked = [f for f in deploy_hits + tool_hits if f.status == "BLOCKED"]
    assert len(all_blocked) >= 1


def test_script_side_effect_degraded():
    """Script references without side-effect boundary -> DEGRADED."""
    findings, records = discover_skill_surfaces(FIXTURES / "unclear_script_side_effect_skill", fixture_mode=True)
    hits = _findings_for("SKILL-SCRIPT-SIDE-EFFECT-UNCLEAR", findings)
    assert len(hits) >= 1
    assert hits[0].status == "DEGRADED"


def test_missing_non_auth_boundary_degraded():
    """Governance skill without non-auth boundary -> DEGRADED."""
    findings, records = discover_skill_surfaces(FIXTURES / "missing_non_auth_boundary", fixture_mode=True)
    hits = _findings_for("SKILL-MISSING-NON-AUTH-BOUNDARY", findings)
    assert len(hits) >= 1
    assert hits[0].status == "DEGRADED"


def test_all_skill_records_have_authority_tier():
    """Every discovered skill record has a non-None authority tier."""
    for fixture_dir in sorted(FIXTURES.iterdir()):
        if not fixture_dir.is_dir():
            continue
        findings, records = discover_skill_surfaces(fixture_dir)
        for r in records:
            assert r.authority_tier is not None
            assert r.artifact_type == "skill"


def test_discovered_skills_not_current_truth():
    """Discovered skills must not have current_truth_allowed=True."""
    for fixture_dir in sorted(FIXTURES.iterdir()):
        if not fixture_dir.is_dir():
            continue
        findings, records = discover_skill_surfaces(fixture_dir)
        for r in records:
            assert r.current_truth_allowed is False, f"Skill {r.artifact_id} should not be current truth"


def test_discovered_skills_not_canonical_policy():
    """Discovered skills should be T3 candidate, not T0/T1 active spec."""
    for fixture_dir in sorted(FIXTURES.iterdir()):
        if not fixture_dir.is_dir():
            continue
        findings, records = discover_skill_surfaces(fixture_dir)
        for r in records:
            assert r.authority_tier.value in ("T3_CANDIDATE_PROPOSAL",), (
                f"Skill {r.artifact_id} has tier {r.authority_tier.value}, expected T3"
            )
