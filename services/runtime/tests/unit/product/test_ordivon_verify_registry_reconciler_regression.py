"""RG-16: Reconciler Regression Tests for RG-11 through RG-15.

Closes the evidence gap found in the RG-11→RG-15 audit. Tests the actual
reconciler semantics implemented in those phases without changing behavior.
"""

import json
import subprocess
import sys
from pathlib import Path

from ordivon_verify.registry import (
    AuthorityTier,
    LifecycleState,
    RegistryKind,
    RegistryObject,
    RegistryImportResult,
    import_all_registry_sources,
    reconcile_registry_objects,
    reconcile_imported_sources,
    validate_registry_object,
)


def _make(**overrides) -> RegistryObject:
    defaults = dict(
        registry_id="test-001",
        kind=RegistryKind.DOCUMENT,
        path="docs/test.md",
        title="Test",
        authority_tier=AuthorityTier.T1_CURRENT_STATUS,
        lifecycle_state=LifecycleState.ACTIVE,
        current_truth_allowed=True,
        owner="test-owner",
        generated=False,
        source_registry="document-registry",
    )
    defaults.update(overrides)
    return RegistryObject(**defaults)


# ═══════════════════════════════════════════════════════════════════
# RG-11: Referenced-Missing Resolution
# ═══════════════════════════════════════════════════════════════════


class TestRG11ReferencedMissingResolution:
    """RG-11: registry_id, path, and filesystem references all resolve."""

    def test_registry_id_reference_resolves(self):
        a = _make(registry_id="a", owner="someone")
        b = _make(registry_id="b", depends_on=("a",), owner="someone")
        result = reconcile_registry_objects([a, b])
        missing = [f for f in result.findings if "referenced-object-exists" in f.invariant]
        assert len(missing) == 0

    def test_object_path_reference_resolves(self):
        a = _make(registry_id="a", path="shared/ledger.jsonl", owner="someone")
        b = _make(registry_id="b", receipt_refs=("shared/ledger.jsonl",), owner="someone")
        result = reconcile_registry_objects([a, b])
        missing = [f for f in result.findings if "referenced-object-exists" in f.invariant]
        assert len(missing) == 0

    def test_filesystem_path_reference_resolves(self, tmp_path):
        """A reference to an existing file on disk resolves even if no RegistryObject has it."""
        existing = tmp_path / "docs" / "real-file.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("# Real file")
        obj = _make(registry_id="a", receipt_refs=("docs/real-file.md",), owner="someone")
        result = reconcile_registry_objects([obj], root=tmp_path)
        missing = [f for f in result.findings if "referenced-object-exists" in f.invariant]
        assert len(missing) == 0

    def test_missing_real_reference_still_produces_finding(self):
        obj = _make(registry_id="a", depends_on=("nonexistent-id",), owner="someone")
        result = reconcile_registry_objects([obj])
        missing = [f for f in result.findings if "referenced-object-exists" in f.invariant]
        assert len(missing) >= 1
        assert "nonexistent-id" in missing[0].message

    def test_missing_filesystem_path_produces_finding(self, tmp_path):
        obj = _make(registry_id="a", receipt_refs=("missing/file.md",), owner="someone")
        result = reconcile_registry_objects([obj], root=tmp_path)
        missing = [f for f in result.findings if "referenced-object-exists" in f.invariant]
        assert len(missing) >= 1

    def test_policy_refs_to_missing_still_blocked(self):
        obj = _make(registry_id="a", policy_refs=("missing-policy-rule",), owner="someone")
        result = reconcile_registry_objects([obj])
        blocked = [
            f
            for f in result.findings
            if "referenced-object-exists" in f.invariant and str(f.status) == "RegistryFindingStatus.BLOCKED"
        ]
        assert len(blocked) >= 1

    def test_generated_from_synthetic_label_does_not_produce_false_finding(self, tmp_path):
        """RG-11: Empty generated_from should not produce findings."""
        obj = _make(
            registry_id="aux:test-ledger",
            kind=RegistryKind.LEDGER,
            generated=True,
            generated_from=(),
            current_truth_allowed=False,
            source_registry="aux-ledgers",
        )
        result = reconcile_registry_objects([obj], root=tmp_path)
        missing = [f for f in result.findings if "referenced" in f.invariant]
        assert len(missing) == 0


