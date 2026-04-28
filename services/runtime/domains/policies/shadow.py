"""Policy Shadow Evaluation — advisory-only testing of candidate policies.

Pure domain logic. No ORM, no DB, no RiskEngine, no side effects.
Does NOT activate, enforce, or modify policies.

Shadow mode answers: "If this policy existed, what would it have
recommended on these cases?"

Output is always advisory. READY_FOR_HUMAN_ACTIVATION_REVIEW means "ready for human
activation review", not automatic activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domains.policies.models import (
    PolicyRecord,
    EvidenceFreshness,
    PolicyScope,
)
from domains.policies.evidence_gate import (
    PolicyEvidenceGate,
    ReadinessLevel,
)


class ShadowVerdict(str, Enum):
    """Advisory verdict from a shadow evaluation — what this policy
    would have recommended if it were active."""

    WOULD_EXECUTE = "would_execute"
    WOULD_ESCALATE = "would_escalate"
    WOULD_REJECT = "would_reject"
    WOULD_HOLD = "would_hold"
    WOULD_RECOMMEND_MERGE = "would_recommend_merge"
    NO_MATCH = "no_match"  # policy scope/context doesn't apply to this case


@dataclass(frozen=True)
class PolicyShadowCase:
    """A test scenario for shadow evaluation.

    Represents a hypothetical governance situation that a policy
    might need to handle. Used for red-team testing and pre-activation
    validation.
    """

    case_id: str
    description: str
    # Case inputs
    actor_type: str  # "dependabot", "human", "ai_agent", "workflow", "unknown"
    changed_files: tuple[str, ...] = ()
    has_ci_failure: bool = False
    has_evidence_artifact: bool = True
    evidence_freshness: EvidenceFreshness = EvidenceFreshness.CURRENT
    has_test_plan: bool = True  # for human PRs
    is_react_update: bool = False  # special case for runtime dependency
    # Policy context
    policy_scope: PolicyScope | None = None  # if None, matches all
    # Expected outcome (for red-team validation)
    expected_verdict: ShadowVerdict | None = None  # None = any outcome acceptable


@dataclass(frozen=True)
class PolicyShadowResult:
    """The result of evaluating a PolicyShadowCase against a PolicyRecord.

    Always advisory. Never mutates state or activates policy.
    """

    case_id: str
    policy_id: str
    verdict: ShadowVerdict
    reasons: tuple[str, ...] = ()
    matched_evidence_refs: tuple[str, ...] = ()
    confidence: float = 0.0  # 0.0 = no confidence, 1.0 = high confidence
    false_positive_risk: str = "unknown"  # "low", "medium", "high"
    false_negative_risk: str = "unknown"
    is_advisory: bool = True  # always True — shadow mode never enforces

    @property
    def would_block(self) -> bool:
        """Would this policy have blocked the action?"""
        return self.verdict in (ShadowVerdict.WOULD_REJECT,)

    @property
    def would_require_review(self) -> bool:
        """Would this policy have required human review?"""
        return self.verdict in (ShadowVerdict.WOULD_ESCALATE, ShadowVerdict.WOULD_HOLD)


class PolicyShadowEvaluator:
    """Evaluates a PolicyRecord against shadow cases to produce advisory results.

    Pure domain logic. Does NOT:
      - Call RiskEngine
      - Modify PolicyRecord state
      - Activate or enforce policies
      - Connect to ORM, DB, or CI

    Usage:
        evaluator = PolicyShadowEvaluator()
        result = evaluator.evaluate(policy, case)
        print(f"Shadow verdict: {result.verdict}")
    """

    def __init__(self):
        self._evidence_gate = PolicyEvidenceGate()

    def evaluate(self, policy: PolicyRecord, case: PolicyShadowCase) -> PolicyShadowResult:
        """Evaluate a single shadow case against a policy.

        Returns an advisory PolicyShadowResult. Never mutates the policy.
        """
        reasons: list[str] = []
        matched_refs: list[str] = []

        # ── Scope match ───────────────────────────────────────────
        if case.policy_scope is not None and case.policy_scope != policy.scope:
            return PolicyShadowResult(
                case_id=case.case_id,
                policy_id=policy.policy_id,
                verdict=ShadowVerdict.NO_MATCH,
                reasons=(
                    f"Policy scope '{policy.scope.value}' does not match case scope '{case.policy_scope.value}'.",
                ),
                confidence=1.0,
            )

        # ── Actor routing ────────────────────────────────────────
        if case.actor_type == "dependabot":
            return self._evaluate_dependabot_case(policy, case, reasons, matched_refs)
        elif case.actor_type == "human":
            return self._evaluate_human_case(policy, case, reasons, matched_refs)
        elif case.actor_type in ("ai_agent", "workflow"):
            return self._evaluate_internal_case(policy, case, reasons, matched_refs)
        elif case.actor_type == "unknown":
            return self._escalate_unknown(policy, case, reasons, matched_refs)

        return PolicyShadowResult(
            case_id=case.case_id,
            policy_id=policy.policy_id,
            verdict=ShadowVerdict.WOULD_ESCALATE,
            reasons=(f"Unhandled actor_type '{case.actor_type}'.",),
            confidence=0.3,
        )

    # ── Per-actor evaluation logic ───────────────────────────────

    def _evaluate_dependabot_case(
        self,
        policy: PolicyRecord,
        case: PolicyShadowCase,
        reasons: list[str],
        matched_refs: list[str],
    ) -> PolicyShadowResult:
        """Evaluate a Dependabot bot PR case."""
        # Evidence freshness gate
        if case.evidence_freshness == EvidenceFreshness.STALE:
            return PolicyShadowResult(
                case_id=case.case_id,
                policy_id=policy.policy_id,
                verdict=ShadowVerdict.WOULD_HOLD,
                reasons=("Stale governance evidence — cannot recommend action without fresh CI.",),
                matched_evidence_refs=(),
                confidence=0.8,
                false_positive_risk="low",
            )

        # React/runtime update with CI failure
        if case.is_react_update and case.has_ci_failure:
            return PolicyShadowResult(
                case_id=case.case_id,
                policy_id=policy.policy_id,
                verdict=ShadowVerdict.WOULD_HOLD,
                reasons=(
                    "Runtime dependency update with CI failure.",
                    "Frontend build/components test failure — requires manual review.",
                ),
                confidence=0.9,
                false_negative_risk="low",
                false_positive_risk="low",
            )

        # Clean dependency-only PR with fresh CI + evidence
        if not case.has_ci_failure and case.has_evidence_artifact:
            gate_result = self._evidence_gate.assess(policy)
            if gate_result.level == ReadinessLevel.NOT_READY:
                return PolicyShadowResult(
                    case_id=case.case_id,
                    policy_id=policy.policy_id,
                    verdict=ShadowVerdict.WOULD_ESCALATE,
                    reasons=("Policy evidence not ready for shadow recommendation.",) + gate_result.reasons,
                    confidence=0.5,
                )
            if gate_result.level != ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW:
                return PolicyShadowResult(
                    case_id=case.case_id,
                    policy_id=policy.policy_id,
                    verdict=ShadowVerdict.WOULD_ESCALATE,
                    reasons=(
                        f"Policy evidence at level '{gate_result.level.value}' — "
                        "not sufficient for merge recommendation. "
                        "Requires READY_FOR_HUMAN_ACTIVATION_REVIEW evidence.",
                    )
                    + gate_result.warnings,
                    confidence=0.5,
                )

            for ref in policy.evidence_refs:
                if ref.freshness in (EvidenceFreshness.CURRENT, EvidenceFreshness.REGENERATED):
                    matched_refs.append(ref.ref_id)

            return PolicyShadowResult(
                case_id=case.case_id,
                policy_id=policy.policy_id,
                verdict=ShadowVerdict.WOULD_RECOMMEND_MERGE,
                reasons=(
                    "Dependabot dependency-only PR with fresh CI and evidence artifact.",
                    "All substantive CI checks passed.",
                ),
                matched_evidence_refs=tuple(matched_refs),
                confidence=0.85,
                false_positive_risk="low",
                false_negative_risk="low",
            )

        # CI failure on non-react update
        if case.has_ci_failure:
            return PolicyShadowResult(
                case_id=case.case_id,
                policy_id=policy.policy_id,
                verdict=ShadowVerdict.WOULD_HOLD,
                reasons=("CI failure detected on dependency update.",),
                confidence=0.7,
            )

        return PolicyShadowResult(
            case_id=case.case_id,
            policy_id=policy.policy_id,
            verdict=ShadowVerdict.WOULD_ESCALATE,
            reasons=("Insufficient classification data for Dependabot case.",),
            confidence=0.4,
        )

    def _evaluate_human_case(
        self,
        policy: PolicyRecord,
        case: PolicyShadowCase,
        reasons: list[str],
        matched_refs: list[str],
    ) -> PolicyShadowResult:
        """Evaluate a human PR case."""
        # Human PR with "deps:" title but no bot metadata
        # This is about actor identity, not title patterns
        if not case.has_test_plan:
            return PolicyShadowResult(
                case_id=case.case_id,
                policy_id=policy.policy_id,
                verdict=ShadowVerdict.WOULD_ESCALATE,
                reasons=(
                    "Human PR without test plan — requires review.",
                    "Title 'deps:' does not confer bot treatment (doctrine §3.3).",
                ),
                confidence=0.9,
            )

        return PolicyShadowResult(
            case_id=case.case_id,
            policy_id=policy.policy_id,
            verdict=ShadowVerdict.WOULD_EXECUTE,
            reasons=("Human PR with test plan — governance pass.",),
            confidence=0.7,
        )

    def _evaluate_internal_case(
        self,
        policy: PolicyRecord,
        case: PolicyShadowCase,
        reasons: list[str],
        matched_refs: list[str],
    ) -> PolicyShadowResult:
        """Evaluate an AI agent or workflow case."""
        return PolicyShadowResult(
            case_id=case.case_id,
            policy_id=policy.policy_id,
            verdict=ShadowVerdict.WOULD_ESCALATE,
            reasons=(f"Internal actor '{case.actor_type}' — requires human review per doctrine §4.3.",),
            confidence=0.6,
        )

    def _escalate_unknown(
        self,
        policy: PolicyRecord,
        case: PolicyShadowCase,
        reasons: list[str],
        matched_refs: list[str],
    ) -> PolicyShadowResult:
        """Escalate unknown actor types — conservative default."""
        return PolicyShadowResult(
            case_id=case.case_id,
            policy_id=policy.policy_id,
            verdict=ShadowVerdict.WOULD_ESCALATE,
            reasons=(f"Unknown actor_type '{case.actor_type}' — conservative escalation.",),
            confidence=0.3,
            false_negative_risk="medium",
        )

    def evaluate_batch(
        self,
        policy: PolicyRecord,
        cases: list[PolicyShadowCase],
    ) -> list[PolicyShadowResult]:
        """Evaluate multiple shadow cases against a policy."""
        return [self.evaluate(policy, case) for case in cases]

    def activation_readiness_check(self, policy: PolicyRecord) -> bool:
        """Check if a policy is ready for human activation review.

        READY_FOR_HUMAN_ACTIVATION_REVIEW from the evidence gate means "ready for
        human review before activation" — it does NOT mean the policy
        is automatically activated.

        Returns True if the evidence gate says READY_FOR_HUMAN_ACTIVATION_REVIEW.
        """
        result = self._evidence_gate.assess(policy)
        return result.level == ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW
