"""Detector Framework — Governance Rule Registry.

Replaces hardcoded if/else in the Reconciler with a registry of
GovernanceRules. Each rule declares:
  - When it applies (applies_when predicate)
  - What it checks (check function)
  - What severity it carries (BLOCKED | DEGRADED | ADVISORY)
  - What evidence types it consumes
  - What fixtures validate it

Adding a new governance rule = adding one entry to GOVERNANCE_RULES.
No reconciler code changes needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ordivon_verify.control.stage_manifest import (
    StageManifest,
    RiskClass,
    AuthorityImpact,
)
from ordivon_verify.control.base_types import DriftEntry, RepoSnapshot


# ═══════════════════════════════════════════════════════════════════
# Governance Rule
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class GovernanceRule:
    """A single governance detection rule.

    Immutable. Registered once, evaluated by Reconciler for every stage.
    """

    rule_id: str  # unique: "BOUNDARY-FORBIDDEN-PATH"
    category: str  # boundary | authority | evidence | closure
    severity: str  # BLOCKED | DEGRADED | ADVISORY
    description: str  # human-readable
    applies_when: Callable[[StageManifest, RepoSnapshot], bool]
    check: Callable[[StageManifest, RepoSnapshot], list[DriftEntry]]
    evidence_types: tuple[str, ...] = ()  # what evidence this rule consumes
    fixture_refs: tuple[str, ...] = ()  # test fixtures that validate this rule
    false_positive_notes: str = ""  # known false positive patterns
    remediation: str = ""  # how to fix violations


# ═══════════════════════════════════════════════════════════════════
# Rule definitions
# ═══════════════════════════════════════════════════════════════════


def _all_files(snapshot: RepoSnapshot) -> list[str]:
    """All files that have changed (modified + untracked)."""
    return snapshot.modified_files + snapshot.untracked_files


def _check_boundary_forbidden(manifest: StageManifest, snapshot: RepoSnapshot) -> list[DriftEntry]:
    """Check: any modified file matches a forbidden_paths pattern."""
    drifts = []
    for f in _all_files(snapshot):
        if manifest.is_hard_boundary(f):
            drifts.append(
                DriftEntry(
                    category="boundary",
                    severity="BLOCKED",
                    description=f"Forbidden path modified: {f}",
                    detail=f"Stage {manifest.stage_id} (risk={manifest.risk_class.value}) must not touch {f}",
                )
            )
    return drifts


def _check_apr0_source(manifest: StageManifest, snapshot: RepoSnapshot) -> list[DriftEntry]:
    """Check: AP-R0 stages must not modify source code outside docs/."""
    if manifest.risk_class != RiskClass.AP_R0:
        return []
    drifts = []
    for f in _all_files(snapshot):
        if f.startswith("src/") and not f.startswith("src/ordivon_verify/registry.py"):
            if not manifest.is_allowed(f):
                drifts.append(
                    DriftEntry(
                        category="authority",
                        severity="BLOCKED",
                        description=f"AP-R0 stage modifying source: {f}",
                        detail="AP-R0 is advisory/documentation only. Source changes require AP-R1+.",
                    )
                )
    return drifts


def _check_ai0_policy(manifest: StageManifest, snapshot: RepoSnapshot) -> list[DriftEntry]:
    """Check: AI-0 stages must not modify policy-related files."""
    if manifest.authority_impact != AuthorityImpact.AI_0:
        return []
    drifts = []
    for f in _all_files(snapshot):
        if "policy" in f.lower() and not f.startswith("docs/"):
            drifts.append(
                DriftEntry(
                    category="authority",
                    severity="BLOCKED",
                    description=f"AI-0 stage modifying policy file: {f}",
                    detail="AI-0 is current_truth only. Policy changes require AI-2+.",
                )
            )
    return drifts


def _check_verification_coverage(manifest: StageManifest, snapshot: RepoSnapshot) -> list[DriftEntry]:
    """Check: every stage must declare at least pr-fast verification."""
    if not manifest.required_verification:
        return [
            DriftEntry(
                category="verification",
                severity="DEGRADED",
                description="No verification gates declared in manifest",
                detail="Every stage must declare at minimum pr-fast baseline.",
            )
        ]
    return []


def _check_evidence_required(manifest: StageManifest, snapshot: RepoSnapshot) -> list[DriftEntry]:
    """Check: if git_diff evidence is required, files must be modified."""
    drifts = []
    for ev in manifest.required_evidence:
        if ev == "git_diff" and not snapshot.modified_files:
            drifts.append(
                DriftEntry(
                    category="evidence",
                    severity="DEGRADED",
                    description="git_diff evidence required but no files modified",
                )
            )
    return drifts


# ═══════════════════════════════════════════════════════════════════
# Rule Registry
# ═══════════════════════════════════════════════════════════════════

GOVERNANCE_RULES: tuple[GovernanceRule, ...] = (
    GovernanceRule(
        rule_id="BOUNDARY-FORBIDDEN-PATH",
        category="boundary",
        severity="BLOCKED",
        description="No file may match a forbidden_paths pattern",
        applies_when=lambda m, s: bool(m.forbidden_paths),
        check=_check_boundary_forbidden,
        evidence_types=("git_diff", "file_change_list"),
        remediation="Move the file change to a stage whose template allows it, or split into multiple stages.",
    ),
    GovernanceRule(
        rule_id="AUTH-APR0-SOURCE-MODIFICATION",
        category="authority",
        severity="BLOCKED",
        description="AP-R0 stages must not modify source code",
        applies_when=lambda m, s: m.risk_class == RiskClass.AP_R0,
        check=_check_apr0_source,
        evidence_types=("git_diff",),
        false_positive_notes="src/ordivon_verify/registry.py is DOCS — describing old API, not functional code",
        remediation="Upgrade to AP-R1+ stage if source changes are intentional, or revert.",
    ),
    GovernanceRule(
        rule_id="AUTH-AI0-POLICY-MODIFICATION",
        category="authority",
        severity="BLOCKED",
        description="AI-0 stages must not modify policy files",
        applies_when=lambda m, s: m.authority_impact == AuthorityImpact.AI_0,
        check=_check_ai0_policy,
        evidence_types=("git_diff",),
        remediation="Policy changes require AI-2+ and human approval.",
    ),
    GovernanceRule(
        rule_id="VERIFY-COVERAGE-MINIMUM",
        category="verification",
        severity="DEGRADED",
        description="Every stage must declare verification gates",
        applies_when=lambda m, s: True,
        check=_check_verification_coverage,
        evidence_types=(),
        remediation="Add at minimum pr-fast baseline to required_verification.",
    ),
    GovernanceRule(
        rule_id="EVIDENCE-GIT-DIFF-REQUIRED",
        category="evidence",
        severity="DEGRADED",
        description="If git_diff evidence is required, files must be modified",
        applies_when=lambda m, s: "git_diff" in m.required_evidence,
        check=_check_evidence_required,
        evidence_types=("git_diff",),
    ),
)


def evaluate_rules(manifest: StageManifest, snapshot: RepoSnapshot) -> list[DriftEntry]:
    """Evaluate all applicable governance rules against current state.

    This replaces the hardcoded if/else in Reconciler.reconcile().
    """
    all_drifts = []
    for rule in GOVERNANCE_RULES:
        try:
            if rule.applies_when(manifest, snapshot):
                drifts = rule.check(manifest, snapshot)
                all_drifts.extend(drifts)
        except Exception as e:
            # A rule that crashes should itself become a drift
            all_drifts.append(
                DriftEntry(
                    category="verification",
                    severity="DEGRADED",
                    description=f"Rule {rule.rule_id} failed to evaluate: {e}",
                )
            )
    return all_drifts


def list_rules() -> list[dict]:
    """Return all registered rules as dicts (for CLI inspection)."""
    return [
        {
            "rule_id": r.rule_id,
            "category": r.category,
            "severity": r.severity,
            "description": r.description,
        }
        for r in GOVERNANCE_RULES
    ]