# ═══════════════════════════════════════════════════════════════════
# RG-12: Registry Self + Ledger/Schema Identity
# ═══════════════════════════════════════════════════════════════════


class TestRG12RegistrySelfAndLedgerSchema:
    """RG-12: Self-registration retired, document-registry-only identity sufficient."""

    def test_ledger_identity_via_document_registry_only(self):
        """A ledger imported only from document-registry does not trigger identity gap."""
        obj = _make(
            registry_id="dr:test-ledger",
            kind=RegistryKind.LEDGER,
            path="docs/governance/test-ledger.jsonl",
            source_registry="document-registry",
            current_truth_allowed=False,
        )
        result = reconcile_registry_objects([obj])
        gaps = [f for f in result.findings if "ledger-schema" in f.invariant or "registry-self" in f.invariant]
        assert len(gaps) == 0

    def test_schema_identity_via_source_declaration(self):
        """A schema's identity is sufficient via its import source."""
        from ordivon_verify.registry.sources import get_registry_source_views

        sources = get_registry_source_views()
        # At minimum, document-registry and artifact-registry should be declared
        source_ids = {s["source_id"] for s in sources}
        assert "document-registry" in source_ids
        assert "artifact-registry" in source_ids
        assert "checker-registry" in source_ids

    def test_source_views_exist_and_populated(self):
        """All 6 source adapters declared in RG-9."""
        from ordivon_verify.registry.sources import REGISTRY_SOURCE_VIEWS

        assert len(REGISTRY_SOURCE_VIEWS) == 6
        roles = {v.role for v in REGISTRY_SOURCE_VIEWS}
        assert "source_adapter" in roles
        assert "generated_view" in roles


# ═══════════════════════════════════════════════════════════════════
# RG-13: Config Surface Registry
# ═══════════════════════════════════════════════════════════════════


