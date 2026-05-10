"""Tests for metabolic governance — auto-discovery, registry, and dry-run findings."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory


from ordivon_verify.metabolic.discover import discover_artifacts
from ordivon_verify.metabolic.models import (
    ArtifactRecord,
    ArtifactTemperature,
    AuthorityTier,
    LifecycleState,
)
from ordivon_verify.metabolic.registry import build_registry, plan_metabolic_actions


def _write(root: Path, path: str, content: str) -> Path:
    dest = root / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    return dest


def test_manifest_exists_in_emitted_pack():
    """Manifest file should be discovered as a manifest artifact."""
    with TemporaryDirectory() as td:
        root = Path(td)
        _write(root, ".ordivon/manifest.json", "{}")
        records = discover_artifacts(root)
        assert len(records) >= 1
        manifests = [r for r in records if r.artifact_type == "manifest"]
        assert len(manifests) == 1
        assert manifests[0].artifact_type == "manifest"


def test_current_truth_exists_in_emitted_pack():
    """CURRENT_TRUTH.md should be discovered at T0."""
    with TemporaryDirectory() as td:
        root = Path(td)
        _write(root, ".ordivon/CURRENT_TRUTH.md", "# Current Truth")
        records = discover_artifacts(root)
        cts = [r for r in records if r.artifact_type == "current_truth"]
        assert len(cts) == 1
        assert cts[0].authority_tier == AuthorityTier.T0_CURRENT_TRUTH
        assert cts[0].current_truth_allowed is True


def test_generated_registry_exists():
    """Generated registry json should be discoverable."""
    with TemporaryDirectory() as td:
        root = Path(td)
        _write(root, ".ordivon/graph/generated-artifact-registry.json", "{}")
        records = discover_artifacts(root)
        regs = [r for r in records if r.artifact_type == "registry"]
        assert len(regs) >= 1


def test_generated_registry_contains_artifact_records():
    """Registry built from discovered records has the records populated."""
    with TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "ordivon.verify.json", "{}")
        _write(root, "PROJECT_AI_LOCALIZATION.md", "# Localization")
        records = discover_artifacts(root)
        registry = build_registry(records, str(root))
        assert len(registry.records) >= 2


def test_artifact_records_have_authority_tier():
    """Every discovered artifact has non-None authority_tier."""
    with TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "ordivon.verify.json", "{}")
        _write(root, "SKILL.md", "# Skill")
        records = discover_artifacts(root)
        for r in records:
            assert r.authority_tier is not None
            assert isinstance(r.authority_tier, AuthorityTier)


def test_t3_candidate_cannot_be_current_truth():
    """T3 candidate with current_truth_allowed=True → BLOCKED finding."""
    record = ArtifactRecord(
        artifact_id="test-candidate",
        path="candidate.json",
        artifact_type="candidate",
        authority_tier=AuthorityTier.T3_CANDIDATE_PROPOSAL,
        lifecycle_state=LifecycleState.CANDIDATE,
        temperature=ArtifactTemperature.COLD,
        owner="test-owner",
        scope="test",
        current_truth_allowed=True,
    )
    registry = build_registry([record], "/tmp/test")
    findings = plan_metabolic_actions(registry)
    codes = [f.code for f in findings]
    assert "ENTROPY-CANDIDATE-AS-TRUTH" in codes


def test_t4_archive_cannot_be_current_truth():
    """T4 archive with current_truth_allowed=True → BLOCKED finding."""
    record = ArtifactRecord(
        artifact_id="test-archive",
        path="archive.json",
        artifact_type="archive",
        authority_tier=AuthorityTier.T4_HISTORICAL_ARCHIVE,
        lifecycle_state=LifecycleState.ACTIVE,
        temperature=ArtifactTemperature.COLD,
        owner=None,
        scope="test",
        current_truth_allowed=True,
    )
    registry = build_registry([record], "/tmp/test")
    findings = plan_metabolic_actions(registry)
    codes = [f.code for f in findings]
    assert "ENTROPY-ARCHIVE-AS-TRUTH" in codes


def test_t5_tombstone_requires_reason_or_supersession():
    """T5 deprecated without reason → DEGRADED finding."""
    record = ArtifactRecord(
        artifact_id="test-tomb",
        path="old.json",
        artifact_type="schema",
        authority_tier=AuthorityTier.T5_DEPRECATED_TOMBSTONED,
        lifecycle_state=LifecycleState.TOMBSTONED,
        temperature=ArtifactTemperature.TOMBSTONED,
        owner=None,
        scope="test",
        superseded_by=None,
        notes=None,
    )
    registry = build_registry([record], "/tmp/test")
    findings = plan_metabolic_actions(registry)
    codes = [f.code for f in findings]
    assert "ENTROPY-TOMBSTONE-NO-REASON" in codes


def test_active_artifact_missing_owner():
    """Active T1 artifact without owner → DEGRADED."""
    record = ArtifactRecord(
        artifact_id="no-owner",
        path="spec.json",
        artifact_type="schema",
        authority_tier=AuthorityTier.T1_ACTIVE_SPEC,
        lifecycle_state=LifecycleState.ACTIVE,
        temperature=ArtifactTemperature.WARM,
        owner=None,
        scope="test",
    )
    registry = build_registry([record], "/tmp/test")
    findings = plan_metabolic_actions(registry)
    codes = [f.code for f in findings]
    assert "ENTROPY-MISSING-OWNER" in codes


def test_active_artifact_missing_last_verified():
    """Active T1 artifact without last_verified → DEGRADED."""
    record = ArtifactRecord(
        artifact_id="no-verified",
        path="spec.json",
        artifact_type="schema",
        authority_tier=AuthorityTier.T1_ACTIVE_SPEC,
        lifecycle_state=LifecycleState.ACTIVE,
        temperature=ArtifactTemperature.WARM,
        owner="someone",
        scope="test",
        last_verified=None,
    )
    registry = build_registry([record], "/tmp/test")
    findings = plan_metabolic_actions(registry)
    codes = [f.code for f in findings]
    assert "ENTROPY-MISSING-VERIFIED" in codes


def test_healthy_artifact_produces_no_findings():
    """A properly registered T0 artifact produces no findings."""
    record = ArtifactRecord(
        artifact_id="healthy",
        path="CURRENT_TRUTH.md",
        artifact_type="current_truth",
        authority_tier=AuthorityTier.T0_CURRENT_TRUTH,
        lifecycle_state=LifecycleState.ACTIVE,
        temperature=ArtifactTemperature.HOT,
        owner="project-owner",
        scope="project",
        last_verified="2026-05-08",
        content_hash="abc123",
    )
    registry = build_registry([record], "/tmp/test")
    findings = plan_metabolic_actions(registry)
    assert len(findings) == 0


def test_discover_artifacts_skips_binary():
    """Binary files should not be classified."""
    with TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "file.pyc", "binary")
        _write(root, "file.so", "binary")
        records = discover_artifacts(root)
        assert len(records) == 0


def test_discover_artifacts_skips_git():
    """Files in .git directory should not be classified."""
    with TemporaryDirectory() as td:
        root = Path(td)
        _write(root, ".git/config", "content")
        _write(root, "README.md", "# Hello")
        records = discover_artifacts(root)
        assert len(records) == 0  # README.md not in convention rules
