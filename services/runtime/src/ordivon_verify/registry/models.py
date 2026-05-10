"""Ordivon Registry Control Plane — unified object model.

RegistryObject is the canonical representation for all governed artifacts
across Ordivon's registry ecosystem. It bridges Document Registry, Artifact
Registry, Checker Registry, Scanner surfaces, Auxiliary ledgers, Ownership
rules, Policy activations, and Legacy scope declarations.

DO NOT IMPORT metabolic models — RegistryObject is registry-plane, not metabolic.
The metabolic ArtifactRecord remains separate for CTTS-3M stability.
RG-2 adapters will bridge the two.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# ── Enums ──────────────────────────────────────────────────────────


class RegistryKind(str, Enum):
    """What kind of governed object this is.

    Extends the concept of doc_type + artifact_class + checker identity
    into a unified taxonomy. Every RegistryObject has exactly one kind.
    """

    DOCUMENT = "document"
    ARTIFACT = "artifact"
    CHECKER = "checker"
    SCANNER_SURFACE = "scanner_surface"
    LEDGER = "ledger"
    SCHEMA = "schema"
    CONFIG_SURFACE = "config_surface"
    GENERATED_VIEW = "generated_view"
    OWNERSHIP_RULE = "ownership_rule"
    POLICY_ACTIVATION = "policy_activation"
    LEGACY_SCOPE = "legacy_scope"
    ARCHIVE_SNAPSHOT = "archive_snapshot"
    AI_HANDOFF_PACKET = "ai_handoff_packet"


class AuthorityTier(str, Enum):
    """How authoritative this object is.

    Extends metabolic AuthorityTier with T2 (Supporting Evidence,
    different naming from T2_ACTIVE_RUNTIME_EVIDENCE) and
    T6 (Out of Scope — explicit identity for legacy/inactive surfaces
    that must not be silently ungoverned).
    """

    T0_SOURCE_OF_TRUTH = "T0_SOURCE_OF_TRUTH"
    T1_CURRENT_STATUS = "T1_CURRENT_STATUS"
    T2_SUPPORTING_EVIDENCE = "T2_SUPPORTING_EVIDENCE"
    T3_CANDIDATE_PROPOSAL = "T3_CANDIDATE_PROPOSAL"
    T4_ARCHIVE_HISTORICAL = "T4_ARCHIVE_HISTORICAL"
    T5_DEPRECATED_TOMBSTONED = "T5_DEPRECATED_TOMBSTONED"
    T6_OUT_OF_SCOPE = "T6_OUT_OF_SCOPE"


# Tiers that may carry current_truth_allowed=True by default.
DECISION_AUTHORITY_TIERS = frozenset({
    AuthorityTier.T0_SOURCE_OF_TRUTH,
    AuthorityTier.T1_CURRENT_STATUS,
})


class LifecycleState(str, Enum):
    """Where this object is in its lifecycle.

    Extends metabolic LifecycleState with GENERATED (machine-produced,
    not human-authored), LEGACY_INACTIVE (known inactive pre-Ordivon
    surface), and OUT_OF_SCOPE (explicitly excluded from current scope).
    """

    DRAFT = "draft"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    STABLE = "stable"
    GENERATED = "generated"
    ARCHIVED = "archived"
    LEGACY_INACTIVE = "legacy_inactive"
    DEPRECATED = "deprecated"
    TOMBSTONED = "tombstoned"
    OUT_OF_SCOPE = "out_of_scope"


# Lifecycle states that are considered "present and relevant" for
# checking freshness, ownership, and dependency resolution.
ACTIVE_LIFECYCLE_STATES = frozenset({
    LifecycleState.ACTIVE,
    LifecycleState.STABLE,
    LifecycleState.CANDIDATE,
})

# Lifecycle states where the object needs an explicit tombstone or
# supersession reason.
TERMINAL_LIFECYCLE_STATES = frozenset({
    LifecycleState.TOMBSTONED,
    LifecycleState.DEPRECATED,
    LifecycleState.ARCHIVED,
})


class RegistryFindingStatus(str, Enum):
    """Severity of a registry invariant violation."""

    BLOCKED = "BLOCKED"
    DEGRADED = "DEGRADED"
    READY_WITHOUT_AUTHORIZATION = "READY_WITHOUT_AUTHORIZATION"


# ── RegistryObject ─────────────────────────────────────────────────


@dataclass(frozen=True)
class RegistryObject:
    """Canonical representation of one governed object in Ordivon.

    This is the single model that Document Registry entries, Artifact
    Registry entries, Checker packages, Scanner surfaces, Ledger
    entries, Config files, Legacy scope declarations, and Policy
    activations all map into.

    It is NOT yet the active control plane — old registries remain
    authoritative sources during RG-1.  RG-2 adapters will convert
    old registry rows into RegistryObject instances.
    """

    registry_id: str
    kind: RegistryKind
    path: str | None
    title: str | None

    authority_tier: AuthorityTier
    lifecycle_state: LifecycleState
    current_truth_allowed: bool

    owner: str | None = None
    reviewer: str | None = None
    approver: str | None = None

    source_registry: str | None = None
    discovered_by: str | None = None
    registered_by: str | None = None

    generated: bool = False
    generated_from: tuple[str, ...] = ()

    content_hash: str | None = None
    scope: str | None = None
    project_id: str | None = None

    depends_on: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    superseded_by: str | None = None

    last_verified: str | None = None
    review_date: str | None = None
    ttl_days: int | None = None

    policy_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    receipt_refs: tuple[str, ...] = ()

    notes: str | None = None


# ── RegistryFinding ────────────────────────────────────────────────


@dataclass(frozen=True)
class RegistryFinding:
    """One invariant violation detected on a RegistryObject.

    Produced by invariant validators.  Does NOT mutate the object.
    """

    finding_id: str
    object_id: str
    status: RegistryFindingStatus
    invariant: str
    message: str
    repair_action: str | None = None


# ── Invariant Validators ───────────────────────────────────────────


# Each validator returns a list of RegistryFinding (empty = pass).
# Validators are stateless and side-effect-free.


def invariant_active_t0_requires_owner(obj: RegistryObject) -> list[RegistryFinding]:
    """Active T0/T1 objects must have an owner."""
    if obj.authority_tier not in DECISION_AUTHORITY_TIERS:
        return []
    if obj.lifecycle_state not in ACTIVE_LIFECYCLE_STATES:
        return []
    if obj.owner:
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-OWNER-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.BLOCKED,
            invariant="active-t0-requires-owner",
            message=f"Active {obj.authority_tier.value} object '{obj.registry_id}' has no owner",
            repair_action="Assign an owner to this object.",
        )
    ]


def invariant_generated_not_source_truth(obj: RegistryObject) -> list[RegistryFinding]:
    """Generated objects cannot be T0 source-of-truth without explicit override."""
    if not obj.generated:
        return []
    if obj.authority_tier != AuthorityTier.T0_SOURCE_OF_TRUTH:
        return []
    # Allow if notes explicitly justify why a generated object is T0
    if obj.notes and "generated-as-truth" in obj.notes.lower():
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-GEN-TRUTH-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.BLOCKED,
            invariant="generated-not-source-truth",
            message=f"Generated object '{obj.registry_id}' is {obj.authority_tier.value} — "
            "generated objects should default to T2_SUPPORTING_EVIDENCE or below",
            repair_action="Set authority_tier to T2_SUPPORTING_EVIDENCE or add "
            "'generated-as-truth' justification in notes.",
        )
    ]


def invariant_current_truth_allowed_restricted(obj: RegistryObject) -> list[RegistryFinding]:
    """current_truth_allowed=True only for T0/T1 unless explicit override."""
    if not obj.current_truth_allowed:
        return []
    if obj.authority_tier in DECISION_AUTHORITY_TIERS:
        return []
    # Allow if notes give explicit reason
    if obj.notes and "current-truth-override" in obj.notes.lower():
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-CTH-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.BLOCKED,
            invariant="current-truth-allowed-restricted",
            message=f"Object '{obj.registry_id}' ({obj.authority_tier.value}) "
            "has current_truth_allowed=True — only T0/T1 may have this by default",
            repair_action="Set current_truth_allowed=False or add 'current-truth-override' justification in notes.",
        )
    ]


def invariant_legacy_scope_requires_legacy_lifecycle(obj: RegistryObject) -> list[RegistryFinding]:
    """LEGACY_SCOPE kind must have LEGACY_INACTIVE or OUT_OF_SCOPE lifecycle."""
    if obj.kind != RegistryKind.LEGACY_SCOPE:
        return []
    if obj.lifecycle_state in (LifecycleState.LEGACY_INACTIVE, LifecycleState.OUT_OF_SCOPE):
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-LEGACY-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.BLOCKED,
            invariant="legacy-scope-requires-legacy-lifecycle",
            message=f"LEGACY_SCOPE object '{obj.registry_id}' has lifecycle "
            f"'{obj.lifecycle_state.value}' — must be LEGACY_INACTIVE or OUT_OF_SCOPE",
            repair_action="Set lifecycle_state to LEGACY_INACTIVE or OUT_OF_SCOPE.",
        )
    ]


def invariant_generated_requires_generated_from(obj: RegistryObject) -> list[RegistryFinding]:
    """Generated objects must declare their sources via generated_from."""
    if not obj.generated:
        return []
    if obj.generated_from:
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-GEN-SRC-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.DEGRADED,
            invariant="generated-requires-generated-from",
            message=f"Generated object '{obj.registry_id}' has empty generated_from",
            repair_action="Populate generated_from with source registry IDs.",
        )
    ]


def invariant_tombstone_requires_reason(obj: RegistryObject) -> list[RegistryFinding]:
    """Tombstoned objects must have superseded_by or tombstone reason in notes."""
    if obj.lifecycle_state not in TERMINAL_LIFECYCLE_STATES:
        return []
    if obj.superseded_by:
        return []
    if obj.notes and ("tombstone" in obj.notes.lower() or "superseded" in obj.notes.lower()):
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-TOMB-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.DEGRADED,
            invariant="tombstone-requires-reason",
            message=f"Terminal-lifecycle object '{obj.registry_id}' "
            f"({obj.lifecycle_state.value}) has no superseded_by or tombstone reason",
            repair_action="Set superseded_by or add tombstone reason in notes.",
        )
    ]


def invariant_config_surface_not_current_truth(obj: RegistryObject) -> list[RegistryFinding]:
    """CONFIG_SURFACE objects default to current_truth_allowed=False."""
    if obj.kind != RegistryKind.CONFIG_SURFACE:
        return []
    if not obj.current_truth_allowed:
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-CFG-CTH-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.DEGRADED,
            invariant="config-surface-not-current-truth",
            message=f"CONFIG_SURFACE object '{obj.registry_id}' has current_truth_allowed=True — "
            "config files should not default to current truth",
            repair_action="Set current_truth_allowed=False.",
        )
    ]


def invariant_archive_snapshot_not_current_truth(obj: RegistryObject) -> list[RegistryFinding]:
    """ARCHIVE_SNAPSHOT objects default to current_truth_allowed=False."""
    if obj.kind != RegistryKind.ARCHIVE_SNAPSHOT:
        return []
    if not obj.current_truth_allowed:
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-ARC-CTH-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.DEGRADED,
            invariant="archive-snapshot-not-current-truth",
            message=f"ARCHIVE_SNAPSHOT object '{obj.registry_id}' has current_truth_allowed=True — "
            "archive snapshots should not be current truth",
            repair_action="Set current_truth_allowed=False.",
        )
    ]


def invariant_policy_activation_requires_target(obj: RegistryObject) -> list[RegistryFinding]:
    """POLICY_ACTIVATION objects must reference a candidate_rule or policy target."""
    if obj.kind != RegistryKind.POLICY_ACTIVATION:
        return []
    # A POLICY_ACTIVATION must have either supersedes (pointing to candidate rule)
    # or depends_on (pointing to activated policy)
    if obj.supersedes or obj.depends_on:
        return []
    return [
        RegistryFinding(
            finding_id=f"INV-PA-TGT-{obj.registry_id}",
            object_id=obj.registry_id,
            status=RegistryFindingStatus.BLOCKED,
            invariant="policy-activation-requires-target",
            message=f"POLICY_ACTIVATION object '{obj.registry_id}' has no supersedes or depends_on — "
            "must reference candidate_rule or policy target",
            repair_action="Set supersedes to candidate rule ID or depends_on to policy target.",
        )
    ]


# Canvas registry of all validators
# Each is a (invariant_id, validator_fn) pair.
# Add new invariant validators here — reconciler discovers all of them.
REGISTRY_INVARIANTS: tuple[tuple[str, object], ...] = (
    ("active-t0-requires-owner", invariant_active_t0_requires_owner),
    ("generated-not-source-truth", invariant_generated_not_source_truth),
    ("current-truth-allowed-restricted", invariant_current_truth_allowed_restricted),
    ("legacy-scope-requires-legacy-lifecycle", invariant_legacy_scope_requires_legacy_lifecycle),
    ("generated-requires-generated-from", invariant_generated_requires_generated_from),
    ("tombstone-requires-reason", invariant_tombstone_requires_reason),
    ("config-surface-not-current-truth", invariant_config_surface_not_current_truth),
    ("archive-snapshot-not-current-truth", invariant_archive_snapshot_not_current_truth),
    ("policy-activation-requires-target", invariant_policy_activation_requires_target),
)


def validate_registry_object(obj: RegistryObject) -> list[RegistryFinding]:
    """Run all registered invariant validators against one object.

    Returns findings (empty list = all invariants pass).
    """
    findings: list[RegistryFinding] = []
    for _inv_id, validator in REGISTRY_INVARIANTS:
        findings.extend(validator(obj))
    return findings