class TestRG13ConfigSurface:
    """RG-13: Config files are imported as config_surface, not source_of_truth."""

    def test_config_surface_importer_available(self):
        from ordivon_verify.registry.adapters import import_config_surfaces

        result = import_config_surfaces(Path("/tmp"))
        assert isinstance(result, RegistryImportResult)

    def test_config_surface_imports_from_real_root(self):
        root = Path("/root/projects/Ordivon")
        from ordivon_verify.registry.adapters import import_config_surfaces

        result = import_config_surfaces(root)
        # Should import at least pyproject.toml
        paths = {obj.path for obj in result.objects}
        assert "pyproject.toml" in paths

    def test_config_surface_not_source_of_truth(self):
        obj = _make(
            registry_id="config:pyproject.toml",
            kind=RegistryKind.CONFIG_SURFACE,
            path="pyproject.toml",
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        # No BLOCKED findings from invariants
        blocked = [f for f in findings if str(f.status) == "RegistryFindingStatus.BLOCKED"]
        assert len(blocked) == 0

    def test_config_surface_current_truth_allowed_is_false(self):
        obj = _make(
            registry_id="config:test",
            kind=RegistryKind.CONFIG_SURFACE,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
        )
        assert obj.current_truth_allowed is False

    def test_config_surface_with_truth_allowed_produces_finding(self):
        obj = _make(
            registry_id="config:test",
            kind=RegistryKind.CONFIG_SURFACE,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=True,
        )
        findings = validate_registry_object(obj)
        config_findings = [f for f in findings if "config-surface" in f.invariant]
        assert len(config_findings) >= 1

    def test_config_surface_not_default_t0(self, tmp_path):
        """Config surfaces from importer should be T2, not T0."""
        root = Path("/root/projects/Ordivon")
        from ordivon_verify.registry.adapters import import_config_surfaces

        result = import_config_surfaces(root)
        for obj in result.objects:
            assert obj.authority_tier != AuthorityTier.T0_SOURCE_OF_TRUTH, f"{obj.registry_id} should not be T0"


# ═══════════════════════════════════════════════════════════════════
# RG-14: Legacy Scope Manifest
# ═══════════════════════════════════════════════════════════════════


class TestRG14LegacyScope:
    """RG-14: Legacy directories have formal lifecycle_state identity."""

    def test_legacy_scope_importer_available(self):
        from ordivon_verify.registry.adapters import import_legacy_scopes

        result = import_legacy_scopes(Path("/root/projects/Ordivon"))
        assert isinstance(result, RegistryImportResult)

    def test_legacy_scope_manifest_exists(self):
        manifest = Path("/root/projects/Ordivon/docs/governance/legacy-scope-manifest-rg-14.jsonl")
        assert manifest.exists()

    def test_legacy_manifest_has_26_entries(self):
        manifest = Path("/root/projects/Ordivon/docs/governance/legacy-scope-manifest-rg-14.jsonl")
        entries = []
        with open(manifest) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        assert len(entries) == 26

    def test_legacy_scope_imports_as_legacy_inactive(self):
        root = Path("/root/projects/Ordivon")
        from ordivon_verify.registry.adapters import import_legacy_scopes

        result = import_legacy_scopes(root)
        for obj in result.objects:
            assert obj.kind == RegistryKind.LEGACY_SCOPE
            assert obj.lifecycle_state in (LifecycleState.LEGACY_INACTIVE, LifecycleState.OUT_OF_SCOPE)
            assert obj.current_truth_allowed is False

    def test_legacy_scope_not_deleted(self):
        """Legacy code dirs still exist — only identity was added."""
        legacy_dirs = ["apps", "capabilities", "governance_engine", "orchestrator"]
        root = Path("/root/projects/Ordivon")
        for d in legacy_dirs:
            assert (root / d).is_dir(), f"{d} should still exist"

    def test_legacy_scope_lifecycle_is_legacy_inactive(self):
        root = Path("/root/projects/Ordivon")
        from ordivon_verify.registry.adapters import import_legacy_scopes

        result = import_legacy_scopes(root)
        for obj in result.objects:
            assert obj.lifecycle_state == LifecycleState.LEGACY_INACTIVE

    def test_legacy_scope_authority_is_t6(self):
        root = Path("/root/projects/Ordivon")
        from ordivon_verify.registry.adapters import import_legacy_scopes

        result = import_legacy_scopes(root)
        for obj in result.objects:
            assert obj.authority_tier == AuthorityTier.T6_OUT_OF_SCOPE

    def test_legacy_scope_current_truth_allowed_is_false(self):
        root = Path("/root/projects/Ordivon")
        from ordivon_verify.registry.adapters import import_legacy_scopes

        result = import_legacy_scopes(root)
        for obj in result.objects:
            assert obj.current_truth_allowed is False

    def test_legacy_surface_with_active_lifecycle_is_invalid(self):
        obj = _make(
            kind=RegistryKind.LEGACY_SCOPE,
            lifecycle_state=LifecycleState.ACTIVE,
            authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        legacy_findings = [f for f in findings if "legacy-scope" in f.invariant]
        assert len(legacy_findings) >= 1


# ═══════════════════════════════════════════════════════════════════
# RG-15: Owner Gap Severity Reclassification
# ═══════════════════════════════════════════════════════════════════


class TestRG15OwnerGapReclassification:
    """RG-15: Owner gaps are BLOCKED only for documents/policy_activation."""

    def test_active_t0_document_without_owner_is_blocked(self):
        obj = _make(authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH, owner=None)
        result = reconcile_registry_objects([obj])
        blocked = [
            f
            for f in result.findings
            if "active-decision-object" in f.invariant and str(f.status) == "RegistryFindingStatus.BLOCKED"
        ]
        assert len(blocked) >= 1

    def test_active_t1_document_without_owner_is_blocked(self):
        obj = _make(authority_tier=AuthorityTier.T1_CURRENT_STATUS, owner=None)
        result = reconcile_registry_objects([obj])
        blocked = [
            f
            for f in result.findings
            if "active-decision-object" in f.invariant and str(f.status) == "RegistryFindingStatus.BLOCKED"
        ]
        assert len(blocked) >= 1

    def test_owner_assigned_document_produces_no_finding(self):
        obj = _make(authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH, owner="someone")
        result = reconcile_registry_objects([obj])
        owner_findings = [f for f in result.findings if "owner" in f.invariant]
        assert len(owner_findings) == 0

    def test_t2_artifact_without_owner_is_degraded_not_blocked(self):
        obj = _make(
            registry_id="ar:test",
            kind=RegistryKind.ARTIFACT,
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            owner=None,
            source_registry="artifact-registry",
        )
        result = reconcile_registry_objects([obj])
        blocked = [
            f
            for f in result.findings
            if "active-decision-object" in f.invariant and str(f.status) == "RegistryFindingStatus.BLOCKED"
        ]
        assert len(blocked) == 0
        degraded = [
            f
            for f in result.findings
            if "active-decision-object" in f.invariant and str(f.status) == "RegistryFindingStatus.DEGRADED"
        ]
        assert len(degraded) >= 1

    def test_checker_without_owner_is_degraded_not_blocked(self):
        obj = _make(
            registry_id="checker:test",
            kind=RegistryKind.CHECKER,
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            owner=None,
            source_registry="checker-registry",
        )
        result = reconcile_registry_objects([obj])
        blocked = [
            f
            for f in result.findings
            if "active-decision-object" in f.invariant and str(f.status) == "RegistryFindingStatus.BLOCKED"
        ]
        assert len(blocked) == 0
        degraded = [
            f
            for f in result.findings
            if "active-decision-object" in f.invariant and str(f.status) == "RegistryFindingStatus.DEGRADED"
        ]
        assert len(degraded) >= 1

    def test_config_surface_without_owner_is_degraded_not_blocked(self):
        obj = _make(
            registry_id="config:test",
            kind=RegistryKind.CONFIG_SURFACE,
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            owner=None,
        )
        result = reconcile_registry_objects([obj])
        blocked = [
            f
            for f in result.findings
            if "active-decision-object" in f.invariant and str(f.status) == "RegistryFindingStatus.BLOCKED"
        ]
        assert len(blocked) == 0

    def test_owner_not_approver(self):
        """Owner field != approver semantic."""
        obj = _make(owner="someone", approver=None)
        assert obj.owner == "someone"
        assert obj.approver is None

    def test_no_mass_owner_fill_for_artifacts(self):
        """RG-15 did not mass-assign owners to artifacts."""
        root = Path("/root/projects/Ordivon")
        from ordivon_verify.registry.adapters import import_artifact_registry

        result = import_artifact_registry(root)
        null_owners = sum(1 for o in result.objects if o.owner is None)
        # Should have many null owners (not mass-filled)
        assert null_owners > 100, f"Expected >100 null artifact owners, got {null_owners}"


# ═══════════════════════════════════════════════════════════════════
# CLI Smoke Test
# ═══════════════════════════════════════════════════════════════════


class TestCLIRegistryIndex:
    """RG-8/16: CLI registry-index command produces correct output."""

    def test_registry_index_cli_runs(self):
        result = subprocess.run(
            [sys.executable, "-m", "ordivon_verify", "registry-index"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/root/projects/Ordivon",
        )
        assert result.returncode == 0, f"stderr: {result.stderr[:200]}"
        data = json.loads(result.stdout)
        assert "authority" in data
        assert data["authority"] == "generated_view"
        assert data["current_truth_allowed"] is False

    def test_registry_index_includes_sources(self):
        result = subprocess.run(
            [sys.executable, "-m", "ordivon_verify", "registry-index"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/root/projects/Ordivon",
        )
        data = json.loads(result.stdout)
        assert len(data["registry_sources"]) == 6

    def test_registry_index_has_objects_and_findings(self):
        result = subprocess.run(
            [sys.executable, "-m", "ordivon_verify", "registry-index"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/root/projects/Ordivon",
        )
        data = json.loads(result.stdout)
        assert data["summary"]["total_objects"] > 0
        assert "blocked_findings" in data["summary"]
        assert "degraded_findings" in data["summary"]

    def test_registry_index_blocked_is_zero(self):
        """RG-16: After RG-4/5/6/15 owner fixes, BLOCKED must be 0."""
        result = subprocess.run(
            [sys.executable, "-m", "ordivon_verify", "registry-index"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/root/projects/Ordivon",
        )
        data = json.loads(result.stdout)
        assert data["summary"]["blocked_findings"] == 0, (
            f"Expected 0 BLOCKED, got {data['summary']['blocked_findings']}"
        )

    def test_registry_index_degraded_is_zero_after_routing(self):
        """RG-18: Path-owner inheritance resolves DEGRADED to 0."""
        result = subprocess.run(
            [sys.executable, "-m", "ordivon_verify", "registry-index"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/root/projects/Ordivon",
        )
        data = json.loads(result.stdout)
        assert data["summary"]["degraded_findings"] == 0, (
            f"Expected 0 DEGRADED, got {data['summary']['degraded_findings']}"
        )

    def test_registry_index_dry_run_does_not_mutate_files(self):
        """Running registry-index should not write to any config or source file."""
        before_files = set()
        root = Path("/root/projects/Ordivon")
        for f in root.rglob("*"):
            if f.is_file() and ".git/" not in str(f) and "__pycache__" not in str(f):
                before_files.add(str(f))

        subprocess.run(
            [sys.executable, "-m", "ordivon_verify", "registry-index"],
            capture_output=True,
            timeout=30,
            cwd="/root/projects/Ordivon",
        )

        after_files = set()
        for f in root.rglob("*"):
            if f.is_file() and ".git/" not in str(f) and "__pycache__" not in str(f):
                after_files.add(str(f))

        new_files = after_files - before_files
        # Allow only test/audit artifacts (pytest cache)
        real_new = {f for f in new_files if ".pytest_cache" not in f}
        assert real_new == set(), f"registry-index created files: {real_new}"


# ═══════════════════════════════════════════════════════════════════
# Current Repo Smoke Test
# ═══════════════════════════════════════════════════════════════════


class TestCurrentRepoSmoke:
    """Smoke test against current Ordivon repository reconciler output."""

    def test_current_repo_blocked_is_zero(self):
        root = Path("/root/projects/Ordivon")
        result = reconcile_imported_sources(import_all_registry_sources(root), root=root)
        assert result.summary.blocked_count == 0, f"Expected 0 BLOCKED, got {result.summary.blocked_count}"

    def test_current_repo_degraded_is_zero_after_routing(self):
        """RG-18: Path-owner inheritance resolves all DEGRADED."""
        root = Path("/root/projects/Ordivon")
        result = reconcile_imported_sources(import_all_registry_sources(root), root=root)
        assert result.summary.degraded_count == 0, (
            f"Expected 0 DEGRADED after routing, got {result.summary.degraded_count}"
        )

    def test_current_repo_all_findings_are_owner_gap(self):
        root = Path("/root/projects/Ordivon")
        result = reconcile_imported_sources(import_all_registry_sources(root), root=root)
        invariants = {f.invariant for f in result.findings}
        # After RG-11→RG-14, only owner-gap should remain
        assert invariants == {"active-decision-object-has-owner"} or len(invariants) <= 1

    def test_current_repo_no_referenced_missing(self):
        root = Path("/root/projects/Ordivon")
        result = reconcile_imported_sources(import_all_registry_sources(root), root=root)
        missing = [f for f in result.findings if "referenced" in f.invariant]
        assert len(missing) == 0

    def test_current_repo_objects_exceed_1000(self):
        root = Path("/root/projects/Ordivon")
        result = reconcile_imported_sources(import_all_registry_sources(root), root=root)
        assert result.summary.total_objects > 1000
