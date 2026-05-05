"""Policy Shadow Runner — advisory evaluation of CandidateRules against red-team corpus.

Loads CandidateRule drafts, constructs synthetic PolicyRecords, runs
PolicyShadowEvaluator against a fixed red-team corpus, and logs results.

Always advisory — exit code 0 regardless of findings (escalation checker).
"""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domains.policies.models import (
    PolicyRecord,
    PolicyScope,
    PolicyState,
    PolicyRisk,
    PolicyEvidenceRef,
    EvidenceFreshness,
)
from domains.policies.shadow import (
    PolicyShadowCase,
    PolicyShadowResult,
    PolicyShadowEvaluator,
    ShadowVerdict,
)
from domains.policies.evidence_gate import (
    PolicyEvidenceGate,
    ReadinessLevel,
)

# ── Paths ────────────────────────────────────────────────────────────

CANDIDATE_RULES_FILE = ROOT / "docs" / "governance" / "candidate-rule-drafts.jsonl"
SHADOW_LOG_FILE = ROOT / "docs" / "governance" / "shadow-evaluation-log.jsonl"
FIXTURES_FILE = ROOT / "checkers" / "policy-shadow" / "fixtures" / "shadow_cases.json"

# ── Datatypes ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

# ── Loaders ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_candidate_rule_drafts() -> list[dict]:
    """Load CandidateRule drafts from JSONL."""
    if not CANDIDATE_RULES_FILE.exists():
        return []
    entries = []
    with open(CANDIDATE_RULES_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries

def load_shadow_cases() -> list[dict]:
    """Load red-team shadow cases from fixtures."""
    if not FIXTURES_FILE.exists():
        return []
    with open(FIXTURES_FILE) as f:
        return json.load(f)

# ── CandidateRule → PolicyRecord mapping ─────────────────────────────

def _draft_to_policy(draft: dict) -> PolicyRecord:
    """Map a CandidateRule draft JSON dict to a PolicyRecord.

    Constructs a synthetic PolicyRecord in DRAFT state. This is NOT the
    same as the CandidateRulePolicyBridge (which requires accepted_candidate
    status). Shadow evaluation happens BEFORE acceptance — this is the
    pre-bridge path for advisory-only evaluation.
    """
    candidate_rule_id = draft.get("candidate_rule_id", "")
    summary = draft.get("summary", "")
    tags = draft.get("tags", [])
    source_refs = draft.get("source_refs", [])

    # Infer scope from tags
    scope = PolicyScope.VERIFICATION  # default
    if "document-registry" in tags or "freshness" in tags:
        scope = PolicyScope.VERIFICATION
    elif "receipt" in tags or "overclaim" in tags:
        scope = PolicyScope.CORE
    elif "ci" in tags or "security" in tags:
        scope = PolicyScope.SECURITY
    elif "pack" in tags:
        scope = PolicyScope.PACK

    # Infer risk from severity
    severity = draft.get("severity", "medium")
    risk_map = {"low": PolicyRisk.LOW, "medium": PolicyRisk.MEDIUM, "high": PolicyRisk.HIGH}
    risk = risk_map.get(severity, PolicyRisk.MEDIUM)

    # Build evidence refs from source_refs
    evidence_refs: list[PolicyEvidenceRef] = []
    for ref in source_refs:
        ref_type = _infer_ref_type(ref)
        evidence_refs.append(
            PolicyEvidenceRef(
                ref_type=ref_type,
                ref_id=ref,
                freshness=EvidenceFreshness.CURRENT,
            )
        )

    # Always add the candidate rule itself
    evidence_refs.append(
        PolicyEvidenceRef(
            ref_type="candidate_rule",
            ref_id=f"candidate_rule:{candidate_rule_id}",
            freshness=EvidenceFreshness.CURRENT,
        )
    )

    return PolicyRecord(
        policy_id=candidate_rule_id,
        title=summary[:200],
        scope=scope,
        state=PolicyState.DRAFT,
        risk=risk,
        evidence_refs=tuple(evidence_refs),
    )

def _infer_ref_type(ref: str) -> str:
    """Infer evidence ref_type from reference prefix."""
    if ref.startswith("candidate_rule:"):
        return "candidate_rule"
    if ref.startswith("lesson:"):
        return "lesson"
    if ref.startswith("review:"):
        return "review"
    if ref.startswith("recommendation:"):
        return "recommendation"
    if ref.startswith("checker:"):
        return "ci_artifact"
    if ref.startswith("phase:"):
        return "source_ref"
    return "source_ref"

def _case_from_dict(data: dict) -> PolicyShadowCase:
    """Construct PolicyShadowCase from JSON dict."""
    freshness_str = data.get("evidence_freshness", "current")
    freshness_map = {
        "current": EvidenceFreshness.CURRENT,
        "stale": EvidenceFreshness.STALE,
        "regenerated": EvidenceFreshness.REGENERATED,
    }
    evidence_freshness = freshness_map.get(freshness_str, EvidenceFreshness.CURRENT)

    policy_scope = None
    if data.get("policy_scope"):
        scope_map = {
            "core": PolicyScope.CORE,
            "pack": PolicyScope.PACK,
            "adapter": PolicyScope.ADAPTER,
            "verification": PolicyScope.VERIFICATION,
            "security": PolicyScope.SECURITY,
        }
        policy_scope = scope_map.get(data["policy_scope"])

    expected_verdict = None
    if data.get("expected_verdict"):
        verdict_map = {
            "would_execute": ShadowVerdict.WOULD_EXECUTE,
            "would_escalate": ShadowVerdict.WOULD_ESCALATE,
            "would_reject": ShadowVerdict.WOULD_REJECT,
            "would_hold": ShadowVerdict.WOULD_HOLD,
            "would_recommend_merge": ShadowVerdict.WOULD_RECOMMEND_MERGE,
            "no_match": ShadowVerdict.NO_MATCH,
        }
        expected_verdict = verdict_map.get(data["expected_verdict"])

    return PolicyShadowCase(
        case_id=data["case_id"],
        description=data.get("description", ""),
        actor_type=data.get("actor_type", "unknown"),
        changed_files=tuple(data.get("changed_files", [])),
        has_ci_failure=data.get("has_ci_failure", False),
        has_evidence_artifact=data.get("has_evidence_artifact", True),
        evidence_freshness=evidence_freshness,
        has_test_plan=data.get("has_test_plan", True),
        is_react_update=data.get("is_react_update", False),
        policy_scope=policy_scope,
        expected_verdict=expected_verdict,
    )

# ── Core logic ───────────────────────────────────────────────────────

def run_shadow_evaluation() -> tuple[list[dict], dict]:
    """Run all CandidateRule drafts against the red-team shadow corpus.

    Returns (log_entries, stats).
    """
    drafts = load_candidate_rule_drafts()
    cases_raw = load_shadow_cases()

    if not drafts:
        return [], {
            "candidate_rules": 0,
            "shadow_cases": len(cases_raw),
            "total_evaluations": 0,
            "correct_verdicts": 0,
            "wrong_verdicts": 0,
            "no_match": 0,
            "readiness_checks": {"ready_for_activation": 0, "ready_for_shadow": 0,
                                  "ready_for_review": 0, "not_ready": 0},
        }

    evaluator = PolicyShadowEvaluator()
    evidence_gate = PolicyEvidenceGate()
    cases = [_case_from_dict(c) for c in cases_raw]
    log_entries: list[dict] = []

    stats = {
        "candidate_rules": len(drafts),
        "shadow_cases": len(cases),
        "total_evaluations": 0,
        "correct_verdicts": 0,
        "wrong_verdicts": 0,
        "no_match": 0,
        "readiness_checks": {"ready_for_activation": 0, "ready_for_shadow": 0,
                              "ready_for_review": 0, "not_ready": 0},
    }

    for draft in drafts:
        candidate_rule_id = draft.get("candidate_rule_id", "unknown")
        try:
            policy = _draft_to_policy(draft)
        except Exception as e:
            log_entries.append({
                "candidate_rule_id": candidate_rule_id,
                "run_at": _now_iso(),
                "error": f"PolicyRecord construction failed: {e}",
                "results": [],
            })
            continue

        # Run evaluation for all cases against this policy
        try:
            results = evaluator.evaluate_batch(policy, cases)
        except Exception as e:
            log_entries.append({
                "candidate_rule_id": candidate_rule_id,
                "run_at": _now_iso(),
                "error": f"Shadow evaluation failed: {e}",
                "results": [],
            })
            continue

        stats["total_evaluations"] += len(results)

        result_entries = []
        for ri, result in enumerate(results):
            case = cases[ri]
            entry = {
                "case_id": result.case_id,
                "verdict": result.verdict.value,
                "confidence": round(result.confidence, 3),
                "reasons": list(result.reasons),
                "false_positive_risk": result.false_positive_risk,
                "false_negative_risk": result.false_negative_risk,
            }

            # Compare against expected verdict
            if result.verdict == ShadowVerdict.NO_MATCH:
                stats["no_match"] += 1
            elif case.expected_verdict is not None:
                if result.verdict == case.expected_verdict:
                    stats["correct_verdicts"] += 1
                    entry["matches_expected"] = True
                else:
                    stats["wrong_verdicts"] += 1
                    entry["matches_expected"] = False
                    entry["expected_verdict"] = case.expected_verdict.value

            result_entries.append(entry)

        # Evidence gate check
        gate_result = evidence_gate.assess(policy)
        readiness_key_map = {
            ReadinessLevel.NOT_READY: "not_ready",
            ReadinessLevel.READY_FOR_REVIEW: "ready_for_review",
            ReadinessLevel.READY_FOR_SHADOW: "ready_for_shadow",
            ReadinessLevel.READY_FOR_HUMAN_ACTIVATION_REVIEW: "ready_for_activation",
        }
        readiness_label = readiness_key_map.get(gate_result.level, "not_ready")
        stats["readiness_checks"][readiness_label] += 1

        log_entry = {
            "candidate_rule_id": candidate_rule_id,
            "run_at": _now_iso(),
            "status": draft.get("status", "draft"),
            "review_status": draft.get("review_status", "pending_review"),
            "evidence_count": draft.get("evidence_count", 0),
            "results": result_entries,
            "readiness": {
                "level": gate_result.level.value,
                "reasons": list(gate_result.reasons),
                "warnings": list(gate_result.warnings),
            },
        }
        log_entries.append(log_entry)

    return log_entries, stats

# ── Checker entry point ──────────────────────────────────────────────

def run() -> CheckerResult:
    log_entries, stats = run_shadow_evaluation()

    findings: list[str] = []

    if stats["candidate_rules"] == 0:
        findings.append("No CandidateRule drafts found — nothing to shadow-test")
        return CheckerResult("pass", 0, findings, dict(stats))

    findings.append(
        f"Shadow-evaluated {stats['candidate_rules']} CandidateRule(s) "
        f"against {stats['shadow_cases']} red-team cases "
        f"({stats['total_evaluations']} total evaluations)"
    )

    if stats["correct_verdicts"] > 0:
        findings.append(
            f"  ✅ {stats['correct_verdicts']} correct verdicts "
            f"(matched expected)"
        )
    if stats["wrong_verdicts"] > 0:
        findings.append(
            f"  ⚠️  {stats['wrong_verdicts']} unexpected verdicts "
            f"(may need rule refinement)"
        )
    if stats["no_match"] > 0:
        findings.append(
            f"  ℹ️  {stats['no_match']} no_match (scope didn't apply)"
        )

    # Readiness report
    rc = stats["readiness_checks"]
    findings.append(f"  Readiness: {rc['ready_for_activation']} activation-ready, "
                     f"{rc['ready_for_shadow']} shadow-ready, "
                     f"{rc['ready_for_review']} review-only, "
                     f"{rc['not_ready']} not_ready")

    # Write log entries
    if log_entries:
        mode = "a" if SHADOW_LOG_FILE.exists() else "w"
        with open(SHADOW_LOG_FILE, mode) as f:
            for entry in log_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        findings.append(f"  Logged to {SHADOW_LOG_FILE}")

    # Always pass — shadow is advisory
    return CheckerResult("pass", 0, findings, dict(stats))


if __name__ == "__main__":
    r = run()
    for f in r.findings:
        print(f"  {f}")
    print(f"\nStats: {json.dumps(r.stats, indent=2)}")
    sys.exit(r.exit_code)
