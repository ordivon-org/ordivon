"""Policy Proposal Path — converts accepted_candidate CandidateRules to PolicyProposals.

This module bridges CandidateRule (governance learning) and Policy (runtime enforcement).
It does NOT:
  - Create active Policies
  - Modify pack policy files
  - Affect RiskEngine decisions
  - Trigger ExecutionRequest/ExecutionReceipt
  - Call broker/order/trade/shell/MCP/IDE

Architecture:
  CandidateRule(accepted_candidate) → PolicyProposal(draft) → (future) Policy(active)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domains.candidate_rules.repository import CandidateRuleRepository
from shared.time.clock import utc_now
from shared.utils.ids import new_id

VALID_PROPOSAL_STATUSES = frozenset({"draft", "under_review", "accepted", "rejected"})


@dataclass(slots=True)
class PolicyProposal:
    """A lightweight proposal to convert an accepted CandidateRule into a Policy.

    This is a plain dataclass — NOT an ORM model.
    Active Policy creation requires a future explicit human approval wave.
    """

    id: str = field(default_factory=lambda: new_id("pprop"))
    candidate_rule_id: str = ""
    status: str = "draft"
    proposed_policy_text: str = ""
    rationale: str = ""
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    created_by: str = ""
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def __post_init__(self) -> None:
        if not self.candidate_rule_id:
            raise ValueError("PolicyProposal requires candidate_rule_id.")
        if self.status not in VALID_PROPOSAL_STATUSES:
            raise ValueError(f"Unsupported proposal status: {self.status!r}")


class DuplicateProposalError(Exception):
    """Raised when a PolicyProposal already exists for a given CandidateRule."""

    def __init__(self, candidate_rule_id: str) -> None:
        super().__init__(
            f"PolicyProposal already exists for CandidateRule {candidate_rule_id}. "
            f"Use the existing proposal instead of creating a duplicate."
        )


class ProposalNotAllowedError(Exception):
    """Raised when a CandidateRule is not eligible for PolicyProposal creation."""

    def __init__(self, rule_id: str, status: str) -> None:
        super().__init__(
            f"CandidateRule {rule_id} has status '{status}'. "
            f"Only 'accepted_candidate' rules can generate PolicyProposals."
        )


class PolicyProposalService:
    """Creates PolicyProposal drafts from accepted_candidate CandidateRules.

    State guard:
      - Only accepted_candidate → PolicyProposal(draft)
      - draft/under_review/rejected → rejected with ProposalNotAllowedError
      - Duplicate → rejected with DuplicateProposalError (one proposal per rule)
    """

    def __init__(self, repository: CandidateRuleRepository) -> None:
        self._repo = repository
        self._proposals: dict[str, PolicyProposal] = {}  # candidate_rule_id → proposal

    def propose_from_accepted(self, candidate_rule_id: str, *, created_by: str, rationale: str) -> PolicyProposal:
        """Create a PolicyProposal(draft) from an accepted_candidate CandidateRule.

        Args:
            candidate_rule_id: The accepted CandidateRule to propose as Policy.
            created_by: Human identifier for audit trail.
            rationale: Why this rule should become Policy.

        Returns:
            A new PolicyProposal in draft status.

        Raises:
            ProposalNotAllowedError: If the CandidateRule is not accepted_candidate.
            DuplicateProposalError: If a proposal already exists for this rule.
        """
        # ── Guard 1: Duplicate check ──────────────────────────────
        if candidate_rule_id in self._proposals:
            raise DuplicateProposalError(candidate_rule_id)

        # ── Guard 2: Status check ─────────────────────────────────
        row = self._repo.get(candidate_rule_id)
        if row is None:
            raise ProposalNotAllowedError(candidate_rule_id, "not_found")
        if row.status != "accepted_candidate":
            raise ProposalNotAllowedError(candidate_rule_id, row.status)

        # ── Build proposal ────────────────────────────────────────
        from shared.utils.serialization import from_json_text

        source_refs: list[str] = list(from_json_text(row.source_refs_json, []))
        source_refs.append(f"candidate_rule:{candidate_rule_id}")

        proposal = PolicyProposal(
            candidate_rule_id=candidate_rule_id,
            status="draft",
            proposed_policy_text=row.summary,
            rationale=rationale,
            source_refs=tuple(source_refs),
            created_by=created_by,
        )
        self._proposals[candidate_rule_id] = proposal
        return proposal

    def get_proposal(self, candidate_rule_id: str) -> PolicyProposal | None:
        """Retrieve an existing PolicyProposal by candidate_rule_id."""
        return self._proposals.get(candidate_rule_id)

    def list_proposals(self) -> list[PolicyProposal]:
        """List all PolicyProposals."""
        return list(self._proposals.values())
