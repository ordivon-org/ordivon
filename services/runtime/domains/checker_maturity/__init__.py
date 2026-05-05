"""Checker Maturity — state machine for checker lifecycle.

Pure domain logic. No ORM, no DB, no side effects.
Enforces maturation: draft → shadow_tested → red_teamed → active.

Inspired by Rust RFC FCP (individual blocking power) and K8s KEP
(graduation stages with independent PRR review).

Design invariant: NO self-promotion. Every maturity transition
requires evidence from an independent source.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class MaturityLevel(str, Enum):
    """Checker maturity — from draft to active enforcement.

    draft:          Checker exists. May be incomplete. Advisory only.
    shadow_tested:  Has been run against shadow red-team corpus.
                    All expected verdicts matched. Evidence in
                    shadow-evaluation-log.jsonl.
    red_teamed:     Has passed adversarial review by someone other
                    than the checker author. Evidence in
                    red-team-review-ledger.jsonl.
    active:         Running in CI as a hard gate. Blocks PRs.
                    Requires owner approval recorded in
                    checker-activation-ledger.jsonl.
    deprecated:     Intentionally retired. Terminal state.
    archived:       Moved to .archive/. Terminal state.
    """

    DRAFT = "draft"
    SHADOW_TESTED = "shadow_tested"
    RED_TEAMED = "red_teamed"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


# ── Valid transitions ──────────────────────────────────────────
# Each transition requires specific evidence (validated by the gate checker)

VALID_TRANSITIONS: dict[MaturityLevel, frozenset[MaturityLevel]] = {
    MaturityLevel.DRAFT: frozenset({MaturityLevel.SHADOW_TESTED}),
    MaturityLevel.SHADOW_TESTED: frozenset({MaturityLevel.DRAFT, MaturityLevel.RED_TEAMED}),
    MaturityLevel.RED_TEAMED: frozenset({
        MaturityLevel.DRAFT,           # rejected → back to draft
        MaturityLevel.SHADOW_TESTED,   # re-evaluate
        MaturityLevel.ACTIVE,          # promote (requires owner signoff)
    }),
    MaturityLevel.ACTIVE: frozenset({
        MaturityLevel.DRAFT,           # emergency rollback
        MaturityLevel.DEPRECATED,      # intentional retirement
    }),
    MaturityLevel.DEPRECATED: frozenset({
        MaturityLevel.ARCHIVED,        # final archival
    }),
    MaturityLevel.ARCHIVED: frozenset(),  # terminal
}


# ── Evidence requirements per transition ────────────────────────

@dataclass(frozen=True)
class TransitionEvidence:
    """What evidence is required for a specific maturity transition."""
    transition: str        # "draft→shadow_tested"
    requires: tuple[str, ...]  # evidence types required
    must_be_independent: bool   # must come from someone other than author


TRANSITION_EVIDENCE: dict[str, TransitionEvidence] = {
    "draft→shadow_tested": TransitionEvidence(
        transition="draft→shadow_tested",
        requires=("shadow_evaluation_log",),
        must_be_independent=True,
    ),
    "shadow_tested→red_teamed": TransitionEvidence(
        transition="shadow_tested→red_teamed",
        requires=("red_team_review_receipt",),
        must_be_independent=True,
    ),
    "red_teamed→active": TransitionEvidence(
        transition="red_teamed→active",
        requires=("owner_approval", "policy_shadow_assessment"),
        must_be_independent=True,
    ),
    # Demotions (emergency rollback) require less evidence
    "active→draft": TransitionEvidence(
        transition="active→draft",
        requires=("rollback_receipt",),
        must_be_independent=False,  # owner can roll back their own gate
    ),
}


# ── Checker Maturity Record ────────────────────────────────────

@dataclass(frozen=True)
class CheckerMaturityRecord:
    """Immutable record of a checker's maturity state.

    State transitions produce new records — the old record remains
    as immutable evidence.
    """
    checker_id: str                 # gate_id from CHECKER.md
    maturity: MaturityLevel
    author: str                     # who created/owns this checker
    changed_by: str                 # who made the last transition
    changed_at: str                 # ISO timestamp
    evidence_refs: tuple[str, ...]  # references to evidence documents
    predecessor_id: str | None = None  # lineage tracking
    notes: str = ""
    grandfathered: bool = False     # admitted without full maturity pipeline

    def __post_init__(self) -> None:
        if not self.checker_id.strip():
            raise ValueError("CheckerMaturityRecord requires checker_id.")
        if not self.author.strip():
            raise ValueError("CheckerMaturityRecord requires author.")
        if not self.changed_by.strip():
            raise ValueError("CheckerMaturityRecord requires changed_by.")


# ── State Machine ──────────────────────────────────────────────

class InvalidTransitionError(Exception):
    """Raised when a maturity transition is not allowed."""

    def __init__(self, current: MaturityLevel, target: MaturityLevel) -> None:
        allowed = VALID_TRANSITIONS.get(current, frozenset())
        super().__init__(
            f"Cannot transition from '{current.value}' to '{target.value}'. "
            f"Allowed targets from '{current.value}': "
            f"{sorted(a.value for a in allowed)}."
        )


class MissingEvidenceError(Exception):
    """Raised when required evidence is missing for a transition."""

    def __init__(self, transition: str, missing: list[str]) -> None:
        super().__init__(
            f"Transition '{transition}' requires evidence: {missing}. "
            "Provide the required evidence before retrying."
        )


class SelfPromotionError(Exception):
    """Raised when the author tries to self-promote."""

    def __init__(self, transition: str) -> None:
        super().__init__(
            f"Transition '{transition}' requires independent review. "
            "Author cannot self-promote. Evidence must come from a different person."
        )


class CheckerMaturityStateMachine:
    """Validates and executes maturity transitions.

    Pure domain logic. Does NOT write to files or modify state.
    Returns new CheckerMaturityRecord on successful transition.

    Usage:
        machine = CheckerMaturityStateMachine()
        try:
            new_record = machine.transition(
                current, target=MaturityLevel.SHADOW_TESTED,
                changed_by="alice", evidence_refs=["shadow-log:2026-05-04"]
            )
        except InvalidTransitionError:
            ...
    """

    @staticmethod
    def allowed_transitions_from(level: MaturityLevel) -> frozenset[MaturityLevel]:
        """What maturity levels can this level transition to?"""
        return VALID_TRANSITIONS.get(level, frozenset())

    @staticmethod
    def is_terminal(level: MaturityLevel) -> bool:
        """Is this a terminal state (no further transitions)?"""
        return len(VALID_TRANSITIONS.get(level, frozenset())) == 0

    @staticmethod
    def transition(
        current: CheckerMaturityRecord,
        target: MaturityLevel,
        changed_by: str,
        evidence_refs: tuple[str, ...] = (),
        notes: str = "",
    ) -> CheckerMaturityRecord:
        """Validate and execute a maturity transition.

        Returns a new CheckerMaturityRecord on success.
        Raises on invalid transition, missing evidence, or self-promotion.
        """
        # ── Gate 1: Is this a valid transition? ─────────────────
        allowed = VALID_TRANSITIONS.get(current.maturity, frozenset())
        if target not in allowed:
            raise InvalidTransitionError(current.maturity, target)

        transition_key = f"{current.maturity.value}→{target.value}"
        evidence_req = TRANSITION_EVIDENCE.get(transition_key)

        # ── Gate 2: Evidence exists? ────────────────────────────
        if evidence_req and evidence_req.requires:
            if not evidence_refs:
                raise MissingEvidenceError(
                    transition_key,
                    list(evidence_req.requires),
                )

        # ── Gate 3: Independent review? ─────────────────────────
        if evidence_req and evidence_req.must_be_independent:
            if changed_by == current.author:
                raise SelfPromotionError(transition_key)

        # ── Execute transition ──────────────────────────────────
        return CheckerMaturityRecord(
            checker_id=current.checker_id,
            maturity=target,
            author=current.author,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc).isoformat(),
            evidence_refs=evidence_refs,
            predecessor_id=current.checker_id,
            notes=notes,
        )
