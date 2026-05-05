"""Governance Reconciler — Ordivon Control Plane reconciler.

Compares desired state (StageManifest) against actual repo state and
produces a drift report. This is the closed-loop control mechanism:
desired → actual → drift → reconcile action.

Usage:
    from ordivon_verify.control.reconciler import Reconciler, RepoSnapshot
    snapshot = RepoSnapshot.capture(ROOT)
    report = Reconciler(manifest).reconcile(snapshot)
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ordivon_verify.control.stage_manifest import (
    StageManifest, VerificationGate, ClosurePredicate, ClosureStatus,
)
from ordivon_verify.control.base_types import DriftEntry, RepoSnapshot
from ordivon_verify.control.rule_registry import evaluate_rules


# ── Reconciliation Report ───────────────────────────────────────────

@dataclass
class ReconciliationReport:
    """Result of reconciling desired vs actual state."""
    stage_id: str
    timestamp: str
    desired: StageManifest
    actual: RepoSnapshot
    drifts: list[DriftEntry] = field(default_factory=list)
    overall: str = "READY"   # READY | DEGRADED | BLOCKED

    @property
    def blocked(self) -> bool:
        return any(d.severity == "BLOCKED" for d in self.drifts)

    @property
    def degraded(self) -> bool:
        return any(d.severity == "DEGRADED" for d in self.drifts) and not self.blocked


# ── Reconciler ──────────────────────────────────────────────────────

class Reconciler:
    """Compares desired state (StageManifest) against actual repo state."""

    def __init__(self, manifest: StageManifest):
        self.manifest = manifest

    def reconcile(self, snapshot: RepoSnapshot) -> ReconciliationReport:
        """Produce a drift report by comparing manifest vs snapshot.

        Uses the GovernanceRule registry — no hardcoded if/else.
        Adding a new rule = adding one entry to GOVERNANCE_RULES.
        """
        report = ReconciliationReport(
            stage_id=self.manifest.stage_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            desired=self.manifest,
            actual=snapshot,
        )

        # Evaluate all applicable governance rules
        report.drifts = evaluate_rules(self.manifest, snapshot)

        # Compute overall
        if report.blocked:
            report.overall = "BLOCKED"
        elif report.degraded:
            report.overall = "DEGRADED"
        else:
            report.overall = "READY"

        return report


# Re-export for convenience
RiskClass = __import__('ordivon_verify.control.stage_manifest', fromlist=['RiskClass']).RiskClass
AuthorityImpact = __import__('ordivon_verify.control.stage_manifest', fromlist=['AuthorityImpact']).AuthorityImpact
