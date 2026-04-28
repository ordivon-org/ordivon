"""CandidateRule Review Service — human review path for CandidateRule drafts.

State transitions (strict):
  draft → under_review  (submit_for_review)
  draft → rejected      (reject directly from draft)
  under_review → accepted_candidate  (accept)
  under_review → rejected            (reject)

Forbidden transitions:
  - accepted_candidate → anything (terminal without explicit reopen)
  - rejected → accepted_candidate (must create new draft)
  - any state → Policy (Policy promotion is separate, human-only)

Reviewer metadata is stored in source_refs:
  - "reviewer:<id>"     — who performed the review
  - "review_rationale:<text>" — reason for the decision
  - "reviewed_at:<iso>" — when the review occurred

This service does NOT:
  - Create Policy
  - Trigger execution
  - Modify packs/finance or packs/coding
  - Call broker/order/trade/shell/MCP/IDE
"""

from __future__ import annotations


from domains.candidate_rules.models import VALID_CANDIDATE_RULE_STATES
from domains.candidate_rules.repository import CandidateRuleRepository
from shared.time.clock import utc_now


class InvalidReviewTransition(Exception):
    """Raised when a CandidateRule status transition is not allowed."""

    def __init__(self, rule_id: str, current: str, target: str, reason: str = "") -> None:
        self.rule_id = rule_id
        self.current = current
        self.target = target
        msg = f"CandidateRule {rule_id}: cannot transition from '{current}' to '{target}'"
        if reason:
            msg += f" — {reason}"
        super().__init__(msg)


class CandidateRuleNotFound(Exception):
    """Raised when a CandidateRule does not exist."""

    def __init__(self, rule_id: str) -> None:
        super().__init__(f"CandidateRule not found: {rule_id}")


# Valid transitions: {from_status: {allowed_target_statuses}}
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"under_review", "rejected"},
    "under_review": {"accepted_candidate", "rejected"},
    "accepted_candidate": set(),  # terminal — no transitions
    "rejected": set(),  # terminal — no transitions
}


class CandidateRuleReviewService:
    """Manages the human review path for CandidateRule status transitions."""

    def __init__(self, repository: CandidateRuleRepository) -> None:
        self._repo = repository

    # ── Public API ──────────────────────────────────────────────────

    def submit_for_review(self, rule_id: str, *, reviewer_id: str, note: str | None = None) -> None:
        """Transition a draft CandidateRule to under_review."""
        self._transition(rule_id, "under_review", reviewer_id=reviewer_id, note=note)

    def accept_candidate(self, rule_id: str, *, reviewer_id: str, rationale: str) -> None:
        """Accept a CandidateRule as a valid candidate (NOT Policy promotion)."""
        self._transition(rule_id, "accepted_candidate", reviewer_id=reviewer_id, note=rationale)

    def reject_candidate(self, rule_id: str, *, reviewer_id: str, rationale: str) -> None:
        """Reject a CandidateRule."""
        self._transition(rule_id, "rejected", reviewer_id=reviewer_id, note=rationale)

    # ── Internal ────────────────────────────────────────────────────

    def _transition(self, rule_id: str, target: str, *, reviewer_id: str, note: str | None = None) -> None:
        """Execute a validated status transition with reviewer metadata."""
        if target not in VALID_CANDIDATE_RULE_STATES:
            raise ValueError(f"Invalid target status: {target!r}")

        row = self._repo.get(rule_id)
        if row is None:
            raise CandidateRuleNotFound(rule_id)

        current = row.status
        allowed = _VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidReviewTransition(rule_id, current, target)

        # Append reviewer metadata to source_refs
        from shared.utils.serialization import from_json_text, to_json_text

        refs: list[str] = list(from_json_text(row.source_refs_json, []))
        reviewed_at = utc_now().isoformat()
        refs.append(f"reviewer:{reviewer_id}")
        refs.append(f"reviewed_at:{reviewed_at}")
        if note:
            refs.append(f"review_rationale:{note}")

        row.source_refs_json = to_json_text(refs)
        row.status = target
        self._repo.db.flush()
