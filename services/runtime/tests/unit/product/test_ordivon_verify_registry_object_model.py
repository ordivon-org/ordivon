"""Unit tests for Ordivon Registry Control Plane — RegistryObject model and invariants.

Tests the unified object model defined in RG-1.
Does NOT import or depend on existing registries (document, artifact, checker, metabolic).
Tests are self-contained with constructed objects.
"""

import json
from pathlib import Path

from ordivon_verify.registry import (
    AuthorityTier,
    LifecycleState,
    RegistryFindingStatus,
    RegistryKind,
    RegistryObject,
    validate_registry_object,
)


# ── Helpers ────────────────────────────────────────────────────────


def _load_schema() -> dict:
    schema_path = (
        Path(__file__).resolve().parents[3] / "src" / "ordivon_verify" / "schemas" / "registry-object.schema.json"
    )
    with open(schema_path) as f:
        return json.load(f)


SCHEMA = _load_schema()


def _validate_against_schema(obj: RegistryObject) -> list[str]:
    """Validate a RegistryObject against the JSON schema (basic structural checks)."""
    import jsonschema

    try:
        # Build a dict from the dataclass fields
        data = {
            "registry_id": obj.registry_id,
            "kind": obj.kind.value,
            "path": obj.path,
            "title": obj.title,
            "authority_tier": obj.authority_tier.value,
            "lifecycle_state": obj.lifecycle_state.value,
            "current_truth_allowed": obj.current_truth_allowed,
            "owner": obj.owner,
            "reviewer": obj.reviewer,
            "approver": obj.approver,
            "source_registry": obj.source_registry,
            "discovered_by": obj.discovered_by,
            "registered_by": obj.registered_by,
            "generated": obj.generated,
            "generated_from": list(obj.generated_from),
            "content_hash": obj.content_hash,
            "scope": obj.scope,
            "project_id": obj.project_id,
            "depends_on": list(obj.depends_on),
            "supersedes": list(obj.supersedes),
            "superseded_by": obj.superseded_by,
            "last_verified": obj.last_verified,
            "review_date": obj.review_date,
            "ttl_days": obj.ttl_days,
            "policy_refs": list(obj.policy_refs),
            "evidence_refs": list(obj.evidence_refs),
            "receipt_refs": list(obj.receipt_refs),
            "notes": obj.notes,
        }
        jsonschema.validate(data, SCHEMA)
        return []
    except jsonschema.ValidationError as e:
        return [str(e)]


# ── Base object factory ────────────────────────────────────────────


def _make(**overrides) -> RegistryObject:
    """Create a minimal valid RegistryObject, with overrides applied."""
    defaults = dict(
        registry_id="test-obj-001",
        kind=RegistryKind.DOCUMENT,
        path="docs/test.md",
        title="Test Document",
        authority_tier=AuthorityTier.T1_CURRENT_STATUS,
        lifecycle_state=LifecycleState.ACTIVE,
        current_truth_allowed=True,
        owner="test-owner",
        generated=False,
    )
    defaults.update(overrides)
    return RegistryObject(**defaults)


# ═══════════════════════════════════════════════════════════════════
# Valid object construction for each kind
# ═══════════════════════════════════════════════════════════════════


