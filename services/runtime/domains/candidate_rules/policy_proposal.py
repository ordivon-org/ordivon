"""CandidateRule → Policy Bridge — maps accepted_candidate to PolicyRecord(draft).

This module is the ADAPTER between CandidateRule (governance learning) and
the Policy Platform (domains/policies). It does NOT:
  - Create active/enforced Policies
  - Modify Pack policy files
  - Affect RiskEngine decisions
  - Trigger ExecutionRequest/ExecutionReceipt
  - Require owner or rollback_plan at draft stage

Architecture (Phase 5.3 boundary alignment):
  CandidateRule(accepted_candidate) → PolicyRecord(state=draft)
  PolicyRecord then follows PolicyStateMachine lifecycle in domains/policies/.

The old standalone PolicyProposal dataclass is retired.
PolicyRecord is the canonical Policy entity.
"""

from __future__ import annotations

from domains.candidate_rules.repository import CandidateRuleRepository
from domains.policies.models import (
    PolicyRecord,
    PolicyScope,
    PolicyState,
    PolicyRisk,
    PolicyEvidenceRef,
    EvidenceFreshness,
)
from shared.utils.ids import new_id


class ProposalNotAllowedError(Exception):
    """Raised when a CandidateRule is not eligible for Policy creation."""

    def __init__(self, rule_id: str, status: str) -> None:
        super().__init__(
            f"CandidateRule {rule_id} has status '{status}'. "
            f"Only 'accepted_candidate' rules can generate Policy drafts."
        )


class DuplicateProposalError(Exception):
    """Raised when a Policy draft already exists for a given CandidateRule."""

    def __init__(self, candidate_rule_id: str) -> None:
        super().__init__(
            f"Policy already drafted for CandidateRule {candidate_rule_id}. "
            f"Use the existing draft instead of creating a duplicate."
        )


class CandidateRulePolicyBridge:
    """Creates PolicyRecord(draft) from accepted_candidate CandidateRules.

    This is the single entry point from the CandidateRule learning path
    into the Policy Platform. It enforces:
      - Only accepted_candidate → draft (never active)
      - Duplicate prevention (one draft per CandidateRule)
      - Evidence lineage (CandidateRule source_refs → PolicyEvidenceRefs)

    The output is a pure PolicyRecord whose lifecycle is managed by
    domains/policies/state_machine.py. No active policy can emerge
    from this bridge.
    """

    def __init__(self, repository: CandidateRuleRepository) -> None:
        self._repo = repository
        self._drafts: dict[str, PolicyRecord] = {}  # candidate_rule_id → PolicyRecord

    def create_policy_draft(
        self,
        candidate_rule_id: str,
        *,
        created_by: str,
        rationale: str,
        scope: PolicyScope = PolicyScope.PACK,
        risk: PolicyRisk = PolicyRisk.LOW,
    ) -> PolicyRecord:
        """Create a PolicyRecord(draft) from an accepted_candidate CandidateRule.

        Args:
            candidate_rule_id: The accepted CandidateRule to draft as Policy.
            created_by: Human identifier for audit trail.
            rationale: Why this rule should become Policy.
            scope: The PolicyScope for the resulting Policy (default: PACK).
            risk: The PolicyRisk classification (default: LOW, can be updated later).

        Returns:
            A new PolicyRecord in DRAFT state.

        Raises:
            ProposalNotAllowedError: If the CandidateRule is not accepted_candidate.
            DuplicateProposalError: If a draft already exists for this rule.
        """
        # ── Guard 1: Duplicate check ──────────────────────────────
        if candidate_rule_id in self._drafts:
            raise DuplicateProposalError(candidate_rule_id)

        # ── Guard 2: Status check — only accepted_candidate ──────
        row = self._repo.get(candidate_rule_id)
        if row is None:
            raise ProposalNotAllowedError(candidate_rule_id, "not_found")
        if row.status != "accepted_candidate":
            raise ProposalNotAllowedError(candidate_rule_id, row.status)

        # ── Guard 3: This bridge NEVER creates active policies ────
        # PolicyRecord.__post_init__ would already reject active states
        # without evidence/owner/rollback_plan, but we enforce it here
        # explicitly for clarity.

        # ── Build evidence refs from CandidateRule lineage ────────
        from shared.utils.serialization import from_json_text

        raw_refs: list[str] = list(from_json_text(row.source_refs_json, []))
        raw_refs.append(f"candidate_rule:{candidate_rule_id}")

        evidence_refs: list[PolicyEvidenceRef] = [
            PolicyEvidenceRef(
                ref_type=_infer_ref_type(ref),
                ref_id=ref,
                freshness=EvidenceFreshness.CURRENT,
            )
            for ref in raw_refs
        ]

        # ── Create PolicyRecord(draft) ────────────────────────────
        policy = PolicyRecord(
            policy_id=new_id("pol"),
            title=row.summary,
            scope=scope,
            state=PolicyState.DRAFT,
            risk=risk,
            evidence_refs=tuple(evidence_refs),
            # owner and rollback_plan are NOT required at draft stage.
            # They are required before active_shadow/enforced per
            # PolicyRecord.__post_init__ and PolicyStateMachine guards.
        )

        self._drafts[candidate_rule_id] = policy
        return policy

    def get_draft(self, candidate_rule_id: str) -> PolicyRecord | None:
        """Retrieve an existing Policy draft by candidate_rule_id."""
        return self._drafts.get(candidate_rule_id)

    def list_drafts(self) -> list[PolicyRecord]:
        """List all Policy drafts created by this bridge."""
        return list(self._drafts.values())


def _infer_ref_type(ref: str) -> str:
    """Infer evidence ref_type from a reference string prefix."""
    if ref.startswith("candidate_rule:"):
        return "candidate_rule"
    if ref.startswith("lesson:"):
        return "lesson"
    if ref.startswith("review:"):
        return "review"
    if ref.startswith("recommendation:"):
        return "recommendation"
    return "source_ref"
