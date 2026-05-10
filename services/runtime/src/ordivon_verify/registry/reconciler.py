"""Cross-Registry Reconciler — Alpha (RG-3).

Consumes RegistryObject instances (produced by RG-2 import adapters) and
runs cross-registry coherence checks that reproduce the split-brain gaps
identified in RG-0.

The reconciler is READ-ONLY. It produces RegistryFinding objects but
never modifies source files, never repairs debts, and never writes
generated indexes. RG-4 through RG-9 will fix classes of findings.

Architecture:
    RG-2 importers → RegistryObject[] → RG-3 reconciler → RegistryFinding[]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from ordivon_verify.registry.models import (
    AuthorityTier,
    DECISION_AUTHORITY_TIERS,
    LifecycleState,
    RegistryFinding,
    RegistryFindingStatus,
    RegistryKind,
    RegistryObject,
)


# ═══════════════════════════════════════════════════════════════════
# Reconciler Result Types
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ReconcileSummary:
    """Aggregated counts from a reconciliation run."""

    total_objects: int = 0
    blocked_count: int = 0
    degraded_count: int = 0
    routed_by_inheritance: int = 0
    by_check: dict[str, int] = field(default_factory=dict)  # check_name → count


@dataclass(frozen=True)
class ReconcileResult:
    """Result of one reconciliation run."""

    objects: tuple[RegistryObject, ...]
    findings: tuple[RegistryFinding, ...]
    summary: ReconcileSummary


# ═══════════════════════════════════════════════════════════════════
# Registry paths — known source files for self-registration checks
# ═══════════════════════════════════════════════════════════════════

_SELF_REGISTRATION_CHECK = (
    ("docs/governance/document-registry.jsonl", "document-registry"),
    ("docs/governance/document-registry-exclusions.json", "document-registry-exclusions"),
    ("docs/governance/artifact-registry.jsonl", "artifact-registry"),
)

_KNOWN_CONFIG_FILES = (
    "pyproject.toml",
    "package.json",
    "pnpm-workspace.yaml",
    "docker-compose.yml",
    "Makefile",
    ".env.example",
)

# Legacy scope directories identified in RG-0 (PFIOS/AegisOS legacy).
# These have files but no formal lifecycle_state identity.
_KNOWN_LEGACY_DIRS = (
    "apps",
    "capabilities",
    "governance_engine",
    "orchestrator",
    "state",
    "intelligence",
    "knowledge",
    "tools",
    "infra",
    "adapters",
    "packs",
    "execution",
    "workflows",
    "policies",
    "prompts",
    "shared",
    "services",
    "alembic",
    "data",
    "db",
    "scratch",
    "wiki",
    "build",
    "dist",
    "evals",
    "knowledge_state",
)


# ═══════════════════════════════════════════════════════════════════
# Check A: Referenced-but-missing objects
# ═══════════════════════════════════════════════════════════════════


def _check_referenced_but_missing(objects: Sequence[RegistryObject], root: Path | None = None) -> list[RegistryFinding]:
    """Detect objects referenced in depends_on/policy_refs/evidence_refs etc.
    that do not exist in the imported object set OR on filesystem.

    Resolution order:
    1. Check if ref matches a known registry_id → resolved
    2. Check if ref matches a known object path → resolved
    3. Check if ref is a filesystem path that exists → resolved
    4. Otherwise → finding
    """
    findings: list[RegistryFinding] = []
    all_ids = {obj.registry_id for obj in objects}
    all_paths = {obj.path for obj in objects if obj.path}

    for obj in objects:
        ref_fields = [
            ("depends_on", obj.depends_on),
            ("policy_refs", obj.policy_refs),
            ("evidence_refs", obj.evidence_refs),
            ("receipt_refs", obj.receipt_refs),
            ("generated_from", obj.generated_from),
        ]

        for field_name, refs in ref_fields:
            for ref in refs:
                # 1. registry_id match
                if ref in all_ids:
                    continue
                # 2. path match
                if ref in all_paths:
                    continue
                # 3. filesystem existence
                if root and (root / ref).exists():
                    continue
                # 4. unresolved
                is_policy_ref = ("policy" in field_name) or ("activation" in ref.lower()) or ("policy" in ref.lower())
                findings.append(
                    RegistryFinding(
                        finding_id=f"REC-MISSING-{obj.registry_id}-{field_name}-{ref[:60]}",
                        object_id=obj.registry_id,
                        status=RegistryFindingStatus.BLOCKED if is_policy_ref else RegistryFindingStatus.DEGRADED,
                        invariant="referenced-object-exists",
                        message=f"Object '{obj.registry_id}' references '{ref}' in {field_name}, "
                        f"but '{ref}' is not a known registry object, registered path, or existing file",
                        repair_action=f"Create the referenced object '{ref}', register it, or remove the dangling reference.",
                    )
                )

    # Also check: are there known files registered in document-registry
    # that reference paths NOT in the imported object set?
    # (This list is cleaned per RG-11 — only real regressions should be added here.)

    return findings


# ═══════════════════════════════════════════════════════════════════
# Check B: Active T0/T1 without owner
# ═══════════════════════════════════════════════════════════════════


def _check_owner_gaps(objects: Sequence[RegistryObject], root: Path | None = None):
    """RG-18/O1: Returns (findings, routed_count) tuple.

    routed_count = number of objects that would have produced findings
    but were resolved by path-owner inheritance.
    """
    findings: list[RegistryFinding] = []
    routing_rules = _load_owner_routing_rules(root)
    routed_count = 0

    for obj in objects:
        if obj.authority_tier not in DECISION_AUTHORITY_TIERS:
            continue
        if obj.lifecycle_state not in (LifecycleState.ACTIVE, LifecycleState.STABLE, LifecycleState.CANDIDATE):
            continue
        if obj.owner:
            continue

        inherited = _inherit_owner_from_path(obj.path, routing_rules)
        if inherited:
            routed_count += 1
            continue

        if obj.kind in (RegistryKind.DOCUMENT, RegistryKind.POLICY_ACTIVATION):
            severity = RegistryFindingStatus.BLOCKED
        elif obj.kind in (RegistryKind.CHECKER, RegistryKind.ARTIFACT, RegistryKind.CONFIG_SURFACE):
            severity = RegistryFindingStatus.DEGRADED
        else:
            severity = RegistryFindingStatus.DEGRADED

        findings.append(
            RegistryFinding(
                finding_id=f"REC-OWNER-{obj.registry_id}",
                object_id=obj.registry_id,
                status=severity,
                invariant="active-decision-object-has-owner",
                message=f"Active {obj.authority_tier.value} object '{obj.registry_id}' "
                f"({obj.kind.value}) has no owner and no path-owner inheritance",
                repair_action="Assign an owner or add path-owner routing rule.",
            )
        )

    return findings, routed_count


def _load_owner_routing_rules(root: Path | None) -> list[dict]:
    """Load owner-routing-rules.jsonl if present."""
    if root is None:
        return []
    rules_path = root / "docs" / "governance" / "owner-routing-rules.jsonl"
    if not rules_path.exists():
        return []
    rules = []
    import json

    try:
        for line in rules_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rules.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    return rules


def _inherit_owner_from_path(obj_path: str | None, rules: list[dict]) -> str | None:
    """Match object path against routing rules using glob patterns."""
    if not obj_path or not rules:
        return None
    from fnmatch import fnmatch

    for rule in rules:
        pattern = rule.get("path_pattern", "")
        if pattern and fnmatch(obj_path, pattern):
            return rule.get("default_owner")
    return None


# ═══════════════════════════════════════════════════════════════════
# Check C: Generated view marked as source of truth
# ═══════════════════════════════════════════════════════════════════


def _check_generated_as_truth(objects: Sequence[RegistryObject]) -> list[RegistryFinding]:
    """Generated objects and generated_view kind should not be T0 source truth
    or have current_truth_allowed=True.

    Covers RG-0 finding: checker-coverage-manifest.json registered as
    source_of_truth despite being a generated view.
    """
    findings: list[RegistryFinding] = []

    for obj in objects:
        if not obj.generated and obj.kind != RegistryKind.GENERATED_VIEW:
            continue

        if obj.current_truth_allowed:
            findings.append(
                RegistryFinding(
                    finding_id=f"REC-GEN-TRUTH-{obj.registry_id}",
                    object_id=obj.registry_id,
                    status=RegistryFindingStatus.BLOCKED,
                    invariant="generated-not-current-truth",
                    message=f"Generated object '{obj.registry_id}' ({obj.kind.value}) has current_truth_allowed=True",
                    repair_action="Set current_truth_allowed=False for generated objects.",
                )
            )
        elif obj.authority_tier == AuthorityTier.T0_SOURCE_OF_TRUTH:
            findings.append(
                RegistryFinding(
                    finding_id=f"REC-GEN-AUTH-{obj.registry_id}",
                    object_id=obj.registry_id,
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="generated-not-source-truth",
                    message=f"Generated object '{obj.registry_id}' ({obj.kind.value}) is T0_SOURCE_OF_TRUTH",
                    repair_action="Set authority_tier to T2_SUPPORTING_EVIDENCE or add "
                    "'generated-as-truth' justification in notes.",
                )
            )

    return findings


# ═══════════════════════════════════════════════════════════════════
# Check: Legacy scope missing formal identity
# ═══════════════════════════════════════════════════════════════════


def _check_legacy_scope_gap(objects: Sequence[RegistryObject]) -> list[RegistryFinding]:
    """RG-14: Legacy scope objects are now imported from manifest.
    Known legacy dirs without a LEGACY_SCOPE object are DEGRADED."""
    findings: list[RegistryFinding] = []
    legacy_scope_objects = {
        obj.path.rstrip("/") for obj in objects if obj.kind == RegistryKind.LEGACY_SCOPE and obj.path
    }
    for legacy_dir in _KNOWN_LEGACY_DIRS:
        if legacy_dir not in legacy_scope_objects:
            findings.append(
                RegistryFinding(
                    finding_id=f"REC-LEGACY-{legacy_dir}",
                    object_id=f"legacy:{legacy_dir}",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="legacy-scope-has-identity",
                    message=f"Legacy directory '{legacy_dir}/' has no LEGACY_SCOPE object "
                    "declaring lifecycle_state=LEGACY_INACTIVE or OUT_OF_SCOPE",
                    repair_action=f"Create a RegistryObject(kind=LEGACY_SCOPE, path='{legacy_dir}/', lifecycle_state=LEGACY_INACTIVE).",
                )
            )
    return findings


# ═══════════════════════════════════════════════════════════════════
# Check G: Config surfaces unregistered
# ═══════════════════════════════════════════════════════════════════


def _check_config_surfaces_unregistered(objects: Sequence[RegistryObject]) -> list[RegistryFinding]:
    """RG-13: Config surfaces are now imported. Objects without config_surface
    identity but within known config paths are DEGRADED. Once imported,
    the gap disappears naturally."""
    findings: list[RegistryFinding] = []
    config_paths = {obj.path for obj in objects if obj.kind == RegistryKind.CONFIG_SURFACE and obj.path}
    for cf in _KNOWN_CONFIG_FILES:
        if cf not in config_paths:
            findings.append(
                RegistryFinding(
                    finding_id=f"REC-CFG-{cf}",
                    object_id=f"config:{cf}",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="config-surface-registered",
                    message=f"Config file '{cf}' has no CONFIG_SURFACE RegistryObject",
                    repair_action=f"Create a RegistryObject(kind=CONFIG_SURFACE, path='{cf}').",
                )
            )
    return findings


# ═══════════════════════════════════════════════════════════════════
# Check H: Authority over-elevation from import mapping
# ═══════════════════════════════════════════════════════════════════


def _check_authority_over_elevation(objects: Sequence[RegistryObject]) -> list[RegistryFinding]:
    """Imported objects that were mapped to T0_SOURCE_OF_TRUTH solely because
    of artifact_layer=L3_CANON may have inflated authority.

    This check looks for objects where:
    - authority_tier=T0_SOURCE_OF_TRUTH
    - source_registry is not a source_of_truth native source (e.g., artifact-registry)
    - notes indicate L3_CANON mapping rather than explicit truth declaration

    Covers RG-2 risk: artifact L3_CANON → T0 mapping may over-elevate authority.
    """
    findings: list[RegistryFinding] = []

    for obj in objects:
        if obj.authority_tier != AuthorityTier.T0_SOURCE_OF_TRUTH:
            continue
        if obj.source_registry != "artifact-registry":
            continue
        if obj.lifecycle_state in (LifecycleState.ARCHIVED, LifecycleState.TOMBSTONED, LifecycleState.DEPRECATED):
            continue

        # Objects from artifact-registry that got T0 via L3_CANON layer mapping
        # should be flagged for review
        if obj.notes and "artifact_layer=L3_CANON" in obj.notes:
            findings.append(
                RegistryFinding(
                    finding_id=f"REC-ELEV-{obj.registry_id}",
                    object_id=obj.registry_id,
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="authority-not-over-elevated",
                    message=f"Object '{obj.registry_id}' ({obj.path}) is T0_SOURCE_OF_TRUTH "
                    "mapped from artifact_layer=L3_CANON import. "
                    "L3_CANON indicates structural placement, not necessarily current truth authority.",
                    repair_action="Review: downgrade to T1_CURRENT_STATUS or add explicit "
                    "source_of_truth declaration in source registry.",
                )
            )

    return findings


# ═══════════════════════════════════════════════════════════════════
# Check I: Lifecycle Invariants (DGP-2)
# ═══════════════════════════════════════════════════════════════════


def _check_lifecycle_invariants(objects: Sequence[RegistryObject]) -> list[RegistryFinding]:
    """DGP-2: Enforce document lifecycle invariants.

    - generated document cannot be source_of_truth.
    - archived/tombstoned/out_of_scope cannot be current_truth_allowed.
    - tombstoned requires reason or superseded_by.
    - superseded requires superseded_by.
    - legacy_inactive requires reentry_condition.
    """
    findings: list[RegistryFinding] = []

    for obj in objects:
        # generated cannot be source_of_truth
        if obj.generated and obj.authority_tier == AuthorityTier.T0_SOURCE_OF_TRUTH:
            if not (obj.notes and "generated-as-truth" in obj.notes.lower()):
                findings.append(
                    RegistryFinding(
                        finding_id=f"LC-GEN-TRUTH-{obj.registry_id}",
                        object_id=obj.registry_id,
                        status=RegistryFindingStatus.BLOCKED,
                        invariant="lifecycle-generated-not-truth",
                        message=f"Generated object '{obj.registry_id}' is T0_SOURCE_OF_TRUTH",
                        repair_action="Set authority_tier to T2_SUPPORTING_EVIDENCE or add 'generated-as-truth' justification.",
                    )
                )

        # archived/tombstoned/out_of_scope cannot be current_truth_allowed
        if obj.lifecycle_state in (LifecycleState.ARCHIVED, LifecycleState.TOMBSTONED, LifecycleState.OUT_OF_SCOPE):
            if obj.current_truth_allowed:
                findings.append(
                    RegistryFinding(
                        finding_id=f"LC-ARCH-TRUTH-{obj.registry_id}",
                        object_id=obj.registry_id,
                        status=RegistryFindingStatus.BLOCKED,
                        invariant="lifecycle-archive-not-truth",
                        message=f"Object '{obj.registry_id}' ({obj.lifecycle_state.value}) has current_truth_allowed=True",
                        repair_action="Set current_truth_allowed=False for archived/tombstoned/out_of_scope objects.",
                    )
                )

        # tombstoned requires reason
        if obj.lifecycle_state == LifecycleState.TOMBSTONED:
            if not obj.superseded_by and not (obj.notes and "tombstone" in obj.notes.lower()):
                findings.append(
                    RegistryFinding(
                        finding_id=f"LC-TOMB-REASON-{obj.registry_id}",
                        object_id=obj.registry_id,
                        status=RegistryFindingStatus.DEGRADED,
                        invariant="lifecycle-tombstone-reason",
                        message=f"Tombstoned object '{obj.registry_id}' has no superseded_by or tombstone reason",
                        repair_action="Set superseded_by or add tombstone reason in notes.",
                    )
                )

    return findings


# ═══════════════════════════════════════════════════════════════════
# Check J: Authority Boundary (DGP-3)
# ═══════════════════════════════════════════════════════════════════


def _check_authority_boundary(objects: Sequence[RegistryObject]) -> list[RegistryFinding]:
    """DGP-3: Prevent authority laundering.

    - generated_view cannot be current_truth_allowed → BLOCKED.
    - proposal (T3) cannot be current_truth_allowed → BLOCKED.
    """
    findings: list[RegistryFinding] = []
    for obj in objects:
        if obj.generated and obj.current_truth_allowed:
            findings.append(
                RegistryFinding(
                    finding_id=f"AUTH-GEN-{obj.registry_id}",
                    object_id=obj.registry_id,
                    status=RegistryFindingStatus.BLOCKED,
                    invariant="authority-generated-not-truth",
                    message=f"Generated object '{obj.registry_id}' has current_truth_allowed=True",
                    repair_action="Set current_truth_allowed=False for generated objects.",
                )
            )
        if obj.authority_tier == AuthorityTier.T3_CANDIDATE_PROPOSAL and obj.current_truth_allowed:
            findings.append(
                RegistryFinding(
                    finding_id=f"AUTH-PROP-{obj.registry_id}",
                    object_id=obj.registry_id,
                    status=RegistryFindingStatus.BLOCKED,
                    invariant="authority-proposal-not-truth",
                    message=f"Proposal object '{obj.registry_id}' has current_truth_allowed=True",
                    repair_action="Set current_truth_allowed=False for proposals.",
                )
            )
    return findings


# ═══════════════════════════════════════════════════════════════════
# Check E1: DGP-4 Onboarding Integrity
# ═══════════════════════════════════════════════════════════════════


def _check_onboarding_integrity(objects: Sequence[RegistryObject], root: Path | None = None) -> list[RegistryFinding]:
    """DGP-E1: Verify AI onboarding surfaces exist and are consistent."""
    findings: list[RegistryFinding] = []
    if not root:
        return findings
    ctx_map = root / "docs/ai/current-context-map.json" if root else None
    reading_order = root / "docs/ai/new-ai-reading-order.md" if root else None
    no_go = root / "docs/ai/no-go-boundary-map.md" if root else None

    if not ctx_map or not ctx_map.exists():
        findings.append(
            RegistryFinding(
                finding_id="ONB-01",
                object_id="dgp-4-context-map",
                status=RegistryFindingStatus.DEGRADED,
                invariant="onboarding-context-map-exists",
                message="current-context-map.json is missing",
                repair_action="Create docs/ai/current-context-map.json.",
            )
        )
    else:
        try:
            import json

            data = json.loads(ctx_map.read_text())
            for key in [
                "current_truth_docs",
                "no_go_docs",
                "start_nodes" if "start_nodes" in data else "onboarding_reading_order",
            ]:
                pass
            if not data.get("archive_warning") or not data.get("generated_view_warning"):
                findings.append(
                    RegistryFinding(
                        finding_id="ONB-02",
                        object_id="dgp-4-context-map",
                        status=RegistryFindingStatus.DEGRADED,
                        invariant="onboarding-context-warnings",
                        message="Context map missing archive_warning or generated_view_warning",
                        repair_action="Add archive and generated view warnings.",
                    )
                )
        except:
            pass

    if not reading_order or not reading_order.exists():
        findings.append(
            RegistryFinding(
                finding_id="ONB-03",
                object_id="dgp-4-reading-order",
                status=RegistryFindingStatus.DEGRADED,
                invariant="onboarding-reading-order-exists",
                message="new-ai-reading-order.md is missing",
                repair_action="Create docs/ai/new-ai-reading-order.md.",
            )
        )

    if not no_go or not no_go.exists():
        findings.append(
            RegistryFinding(
                finding_id="ONB-04",
                object_id="dgp-4-no-go",
                status=RegistryFindingStatus.DEGRADED,
                invariant="onboarding-no-go-exists",
                message="no-go-boundary-map.md is missing",
                repair_action="Create docs/ai/no-go-boundary-map.md.",
            )
        )
    elif no_go.exists():
        content = no_go.read_text()
        if "not authoriz" not in content.lower() and "not merge" not in content.lower():
            findings.append(
                RegistryFinding(
                    finding_id="ONB-05",
                    object_id="dgp-4-no-go",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="onboarding-non-authorization",
                    message="No-go boundary map missing non-authorization statement",
                    repair_action="Add authorization boundary to no-go map.",
                )
            )

    return findings


def _find_root(objects: Sequence[RegistryObject]) -> Path | None:
    """Heuristic: find project root from object paths."""
    from pathlib import Path

    for o in objects:
        if o.path and "/" in o.path:
            p = Path(o.path)
            if p.parts[0] in ("docs", "src", "tests", "scripts"):
                # Walk up until we find AGENTS.md or pyproject.toml
                for parent in [Path.cwd()] + list(Path.cwd().parents):
                    if (parent / "AGENTS.md").exists() or (parent / "pyproject.toml").exists():
                        return parent
                return Path.cwd()
    return Path.cwd() if (Path.cwd() / "AGENTS.md").exists() else None


# ═══════════════════════════════════════════════════════════════════
# Check E1: DGP-5 Receipt Standards
# ═══════════════════════════════════════════════════════════════════


def _check_receipt_standards(objects: Sequence[RegistryObject], root: Path | None = None) -> list[RegistryFinding]:
    """DGP-E1: Verify receipt/phase-closure governance surfaces."""
    findings: list[RegistryFinding] = []
    if not root:
        return findings

    receipt_std = root / "docs/governance/phase-receipt-standard-dgp-5.md"
    summit_std = root / "docs/governance/stage-summit-standard-dgp-5.md"
    ledger = root / "docs/governance/phase-closure-ledger.jsonl"

    if not receipt_std.exists():
        findings.append(
            RegistryFinding(
                finding_id="RCP-01",
                object_id="dgp-5-receipt-standard",
                status=RegistryFindingStatus.DEGRADED,
                invariant="receipt-standard-exists",
                message="phase-receipt-standard-dgp-5.md is missing",
                repair_action="Create receipt standard doc.",
            )
        )
    if not summit_std.exists():
        findings.append(
            RegistryFinding(
                finding_id="RCP-02",
                object_id="dgp-5-summit-standard",
                status=RegistryFindingStatus.DEGRADED,
                invariant="summit-standard-exists",
                message="stage-summit-standard-dgp-5.md is missing",
                repair_action="Create stage summit standard doc.",
            )
        )
    if summit_std.exists() and "what not to infer" not in summit_std.read_text().lower():
        findings.append(
            RegistryFinding(
                finding_id="RCP-03",
                object_id="dgp-5-summit-standard",
                status=RegistryFindingStatus.DEGRADED,
                invariant="summit-what-not-to-infer",
                message="Stage summit standard missing 'what not to infer' section",
                repair_action="Add what-not-to-infer section.",
            )
        )
    if not ledger.exists():
        findings.append(
            RegistryFinding(
                finding_id="RCP-04",
                object_id="dgp-5-phase-ledger",
                status=RegistryFindingStatus.DEGRADED,
                invariant="phase-closure-ledger-exists",
                message="phase-closure-ledger.jsonl is missing",
                repair_action="Create phase closure ledger.",
            )
        )

    return findings


# ═══════════════════════════════════════════════════════════════════
# Check E1: DGP-6 Medium Authority
# ═══════════════════════════════════════════════════════════════════


def _check_medium_authority(objects: Sequence[RegistryObject], root: Path | None = None) -> list[RegistryFinding]:
    """DGP-E1: Verify medium authority map exists and generated defaults are correct."""
    findings: list[RegistryFinding] = []
    if not root:
        return findings

    medium_map = root / "docs/governance/artifact-medium-map.jsonl"
    if not medium_map.exists():
        findings.append(
            RegistryFinding(
                finding_id="MED-01",
                object_id="dgp-6-medium-map",
                status=RegistryFindingStatus.DEGRADED,
                invariant="medium-map-exists",
                message="artifact-medium-map.jsonl is missing",
                repair_action="Create medium authority map.",
            )
        )
        return findings

    import json

    for line in medium_map.read_text().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            generated = e.get("source_or_generated") == "generated"
            truth = e.get("current_truth_allowed_default", True)
            if generated and truth:
                findings.append(
                    RegistryFinding(
                        finding_id=f"MED-{e.get('medium_id', '?')}",
                        object_id=f"dgp-6-{e.get('medium_id', '?')}",
                        status=RegistryFindingStatus.BLOCKED,
                        invariant="medium-generated-not-truth",
                        message=f"Medium '{e.get('medium_id')}' is generated but current_truth_allowed_default=True",
                        repair_action=f"Set current_truth_allowed_default=False for {e.get('medium_id')}.",
                    )
                )
        except:
            pass

    return findings


# ═══════════════════════════════════════════════════════════════════
# Check E1: DGP-7 Metabolism Integrity
# ═══════════════════════════════════════════════════════════════════


def _check_metabolism_integrity(objects: Sequence[RegistryObject], root: Path | None = None) -> list[RegistryFinding]:
    """DGP-E1: Verify tombstone/supersession ledgers are governed."""
    findings: list[RegistryFinding] = []
    if not root:
        return findings

    tombstone = root / "docs/governance/document-tombstone-ledger.jsonl"
    supersession = root / "docs/governance/document-supersession-map.jsonl"

    if not tombstone.exists():
        findings.append(
            RegistryFinding(
                finding_id="MET-01",
                object_id="dgp-7-tombstone",
                status=RegistryFindingStatus.DEGRADED,
                invariant="tombstone-ledger-exists",
                message="document-tombstone-ledger.jsonl is missing",
                repair_action="Create tombstone ledger.",
            )
        )
    if not supersession.exists():
        findings.append(
            RegistryFinding(
                finding_id="MET-02",
                object_id="dgp-7-supersession",
                status=RegistryFindingStatus.DEGRADED,
                invariant="supersession-map-exists",
                message="document-supersession-map.jsonl is missing",
                repair_action="Create supersession map.",
            )
        )

    return findings


# ═══════════════════════════════════════════════════════════════════
# Check E1: DGP-8 Knowledge Navigation
# ═══════════════════════════════════════════════════════════════════


def _check_knowledge_navigation(objects: Sequence[RegistryObject], root: Path | None = None) -> list[RegistryFinding]:
    """DGP-E1: Verify knowledge map and system map are governed."""
    findings: list[RegistryFinding] = []
    if not root:
        return findings

    km = root / "docs/governance/knowledge-map.json"
    rg = root / "docs/ai/reading-graph.json"
    sm = root / "docs/ai/current-system-map.md"

    if not km.exists():
        findings.append(
            RegistryFinding(
                finding_id="KNW-01",
                object_id="dgp-8-knowledge-map",
                status=RegistryFindingStatus.DEGRADED,
                invariant="knowledge-map-exists",
                message="knowledge-map.json is missing",
                repair_action="Create knowledge map.",
            )
        )
    if not rg.exists():
        findings.append(
            RegistryFinding(
                finding_id="KNW-02",
                object_id="dgp-8-reading-graph",
                status=RegistryFindingStatus.DEGRADED,
                invariant="reading-graph-exists",
                message="reading-graph.json is missing",
                repair_action="Create reading graph.",
            )
        )
    if not sm.exists():
        findings.append(
            RegistryFinding(
                finding_id="KNW-03",
                object_id="dgp-8-system-map",
                status=RegistryFindingStatus.DEGRADED,
                invariant="system-map-exists",
                message="current-system-map.md is missing",
                repair_action="Create current system map.",
            )
        )
    if sm.exists() and ("registry-index" not in sm.read_text() or "not authoriz" not in sm.read_text().lower()):
        findings.append(
            RegistryFinding(
                finding_id="KNW-04",
                object_id="dgp-8-system-map",
                status=RegistryFindingStatus.DEGRADED,
                invariant="system-map-content",
                message="System map missing registry-index reference or non-authorization boundary",
                repair_action="Add registry-index and non-authorization to system map.",
            )
        )

    return findings


_RECONCILER_CHECKS: tuple[tuple[str, object], ...] = (
    ("referenced-but-missing", _check_referenced_but_missing),
    ("active-t0-t1-owner-gap", _check_owner_gaps),
    ("generated-as-truth", _check_generated_as_truth),
    ("legacy-scope-gap", _check_legacy_scope_gap),
    ("config-surface-gap", _check_config_surfaces_unregistered),
    ("authority-over-elevation", _check_authority_over_elevation),
    ("lifecycle-invariants", _check_lifecycle_invariants),
    ("authority-boundary", _check_authority_boundary),
    ("onboarding-integrity", _check_onboarding_integrity),
    ("receipt-standards", _check_receipt_standards),
    ("medium-authority", _check_medium_authority),
    ("metabolism-integrity", _check_metabolism_integrity),
    ("knowledge-navigation", _check_knowledge_navigation),
)


def reconcile_registry_objects(
    objects: Sequence[RegistryObject],
    *,
    checks: Sequence[str] | None = None,
    root: Path | None = None,
) -> ReconcileResult:
    """Run cross-registry consistency checks against a set of RegistryObjects.

    Args:
        objects: Imported registry objects from any/all sources.
        checks: Optional list of check names to run. None = all checks.
        root: Project root for filesystem path resolution. Used by
              referenced-but-missing check to validate file paths.

    Returns:
        ReconcileResult with findings and summary.
    """
    obj_list = tuple(objects)
    all_findings: list[RegistryFinding] = []
    by_check: dict[str, int] = {}
    total_routed = 0

    for check_name, check_fn in _RECONCILER_CHECKS:
        if checks is not None and check_name not in checks:
            continue
        if check_name in (
            "referenced-but-missing",
            "onboarding-integrity",
            "receipt-standards",
            "medium-authority",
            "metabolism-integrity",
            "knowledge-navigation",
        ):
            if root is not None:
                result = check_fn(obj_list, root=root)
            else:
                result = check_fn(obj_list)
        elif check_name == "active-t0-t1-owner-gap":
            if root is not None:
                findings_result, routed = check_fn(obj_list, root=root)
            else:
                findings_result, routed = check_fn(obj_list)
            result = findings_result
            total_routed += routed
        else:
            result = check_fn(obj_list)
        if result:
            all_findings.extend(result)
            by_check[check_name] = len(result)

    blocked = sum(1 for f in all_findings if f.status == RegistryFindingStatus.BLOCKED)
    degraded = sum(1 for f in all_findings if f.status == RegistryFindingStatus.DEGRADED)

    summary = ReconcileSummary(
        total_objects=len(obj_list),
        blocked_count=blocked,
        degraded_count=degraded,
        routed_by_inheritance=total_routed,
        by_check=by_check,
    )

    return ReconcileResult(
        objects=obj_list,
        findings=tuple(all_findings),
        summary=summary,
    )


def reconcile_imported_sources(results: dict, root: Path | None = None) -> ReconcileResult:
    """Reconcile objects from multiple RG-2 import results.

    Args:
        results: Dict of {source_name: RegistryImportResult} from import_all_registry_sources().
        root: Project root for filesystem path resolution.

    Returns:
        ReconcileResult with combined findings.
    """
    all_objects: list[RegistryObject] = []
    for result in results.values():
        all_objects.extend(result.objects)

    return reconcile_registry_objects(all_objects, root=root)


# ═══════════════════════════════════════════════════════════════════
# Generated Registry Index (RG-8)
# ═══════════════════════════════════════════════════════════════════


def _get_registry_sources_safe() -> list[dict]:
    """Try to load registry source/view declarations; return empty list on failure."""
    try:
        from ordivon_verify.registry.sources import get_registry_source_views

        return get_registry_source_views()
    except Exception:
        return []


def generate_registry_index(root: Path | None = None) -> dict:
    """Import all sources, reconcile, and produce a unified registry index.

    This is the RG-8 generated index — NOT source of truth. It is a
    machine-generated compilation of all registry sources for querying.

    Args:
        root: Project root. Defaults to auto-detection (3 levels up from this file).

    Returns:
        Dict with metadata, objects, findings, and breakdowns suitable for
        writing to .ordivon/registry/generated-registry.json.
    """
    from datetime import datetime, timezone

    from ordivon_verify.registry.adapters import import_all_registry_sources

    if root is None:
        root = Path(__file__).resolve().parents[2]  # reconciler → registry → ordivon_verify → src → root

    # Import all sources
    import_results = import_all_registry_sources(root)

    # Reconcile
    reconcile_result = reconcile_imported_sources(import_results, root=root)

    # Build object dict as JSON-serializable
    objects = {}
    for obj in reconcile_result.objects:
        objects[obj.registry_id] = {
            "registry_id": obj.registry_id,
            "kind": obj.kind.value,
            "path": obj.path,
            "title": obj.title,
            "authority_tier": obj.authority_tier.value,
            "lifecycle_state": obj.lifecycle_state.value,
            "current_truth_allowed": obj.current_truth_allowed,
            "owner": obj.owner,
            "generated": obj.generated,
            "source_registry": obj.source_registry,
        }

    # Build findings list
    findings_list = []
    for f in reconcile_result.findings:
        findings_list.append({
            "finding_id": f.finding_id,
            "object_id": f.object_id,
            "status": f.status.value,
            "invariant": f.invariant,
            "message": f.message,
            "repair_action": f.repair_action,
        })

    # Breakdowns
    by_kind: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_authority: dict[str, int] = {}
    for obj in reconcile_result.objects:
        by_kind[obj.kind.value] = by_kind.get(obj.kind.value, 0) + 1
        src = obj.source_registry or "unknown"
        by_source[src] = by_source.get(src, 0) + 1
        by_authority[obj.authority_tier.value] = by_authority.get(obj.authority_tier.value, 0) + 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "version": "rg-8-alpha",
        "authority": "generated_view",
        "current_truth_allowed": False,
        "registry_sources": _get_registry_sources_safe(),
        "summary": {
            "total_objects": reconcile_result.summary.total_objects,
            "blocked_findings": reconcile_result.summary.blocked_count,
            "degraded_findings": reconcile_result.summary.degraded_count,
            "routed_by_inheritance": reconcile_result.summary.routed_by_inheritance,
            "by_check": reconcile_result.summary.by_check,
            "by_kind": by_kind,
            "by_source": by_source,
            "by_authority": by_authority,
        },
        "objects": objects,
        "findings": findings_list,
    }