class TestValidObjectConstruction:
    """Every RegistryKind must be constructable with a valid configuration."""

    def test_valid_document(self):
        obj = _make(kind=RegistryKind.DOCUMENT)
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_artifact(self):
        obj = _make(
            registry_id="ar-001",
            kind=RegistryKind.ARTIFACT,
            path="src/test.py",
            title="Test Artifact",
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_checker(self):
        obj = _make(
            registry_id="chk-001",
            kind=RegistryKind.CHECKER,
            path="checkers/test/run.py",
            title="Test Checker",
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_scanner_surface(self):
        obj = _make(
            registry_id="scn-001",
            kind=RegistryKind.SCANNER_SURFACE,
            path="~/.hermes/skills/test/SKILL.md",
            title="Test Scanner Surface",
            authority_tier=AuthorityTier.T3_CANDIDATE_PROPOSAL,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_ledger(self):
        obj = _make(
            registry_id="ldg-001",
            kind=RegistryKind.LEDGER,
            path="docs/governance/test.jsonl",
            title="Test Ledger",
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_schema(self):
        obj = _make(
            registry_id="sch-001",
            kind=RegistryKind.SCHEMA,
            path="src/schemas/test.schema.json",
            title="Test Schema",
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_config_surface(self):
        obj = _make(
            registry_id="cfg-001",
            kind=RegistryKind.CONFIG_SURFACE,
            path="pyproject.toml",
            title="Test Config",
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            lifecycle_state=LifecycleState.ACTIVE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_generated_view(self):
        obj = _make(
            registry_id="gv-001",
            kind=RegistryKind.GENERATED_VIEW,
            path="docs/generated.json",
            title="Test Generated View",
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            lifecycle_state=LifecycleState.GENERATED,
            current_truth_allowed=False,
            generated=True,
            generated_from=("sch-001", "ldg-001"),
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_ownership_rule(self):
        obj = _make(
            registry_id="own-001",
            kind=RegistryKind.OWNERSHIP_RULE,
            path=None,
            title="Test Ownership Rule",
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_policy_activation(self):
        obj = _make(
            registry_id="pa-001",
            kind=RegistryKind.POLICY_ACTIVATION,
            path=None,
            title="Test Policy Activation",
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            lifecycle_state=LifecycleState.ACTIVE,
            current_truth_allowed=False,
            supersedes=("cr-001",),
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_policy_activation_depends_on(self):
        obj = _make(
            registry_id="pa-002",
            kind=RegistryKind.POLICY_ACTIVATION,
            path=None,
            title="Test Policy Activation via depends_on",
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            lifecycle_state=LifecycleState.ACTIVE,
            current_truth_allowed=False,
            depends_on=("policy-001",),
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_legacy_scope(self):
        obj = _make(
            registry_id="leg-001",
            kind=RegistryKind.LEGACY_SCOPE,
            path="apps/",
            title="Legacy Apps Directory",
            authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
            lifecycle_state=LifecycleState.LEGACY_INACTIVE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_archive_snapshot(self):
        obj = _make(
            registry_id="arc-001",
            kind=RegistryKind.ARCHIVE_SNAPSHOT,
            path="docs/archive/snapshot.json",
            title="Test Archive Snapshot",
            authority_tier=AuthorityTier.T4_ARCHIVE_HISTORICAL,
            lifecycle_state=LifecycleState.ARCHIVED,
            current_truth_allowed=False,
            notes="Tombstone: historical archive snapshot.",
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_valid_ai_handoff_packet(self):
        obj = _make(
            registry_id="ai-001",
            kind=RegistryKind.AI_HANDOFF_PACKET,
            path="docs/ai/handoff.json",
            title="Test AI Handoff Packet",
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
            generated=True,
            generated_from=("doc-001", "ldg-001"),
        )
        findings = validate_registry_object(obj)
        assert findings == []


# ═══════════════════════════════════════════════════════════════════
# Invariant violations
# ═══════════════════════════════════════════════════════════════════


class TestInvariantActiveT0RequiresOwner:
    """Active T0/T1 objects must have an owner."""

    def test_active_t0_without_owner_blocked(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            owner=None,
        )
        findings = validate_registry_object(obj)
        assert len(findings) == 1
        f = findings[0]
        assert f.status == RegistryFindingStatus.BLOCKED
        assert "owner" in f.message.lower()

    def test_active_t1_without_owner_blocked(self):
        obj = _make(
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            owner=None,
        )
        findings = validate_registry_object(obj)
        assert len(findings) == 1
        assert findings[0].status == RegistryFindingStatus.BLOCKED

    def test_active_t2_without_owner_ok(self):
        obj = _make(
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            owner=None,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_active_t0_with_owner_pass(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            owner="someone",
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_archived_t0_without_owner_not_enforced(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            lifecycle_state=LifecycleState.ARCHIVED,
            owner=None,
            current_truth_allowed=False,
            notes="Tombstone: historical archive.",
        )
        findings = validate_registry_object(obj)
        assert findings == []


class TestInvariantGeneratedNotSourceTruth:
    """Generated objects cannot be T0 source-of-truth without override."""

    def test_generated_t0_blocked(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            lifecycle_state=LifecycleState.GENERATED,
            generated=True,
            generated_from=("src-001",),
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert len(findings) == 1
        assert findings[0].status == RegistryFindingStatus.BLOCKED

    def test_generated_t0_with_override_notes_pass(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            lifecycle_state=LifecycleState.GENERATED,
            generated=True,
            generated_from=("src-001",),
            current_truth_allowed=False,
            notes="This is generated-as-truth because it is the single compiled source from multiple registries.",
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_generated_t2_pass(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            lifecycle_state=LifecycleState.GENERATED,
            generated=True,
            generated_from=("src-001",),
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_not_generated_t0_pass(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            generated=False,
        )
        findings = validate_registry_object(obj)
        assert findings == []


class TestInvariantCurrentTruthAllowedRestricted:
    """current_truth_allowed=True only for T0/T1 unless override."""

    def test_t2_current_truth_blocked(self):
        obj = _make(
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=True,
        )
        findings = validate_registry_object(obj)
        assert any("current-truth-allowed" in f.invariant for f in findings)

    def test_t3_current_truth_blocked(self):
        obj = _make(
            authority_tier=AuthorityTier.T3_CANDIDATE_PROPOSAL,
            current_truth_allowed=True,
        )
        findings = validate_registry_object(obj)
        assert any("current-truth-allowed" in f.invariant for f in findings)

    def test_t0_current_truth_pass(self):
        obj = _make(
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            current_truth_allowed=True,
        )
        findings = validate_registry_object(obj)
        assert not any("current-truth-allowed" in f.invariant for f in findings)

    def test_t1_current_truth_pass(self):
        obj = _make(
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            current_truth_allowed=True,
        )
        findings = validate_registry_object(obj)
        assert not any("current-truth-allowed" in f.invariant for f in findings)

    def test_t2_current_truth_with_override_notes_pass(self):
        obj = _make(
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=True,
            notes="current-truth-override: this evidence is authoritative for its domain.",
        )
        findings = validate_registry_object(obj)
        assert not any("current-truth-allowed" in f.invariant for f in findings)

    def test_t2_current_truth_false_pass(self):
        obj = _make(
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert not any("current-truth-allowed" in f.invariant for f in findings)


class TestInvariantLegacyScopeRequiresLegacyLifecycle:
    """LEGACY_SCOPE kind must have LEGACY_INACTIVE or OUT_OF_SCOPE lifecycle."""

    def test_legacy_active_blocked(self):
        obj = _make(
            kind=RegistryKind.LEGACY_SCOPE,
            authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
            lifecycle_state=LifecycleState.ACTIVE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert any("legacy-scope" in f.invariant for f in findings)

    def test_legacy_inactive_pass(self):
        obj = _make(
            kind=RegistryKind.LEGACY_SCOPE,
            authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
            lifecycle_state=LifecycleState.LEGACY_INACTIVE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert not any("legacy-scope" in f.invariant for f in findings)

    def test_legacy_out_of_scope_pass(self):
        obj = _make(
            kind=RegistryKind.LEGACY_SCOPE,
            authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
            lifecycle_state=LifecycleState.OUT_OF_SCOPE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert not any("legacy-scope" in f.invariant for f in findings)

    def test_non_legacy_active_pass(self):
        obj = _make(
            kind=RegistryKind.DOCUMENT,
            lifecycle_state=LifecycleState.ACTIVE,
        )
        findings = validate_registry_object(obj)
        assert not any("legacy-scope" in f.invariant for f in findings)


class TestInvariantGeneratedRequiresGeneratedFrom:
    """Generated objects must declare generated_from."""

    def test_generated_empty_sources_degraded(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            lifecycle_state=LifecycleState.GENERATED,
            current_truth_allowed=False,
            generated=True,
            generated_from=(),
        )
        findings = validate_registry_object(obj)
        assert any("generated-requires" in f.invariant for f in findings)

    def test_generated_with_sources_pass(self):
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            lifecycle_state=LifecycleState.GENERATED,
            current_truth_allowed=False,
            generated=True,
            generated_from=("a", "b"),
        )
        findings = validate_registry_object(obj)
        assert not any("generated-requires" in f.invariant for f in findings)

    def test_not_generated_empty_sources_pass(self):
        obj = _make(
            kind=RegistryKind.DOCUMENT,
            generated=False,
            generated_from=(),
        )
        findings = validate_registry_object(obj)
        assert not any("generated-requires" in f.invariant for f in findings)


class TestInvariantTombstoneRequiresReason:
    """Tombstoned/deprecated/archived objects need reason."""

    def test_tombstoned_no_reason_degraded(self):
        obj = _make(
            lifecycle_state=LifecycleState.TOMBSTONED,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert any("tombstone-requires" in f.invariant for f in findings)

    def test_tombstoned_with_superseded_by_pass(self):
        obj = _make(
            lifecycle_state=LifecycleState.TOMBSTONED,
            superseded_by="newer-obj",
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert not any("tombstone-requires" in f.invariant for f in findings)

    def test_tombstoned_with_notes_pass(self):
        obj = _make(
            lifecycle_state=LifecycleState.TOMBSTONED,
            current_truth_allowed=False,
            notes="Tombstoned: replaced by registry-v2.",
        )
        findings = validate_registry_object(obj)
        assert not any("tombstone-requires" in f.invariant for f in findings)

    def test_deprecated_no_reason_degraded(self):
        obj = _make(
            lifecycle_state=LifecycleState.DEPRECATED,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert any("tombstone-requires" in f.invariant for f in findings)

    def test_active_no_tombstone_pass(self):
        obj = _make(lifecycle_state=LifecycleState.ACTIVE)
        findings = validate_registry_object(obj)
        assert not any("tombstone-requires" in f.invariant for f in findings)


class TestInvariantConfigSurfaceNotCurrentTruth:
    """CONFIG_SURFACE objects default to current_truth_allowed=False."""

    def test_config_with_current_truth_degraded(self):
        obj = _make(
            kind=RegistryKind.CONFIG_SURFACE,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=True,
        )
        findings = validate_registry_object(obj)
        assert any("config-surface" in f.invariant for f in findings)

    def test_config_without_current_truth_pass(self):
        obj = _make(
            kind=RegistryKind.CONFIG_SURFACE,
            authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert not any("config-surface" in f.invariant for f in findings)

    def test_document_with_current_truth_not_affected(self):
        obj = _make(kind=RegistryKind.DOCUMENT)
        findings = validate_registry_object(obj)
        assert not any("config-surface" in f.invariant for f in findings)


class TestInvariantArchiveSnapshotNotCurrentTruth:
    """ARCHIVE_SNAPSHOT objects default to current_truth_allowed=False."""

    def test_archive_with_current_truth_degraded(self):
        obj = _make(
            kind=RegistryKind.ARCHIVE_SNAPSHOT,
            authority_tier=AuthorityTier.T4_ARCHIVE_HISTORICAL,
            lifecycle_state=LifecycleState.ARCHIVED,
            current_truth_allowed=True,
        )
        findings = validate_registry_object(obj)
        assert any("archive-snapshot" in f.invariant for f in findings)

    def test_archive_without_current_truth_pass(self):
        obj = _make(
            kind=RegistryKind.ARCHIVE_SNAPSHOT,
            authority_tier=AuthorityTier.T4_ARCHIVE_HISTORICAL,
            lifecycle_state=LifecycleState.ARCHIVED,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert not any("archive-snapshot" in f.invariant for f in findings)


class TestInvariantPolicyActivationRequiresTarget:
    """POLICY_ACTIVATION must reference candidate_rule or policy target."""

    def test_policy_activation_no_target_blocked(self):
        obj = _make(
            kind=RegistryKind.POLICY_ACTIVATION,
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            current_truth_allowed=False,
        )
        findings = validate_registry_object(obj)
        assert any("policy-activation" in f.invariant for f in findings)

    def test_policy_activation_with_supersedes_pass(self):
        obj = _make(
            kind=RegistryKind.POLICY_ACTIVATION,
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            current_truth_allowed=False,
            supersedes=("cr-001",),
        )
        findings = validate_registry_object(obj)
        assert not any("policy-activation" in f.invariant for f in findings)

    def test_policy_activation_with_depends_on_pass(self):
        obj = _make(
            kind=RegistryKind.POLICY_ACTIVATION,
            authority_tier=AuthorityTier.T1_CURRENT_STATUS,
            current_truth_allowed=False,
            depends_on=("policy-target",),
        )
        findings = validate_registry_object(obj)
        assert not any("policy-activation" in f.invariant for f in findings)

    def test_document_activation_not_checked(self):
        obj = _make(kind=RegistryKind.DOCUMENT)
        findings = validate_registry_object(obj)
        assert not any("policy-activation" in f.invariant for f in findings)


# ═══════════════════════════════════════════════════════════════════
# JSON Schema validation
# ═══════════════════════════════════════════════════════════════════


class TestJsonSchema:
    """RegistryObject instances validate against the JSON schema."""

    def test_document_validates_against_schema(self):
        obj = _make()
        errors = _validate_against_schema(obj)
        assert errors == [], f"Schema errors: {errors}"

    def test_all_kinds_valid_in_schema(self):
        for kind in RegistryKind:
            if kind == RegistryKind.LEGACY_SCOPE:
                obj = _make(
                    registry_id=f"test-{kind.value}",
                    kind=kind,
                    authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
                    lifecycle_state=LifecycleState.LEGACY_INACTIVE,
                    current_truth_allowed=False,
                )
            elif kind == RegistryKind.GENERATED_VIEW:
                obj = _make(
                    registry_id=f"test-{kind.value}",
                    kind=kind,
                    authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
                    lifecycle_state=LifecycleState.GENERATED,
                    current_truth_allowed=False,
                    generated=True,
                    generated_from=("src",),
                )
            elif kind == RegistryKind.POLICY_ACTIVATION:
                obj = _make(
                    registry_id=f"test-{kind.value}",
                    kind=kind,
                    authority_tier=AuthorityTier.T1_CURRENT_STATUS,
                    current_truth_allowed=False,
                    supersedes=("cr-001",),
                )
            elif kind == RegistryKind.ARCHIVE_SNAPSHOT:
                obj = _make(
                    registry_id=f"test-{kind.value}",
                    kind=kind,
                    authority_tier=AuthorityTier.T4_ARCHIVE_HISTORICAL,
                    lifecycle_state=LifecycleState.ARCHIVED,
                    current_truth_allowed=False,
                )
            elif kind == RegistryKind.OWNERSHIP_RULE:
                obj = _make(
                    registry_id=f"test-{kind.value}",
                    kind=kind,
                    path=None,
                    current_truth_allowed=False,
                )
            else:
                obj = _make(
                    registry_id=f"test-{kind.value}",
                    kind=kind,
                    current_truth_allowed=False,
                )
            errors = _validate_against_schema(obj)
            assert errors == [], f"Schema errors for {kind.value}: {errors}"

    def test_all_authority_tiers_in_schema(self):
        for tier in AuthorityTier:
            obj = _make(
                registry_id=f"test-{tier.value}",
                authority_tier=tier,
                current_truth_allowed=(tier in (AuthorityTier.T0_SOURCE_OF_TRUTH, AuthorityTier.T1_CURRENT_STATUS)),
            )
            errors = _validate_against_schema(obj)
            assert errors == [], f"Schema errors for {tier.value}: {errors}"

    def test_all_lifecycle_states_in_schema(self):
        for state in LifecycleState:
            obj = _make(
                registry_id=f"test-{state.value}",
                lifecycle_state=state,
                current_truth_allowed=False,
            )
            errors = _validate_against_schema(obj)
            assert errors == [], f"Schema errors for {state.value}: {errors}"


# ═══════════════════════════════════════════════════════════════════
# Edge cases and robustness
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Objects at the boundaries of the model behavior."""

    def test_pathless_object(self):
        obj = _make(path=None, owner="someone")
        findings = validate_registry_object(obj)
        assert findings == []

    def test_object_with_all_optional_fields_null(self):
        obj = RegistryObject(
            registry_id="minimal",
            kind=RegistryKind.LEGACY_SCOPE,
            path=None,
            title=None,
            authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
            lifecycle_state=LifecycleState.LEGACY_INACTIVE,
            current_truth_allowed=False,
            owner=None,
            reviewer=None,
            approver=None,
            source_registry=None,
            discovered_by=None,
            registered_by=None,
            generated=False,
            generated_from=(),
            content_hash=None,
            scope=None,
            project_id=None,
            depends_on=(),
            supersedes=(),
            superseded_by=None,
            last_verified=None,
            review_date=None,
            ttl_days=None,
            policy_refs=(),
            evidence_refs=(),
            receipt_refs=(),
            notes=None,
        )
        findings = validate_registry_object(obj)
        assert findings == []

    def test_multiple_invariants_on_one_object(self):
        """An object can violate multiple invariants simultaneously.

        This object violates: active-t0-requires-owner (ACTIVE+T0, no owner),
        generated-not-source-truth (generated+T0), generated-requires-generated-from
        (generated, empty sources). current-truth-allowed-restricted does NOT fire
        because T0 is a decision authority tier.
        Tombstone-requires-reason does NOT fire because GENERATED lifecycle is not
        in TERMINAL_LIFECYCLE_STATES.
        """
        obj = _make(
            kind=RegistryKind.GENERATED_VIEW,
            authority_tier=AuthorityTier.T0_SOURCE_OF_TRUTH,
            lifecycle_state=LifecycleState.ACTIVE,
            current_truth_allowed=True,
            owner=None,
            generated=True,
            generated_from=(),
        )
        findings = validate_registry_object(obj)
        # Should trigger: active-t0-requires-owner, generated-not-source-truth,
        # generated-requires-generated-from (3 invariants)
        assert len(findings) == 3
        invariant_ids = {f.invariant for f in findings}
        assert "active-t0-requires-owner" in invariant_ids
        assert "generated-not-source-truth" in invariant_ids
        assert "generated-requires-generated-from" in invariant_ids
        # These should NOT fire:
        assert "current-truth-allowed-restricted" not in invariant_ids
        assert "tombstone-requires-reason" not in invariant_ids

    def test_validate_empty_objects_returns_empty(self):
        findings = validate_registry_object(_make())
        assert findings == []

    def test_registry_invariants_tuple_is_nonempty(self):
        from ordivon_verify.registry import REGISTRY_INVARIANTS

        assert len(REGISTRY_INVARIANTS) >= 9
