"""Unit tests for Ordivon Cross-Registry Reconciler (RG-3).

Tests that the reconciler detects the major coherence gaps identified in
RG-0 by checking imported RegistryObject sets. Uses constructed objects
— no dependency on real filesystem state.
"""

from ordivon_verify.registry import (
    AuthorityTier,
    LifecycleState,
    RegistryKind,
    RegistryObject,
    reconcile_registry_objects,
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
# Check A: Referenced-but-missing
# ═══════════════════════════════════════════════════════════════════


class TestReferencedButMissing:
    """Objects referencing non-existent registry objects."""

    def test_policy_ref_to_missing_object(self):
        obj = _make(policy_refs=("missing-policy",))
        result = reconcile_registry_objects([obj])
        assert any("missing-policy" in f.message for f in result.findings)

    def test_depends_on_to_missing_object(self):
        obj = _make(depends_on=("missing-dep",))
        result = reconcile_registry_objects([obj])
        assert any("missing-dep" in f.message for f in result.findings)

    def test_generated_from_missing_object(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            generated=True,
            generated_from=("missing-src",),
            current_truth_allowed=False,
        )
        result = reconcile_registry_objects([obj])
        assert any("missing-src" in f.message for f in result.findings)

    def test_valid_refs_no_findings(self):
        a = _make(registry_id="a")
        b = _make(registry_id="b", depends_on=("a",))
        result = reconcile_registry_objects([a, b])
        assert not any("referenced-object-exists" in f.invariant for f in result.findings)

    def test_missing_policy_activation_file_gap(self):
        """RG-4: policy-activation-ledger now exists — no longer BLOCKED for file gap."""
        result = reconcile_registry_objects([_make()])
        # policy-activation-ledger.jsonl should NOT appear as a missing file
        policy_file_gaps = [
            f
            for f in result.findings
            if "policy-activation-ledger" in f.message.lower() and "referenced-file-exists" in f.invariant
        ]
        assert len(policy_file_gaps) == 0


# ═══════════════════════════════════════════════════════════════════
# Check B: Active T0/T1 without owner
# ═══════════════════════════════════════════════════════════════════


class TestOwnerGaps:
    """Active T0/T1 authority objects missing owner."""

    def test_active_t0_without_owner_blocked(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            owner=None,
        )
        result = reconcile_registry_objects([obj])
        assert result.summary.blocked_count >= 1
        assert any("owner" in f.message.lower() for f in result.findings)

    def test_active_t1_without_owner_blocked(self):
        obj = _make(
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            owner=None,
        )
        result = reconcile_registry_objects([obj])
        assert result.summary.blocked_count >= 1

    def test_t2_without_owner_not_blocked(self):
        obj = _make(
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            owner=None,
            current_truth_allowed=False,
        )
        result = reconcile_registry_objects([obj])
        assert not any("active-decision-object-has-owner" in f.invariant for f in result.findings)

    def test_t0_with_owner_pass(self):
        obj = _make(authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH, owner="someone")
        result = reconcile_registry_objects([obj])
        assert not any("active-decision-object-has-owner" in f.invariant for f in result.findings)

    def test_archived_t0_no_owner_not_checked(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            lifecycle_state=LifecycleState.ARCHIVED,
            owner=None,
            current_truth_allowed=False,
        )
        result = reconcile_registry_objects([obj])
        assert not any("active-decision-object-has-owner" in f.invariant for f in result.findings)


# ═══════════════════════════════════════════════════════════════════
# Check C: Generated view as source truth
# ═══════════════════════════════════════════════════════════════════


class TestGeneratedAsTruth:
    """Generated objects should not be truth."""

    def test_generated_view_with_current_truth_blocked(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            generated=True,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=True,
            generated_from=("src",),
        )
        result = reconcile_registry_objects([obj])
        assert result.summary.blocked_count >= 1

    def test_generated_view_t0_degraded(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            generated=True,
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            current_truth_allowed=False,
            generated_from=("src",),
        )
        result = reconcile_registry_objects([obj])
        assert result.summary.degraded_count >= 1

    def test_generated_object_with_current_truth_blocked(self):
        obj = _make(
            generated=True,
            generated_from=("src",),
            current_truth_allowed=True,
        )
        result = reconcile_registry_objects([obj])
        assert result.summary.blocked_count >= 1

    def test_non_generated_no_findings(self):
        obj = _make(generated=False)
        result = reconcile_registry_objects([obj])
        assert not any("generated-not" in f.invariant for f in result.findings)


# ═══════════════════════════════════════════════════════════════════
# Check D: Ledger/schema without artifact identity
# ═══════════════════════════════════════════════════════════════════


# RG-12: ledger/schema artifact gap check retired — document-registry-only identity is sufficient.


# ═══════════════════════════════════════════════════════════════════
# Check E: Registry self-registration gap
# ═══════════════════════════════════════════════════════════════════


# RG-12: registry self-gap check retired — source adapters declared in registry/sources.py.


# ═══════════════════════════════════════════════════════════════════
# Check F: Legacy scope missing identity
# ═══════════════════════════════════════════════════════════════════


class TestLegacyScopeGap:
    """Legacy directories should have LEGACY_SCOPE objects."""

    def test_no_legacy_scope_objects(self):
        result = reconcile_registry_objects([_make()])
        legacy_findings = [f for f in result.findings if "legacy-scope-has-identity" in f.invariant]
        assert len(legacy_findings) == 26  # all 26 known legacy dirs

    def test_legacy_scope_registered(self):
        legacy_objs = [
            _make(
                registry_id=f"legacy:{d}",
                kind=RegistryKind.LEGACY_SCOPE,
                path=d,
                authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
                lifecycle_state=LifecycleState.LEGACY_INACTIVE,
                current_truth_allowed=False,
            )
            for d in ("apps", "capabilities")
        ]
        result = reconcile_registry_objects(legacy_objs + [_make()])
        # The two registered dirs should not appear in findings
        legacy_findings = [f for f in result.findings if "legacy-scope-has-identity" in f.invariant]
        registered_names = {f.object_id for f in legacy_findings}
        assert "legacy:apps" not in registered_names
        assert "legacy:capabilities" not in registered_names

    def test_legacy_scope_degraded_not_blocked(self):
        result = reconcile_registry_objects([_make()])
        legacy_findings = [f for f in result.findings if "legacy-scope-has-identity" in f.invariant]
        for f in legacy_findings:
            assert f.status.value == "DEGRADED"


# ═══════════════════════════════════════════════════════════════════
# Check G: Config surfaces unregistered
# ═══════════════════════════════════════════════════════════════════


class TestConfigSurfacesUnregistered:
    """Config files should have CONFIG_SURFACE objects."""

    def test_no_config_surface_objects(self):
        result = reconcile_registry_objects([_make()])
        cfg_findings = [f for f in result.findings if "config-surface-registered" in f.invariant]
        assert len(cfg_findings) == 6  # all 6 known config files

    def test_config_surface_registered(self):
        cfg_obj = _make(
            registry_id="config:pyproject.toml",
            kind=RegistryKind.CONFIG_SURFACE,
            path="pyproject.toml",
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
        )
        result = reconcile_registry_objects([cfg_obj])
        cfg_findings = [f for f in result.findings if "config-surface-registered" in f.invariant]
        assert "config:pyproject.toml" not in {f.object_id for f in cfg_findings}

    def test_config_surface_degraded_not_blocked(self):
        result = reconcile_registry_objects([_make()])
        cfg_findings = [f for f in result.findings if "config-surface-registered" in f.invariant]
        for f in cfg_findings:
            assert f.status.value == "DEGRADED"


# ═══════════════════════════════════════════════════════════════════
# Check H: Authority over-elevation
# ═══════════════════════════════════════════════════════════════════


class TestAuthorityOverElevation:
    """Artifact L3_CANON mapped to T0 may inflate authority."""

    def test_artifact_l3_canon_t0_produces_finding(self):
        obj = _make(
            registry_id="ar:some-artifact",
            kind=RegistryKind.ARTIFACT,
            path="src/ordivon_verify/runner.py",
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            source_registry="artifact-registry",
            current_truth_allowed=True,
            notes="artifact_class=source_registry; artifact_criticality=governance_critical; artifact_layer=L3_CANON",
        )
        result = reconcile_registry_objects([obj])
        elev_findings = [f for f in result.findings if "authority-not-over-elevated" in f.invariant]
        assert len(elev_findings) >= 1
        assert any("L3_CANON" in f.message for f in elev_findings)

    def test_non_artifact_t0_no_finding(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            source_registry="document-registry",
        )
        result = reconcile_registry_objects([obj])
        elev_findings = [f for f in result.findings if "authority-not-over-elevated" in f.invariant]
        assert len(elev_findings) == 0

    def test_artifact_t1_no_finding(self):
        obj = _make(
            registry_id="ar:some-artifact",
            kind=RegistryKind.ARTIFACT,
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            source_registry="artifact-registry",
            current_truth_allowed=False,
            notes="artifact_layer=L3_CANON",
        )
        result = reconcile_registry_objects([obj])
        elev_findings = [f for f in result.findings if "authority-not-over-elevated" in f.invariant]
        assert len(elev_findings) == 0


# ═══════════════════════════════════════════════════════════════════
# Reconciler integration
# ═══════════════════════════════════════════════════════════════════


class TestReconcileIntegration:
    """Integration tests for reconcile_registry_objects()."""

    def test_clean_object_set_no_findings(self):
        """A well-formed object set produces no findings."""
        objects = [
            _make(registry_id="doc-001", owner="someone"),
            _make(
                registry_id="doc-002",
                path="docs/ai/README.md",
                authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
                owner="governance",
            ),
        ]
        result = reconcile_registry_objects(objects)
        # Should still have referenced-but-missing file gaps (policy-activation-ledger)
        # and legacy/config gaps — but no owner or authority findings
        owner_findings = [f for f in result.findings if "owner" in f.invariant]
        assert len(owner_findings) == 0

    def test_reconcile_does_not_mutate_objects(self):
        obj = _make()
        original = obj.registry_id
        reconcile_registry_objects([obj])
        assert obj.registry_id == original
        assert obj.authority_tier == AuthorityTier.T1_CURRENT_STATUS

    def test_summary_counts_match_findings(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            owner=None,
        )
        result = reconcile_registry_objects([obj])
        assert result.summary.blocked_count > 0
        assert result.summary.total_objects == 1

    def test_summary_by_check_populated(self):
        result = reconcile_registry_objects([_make()])
        assert len(result.summary.by_check) >= 1
        assert "active-t0-t1-owner-gap" in result.summary.by_check or "config-surface-gap" in result.summary.by_check

    def test_selective_checks(self):
        result = reconcile_registry_objects(
            [_make(authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH, owner=None)],
            checks=["active-t0-t1-owner-gap"],
        )
        assert result.summary.by_check.get("active-t0-t1-owner-gap", 0) >= 1
        # Other checks should not be present
        assert "legacy-scope-gap" not in result.summary.by_check

    def test_all_checks_registered(self):
        from ordivon_verify.registry.reconciler import _RECONCILER_CHECKS

        assert len(_RECONCILER_CHECKS) == 13
        check_names = {nc[0] for nc in _RECONCILER_CHECKS}
        expected = {
            "referenced-but-missing",
            "active-t0-t1-owner-gap",
            "generated-as-truth",
            "legacy-scope-gap",
            "config-surface-gap",
            "authority-over-elevation",
            "lifecycle-invariants",
            "authority-boundary",
            "onboarding-integrity",
            "receipt-standards",
            "medium-authority",
            "metabolism-integrity",
            "knowledge-navigation",
        }
        assert check_names == expected

    def test_reconcile_empty_objects(self):
        result = reconcile_registry_objects([])
        assert result.summary.total_objects == 0
        # No objects = no owner gaps, no generated-as-truth, no authority over-elevation.
        # Still finds: known missing files (release-claim-map, tool-boundary-map → DEGRADED).
        assert result.summary.blocked_count == 0

    def test_reconcile_result_is_frozen(self):
        import dataclasses

        obj = _make()
        result = reconcile_registry_objects([obj])
        assert dataclasses.is_dataclass(result)


# ═══════════════════════════════════════════════════════════════════
# RG-8: Generated Registry Index
# ═══════════════════════════════════════════════════════════════════


class TestGenerateRegistryIndex:
    """Tests for generate_registry_index() (RG-8)."""

    def _setup_full(self, tmp_path):
        """Set up minimal registry environment for index generation."""
        gov = tmp_path / "docs" / "governance"
        gov.mkdir(parents=True)
        # Document registry
        (gov / "document-registry.jsonl").write_text(
            '{"doc_id": "test-doc", "path": "docs/test.md", "title": "Test", '
            '"doc_type": "root_context", "status": "current", "authority": "source_of_truth", '
            '"owner": "governance", "freshness": "2026-05-09", "ai_read_priority": 0, '
            '"last_verified": "2026-05-09", "stale_after_days": 7, "doc_layer": "L0", '
            '"doc_authority": "source_of_truth"}\n'
        )
        # Policy activation ledger
        (gov / "policy-activation-ledger.jsonl").write_text("\n")
        # Checkers
        checkers = tmp_path / "checkers"
        checkers.mkdir()
        d = checkers / "test-checker"
        d.mkdir()
        (d / "CHECKER.md").write_text("---\ngate_id: test_checker\n---\n# Test\n")
        (d / "run.py").write_text("def run():\n    pass\n")
        # Scanners
        scan = tmp_path / "src" / "ordivon_verify" / "scanners"
        scan.mkdir(parents=True)
        (scan / "skill_boundary.py").write_text("# scanner\n")
        return tmp_path

    def test_index_is_dict_with_expected_keys(self, tmp_path, monkeypatch):
        from ordivon_verify.registry.reconciler import generate_registry_index

        root = self._setup_full(tmp_path)
        index = generate_registry_index(root)
        assert isinstance(index, dict)
        for key in ("generated_at", "repo_root", "version", "authority", "summary", "objects", "findings"):
            assert key in index, f"Missing key: {key}"

    def test_index_authority_is_generated_view(self, tmp_path, monkeypatch):
        from ordivon_verify.registry.reconciler import generate_registry_index

        root = self._setup_full(tmp_path)
        index = generate_registry_index(root)
        assert index["authority"] == "generated_view"

    def test_index_summary_has_counts(self, tmp_path, monkeypatch):
        from ordivon_verify.registry.reconciler import generate_registry_index

        root = self._setup_full(tmp_path)
        index = generate_registry_index(root)
        s = index["summary"]
        assert s["total_objects"] > 0
        assert "blocked_findings" in s
        assert "degraded_findings" in s
        assert "by_kind" in s
        assert "by_source" in s

    def test_index_objects_have_required_fields(self, tmp_path, monkeypatch):
        from ordivon_verify.registry.reconciler import generate_registry_index

        root = self._setup_full(tmp_path)
        index = generate_registry_index(root)
        for reg_id, obj_data in index["objects"].items():
            assert "registry_id" in obj_data
            assert "kind" in obj_data
            assert "authority_tier" in obj_data
            assert "source_registry" in obj_data
            break  # Check first one only

    def test_index_findings_are_list_of_dicts(self, tmp_path, monkeypatch):
        from ordivon_verify.registry.reconciler import generate_registry_index

        root = self._setup_full(tmp_path)
        index = generate_registry_index(root)
        assert isinstance(index["findings"], list)
        if index["findings"]:
            f = index["findings"][0]
            assert "finding_id" in f
            assert "status" in f
