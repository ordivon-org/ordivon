"""Stage Manifest — Ordivon Control Plane desired state model.

A StageManifest declares what a governance stage should produce, what
boundaries it must respect, what verification it must pass, and what
predicates constitute closure.

This is the Ordivon equivalent of a Kubernetes Custom Resource — the
desired state that the Reconciler compares against actual repo state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ── Enums ───────────────────────────────────────────────────────────

class RiskClass(str, Enum):
    """Risk classification for a stage."""
    AP_R0 = "AP-R0"   # advisory / documentation only
    AP_R1 = "AP-R1"   # local code change, no external effect
    AP_R2 = "AP-R2"   # integration / external dependency
    AP_R3 = "AP-R3"   # runtime / external action / publish


class AuthorityImpact(str, Enum):
    """Authority impact level."""
    AI_0 = "AI-0"     # current_truth only
    AI_1 = "AI-1"     # governance docs / schemas
    AI_2 = "AI-2"     # policy proposal / evidence
    AI_3 = "AI-3"     # policy activation / publish / release


class ClosureStatus(str, Enum):
    """Stage closure state."""
    ACTIVE = "active"
    READY_FOR_REVIEW = "ready_for_review"
    CLOSED = "closed"
    REOPENED = "reopened"
    BLOCKED = "blocked"


# ── Verification Gate ───────────────────────────────────────────────

@dataclass(frozen=True)
class VerificationGate:
    """A single verification step in a stage manifest."""
    gate_id: str
    command: str
    description: str = ""
    on_failure: str = "BLOCKED"   # BLOCKED | DEGRADED | ADVISORY
    timeout: int = 300


# ── Closure Predicate ───────────────────────────────────────────────

@dataclass(frozen=True)
class ClosurePredicate:
    """A condition that must be true for the stage to be closed."""
    predicate_id: str
    description: str = ""
    check_method: str = ""   # registry_scan, receipt_schema_validation, etc.


# ── Stage Manifest ──────────────────────────────────────────────────

@dataclass(frozen=True)
class StageManifest:
    """Desired state for a governance stage.

    Loaded from stage-templates/*.yaml (CATLASS) or standalone manifest YAML.
    This is the canonical declaration of what a stage IS.
    """
    stage_id: str
    risk_class: RiskClass
    authority_impact: AuthorityImpact
    task_type: str = "documentation_governance"
    description: str = ""

    allowed_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()

    required_verification: tuple[VerificationGate, ...] = ()
    required_evidence: tuple[str, ...] = ()
    required_receipt_fields: tuple[str, ...] = ()
    closure_predicates: tuple[ClosurePredicate, ...] = ()

    template_id: str = ""
    template_version: int = 1

    # ── Factory ─────────────────────────────────────────────────

    @classmethod
    def from_template(cls, template: dict, stage_id: str) -> StageManifest:
        """Create a StageManifest from a CATLASS template dict."""
        # Parse verification gates
        gates = []
        for g in template.get("verification", []):
            if isinstance(g, dict):
                gates.append(VerificationGate(
                    gate_id=g.get("id", ""),
                    command=g.get("command", ""),
                    description=g.get("description", ""),
                    on_failure=g.get("on_failure", "BLOCKED"),
                    timeout=g.get("timeout", 300),
                ))

        # Parse closure predicates
        predicates = []
        closure_cfg = template.get("closure", {})
        if isinstance(closure_cfg, dict):
            for key, val in closure_cfg.items():
                if isinstance(val, bool) and val:
                    predicates.append(ClosurePredicate(
                        predicate_id=key,
                        description=key.replace("_", " "),
                    ))

        # Parse allowed/forbidden
        allowed = tuple(template.get("allowed_paths", []))
        forbidden = tuple(template.get("forbidden_boundaries", []))

        # Determine risk class from template — doc-governance defaults to AP-R0
        risk_str = template.get("risk_class", "AP-R0")
        try:
            risk = RiskClass(risk_str)
        except ValueError:
            risk = RiskClass.AP_R0

        auth_str = template.get("authority_impact", "AI-0")
        try:
            auth = AuthorityImpact(auth_str)
        except ValueError:
            auth = AuthorityImpact.AI_0

        return cls(
            stage_id=stage_id,
            risk_class=risk,
            authority_impact=auth,
            task_type=template.get("template_id", template.get("task_type", "documentation_governance")),
            description=template.get("description", ""),
            allowed_paths=allowed,
            forbidden_paths=forbidden,
            required_verification=tuple(gates),
            required_evidence=tuple(template.get("required_evidence", [])),
            required_receipt_fields=tuple(template.get("required_receipt_fields", [])),
            closure_predicates=tuple(predicates),
            template_id=template.get("template_id", ""),
            template_version=template.get("template_version", 1),
        )

    # ── Queries ─────────────────────────────────────────────────

    def is_hard_boundary(self, filepath: str) -> bool:
        """Check if a filepath violates a forbidden boundary."""
        from fnmatch import fnmatch
        for pattern in self.forbidden_paths:
            if fnmatch(filepath, pattern):
                return True
        return False

    def is_allowed(self, filepath: str) -> bool:
        """Check if a filepath is within allowed scope."""
        from fnmatch import fnmatch
        if not self.allowed_paths:
            return True  # no restrictions = everything allowed
        for pattern in self.allowed_paths:
            if fnmatch(filepath, pattern):
                return True
        return False
